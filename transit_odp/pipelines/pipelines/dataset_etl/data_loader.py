from typing import List

import numpy as np
import pandas as pd
from celery.utils.log import get_task_logger
from django.db.models import Q

from transit_odp.organisation.models import DatasetRevision
from transit_odp.pipelines import exceptions
from transit_odp.pipelines.pipelines.dataset_etl.utils.extract_meta_result import (
    ETLReport,
)
from transit_odp.pipelines.pipelines.dataset_etl.utils.models import TransformedData
from transit_odp.pipelines.pipelines.dataset_etl.utils.timestamping import (
    empty_timestamp,
    starting_timestamp,
)

from transit_odp.transmodel.models import (
    Service,
    ServiceLink,
    ServicePattern,
    ServicePatternStop,
)

from .utils.dataframes import (
    create_service_link_df_from_queryset,
    df_to_service_links,
    df_to_service_patterns,
    df_to_services,
    get_max_date_or_none,
    get_min_date_or_none,
)

logger = get_task_logger(__name__)


class DataLoader:
    def __init__(self, feed_parser):
        self.feed_parser = feed_parser

    def load(self, transformed: TransformedData) -> ETLReport:
        services = transformed.services
        service_patterns = transformed.service_patterns

        service_pattern_stops = transformed.service_pattern_stops
        services = self.load_services(services)

        self.load_service_patterns(services, service_patterns, service_pattern_stops)

        load_results = self.produce_report(transformed)

        if load_results.line_count == 0:
            raise exceptions.PipelineException(
                message="No results were loaded",
            )

        return load_results

    def produce_report(self, transformed: TransformedData) -> ETLReport:
        loaded_services = list(self.feed_parser.service_cache.values())

        report = ETLReport()

        report.import_datetime = self.feed_parser.now

        # Expiration dates
        report.first_expiring_service = empty_timestamp()
        report.last_expiring_service = starting_timestamp()
        report.first_service_start = starting_timestamp()

        expiration_dates = []
        start_dates = []
        for service in loaded_services:
            expiration_dates.append(service.end_date)
            start_dates.append(service.start_date)

        report.first_expiring_service = get_min_date_or_none(expiration_dates)
        report.last_expiring_service = get_max_date_or_none(expiration_dates)
        report.first_service_start = get_min_date_or_none(start_dates)

        report.schema_version = transformed.schema_version

        report.creation_datetime = transformed.creation_datetime
        report.modification_datetime = transformed.modification_datetime
        report.line_count = transformed.line_count
        report.stop_count = transformed.stop_count
        report.name = self.create_feed_name(
            transformed.most_common_localities,
            report.first_service_start,
            report.line_count,
            transformed.line_names,
        )

        logger.info("[DataLoader] Finished produce_report")

        return report

    def load_services(self, services: pd.DataFrame):
        """Load Services into DB"""
        # reset index so we can match up bulk created objects.
        # The bulk created objects should have the same order
        # as the services dataframe
        logger.info("[DataLoader] Starting load_services")

        services.reset_index(inplace=True)
        created = Service.objects.bulk_create(
            df_to_services(self.feed_parser.revision, services)
        )

        services["id"] = pd.Series((obj.id for obj in created))

        # set index back again
        services.set_index(["file_id", "service_code"], inplace=True)

        # Update cache with created services
        self.feed_parser.service_cache.update(
            {service.id: service for service in created}
        )

        logger.info("[DataLoader] Finished load_services")
        return services

    def load_service_links(self, service_links: pd.DataFrame):
        """Load ServiceLinks into DB"""
        logger.info("[DataLoader] Starting load_service_links")

        service_link_cache = self.feed_parser.service_link_cache

        service_links_refs = set(service_links.index)
        cached_service_links = set(service_link_cache.index)

        # Fetch ServiceLinks not in cache
        fetch_links = service_links_refs - cached_service_links
        if fetch_links != set():
            # Create Django query expression
            # Note we're querying on the denormalised atco_code columns,
            # rather than the DB stop ids,
            # since ServiceLinks can be created for non-existent StopPoints. This
            # allows us to get the id of an 'incomplete' ServiceLink if it has
            # already been created
            q = np.bitwise_or.reduce(
                [
                    Q(from_stop_atco=link[0], to_stop_atco=link[1])
                    for link in list(fetch_links)
                ]
            )

            qs = ServiceLink.objects.filter(q)
            fetched = create_service_link_df_from_queryset(qs)

            # Create missing service links - those which were not returned from database
            missing_links = fetch_links - set(fetched.index)
            # Select missing service_links from input data
            missing = service_links.loc[sorted(missing_links)]

            # Bulk create service links
            created = create_service_link_df_from_queryset(
                ServiceLink.objects.bulk_create(df_to_service_links(missing))
            )

            # Update cache with fetched and newly created
            service_link_cache = pd.concat(
                [service_link_cache, fetched, created], sort=True
            )

        # Return updated services links referenced in doc rather than entire cache
        service_links = service_link_cache.loc[sorted(service_links_refs)]

        logger.info("[DataLoader] Finished load_service_links")
        return service_links

    def load_service_patterns(self, services, service_patterns, service_pattern_stops):
        logger.info("[DataLoader] Starting load_service_patterns")

        created = ServicePattern.objects.bulk_create(
            df_to_service_patterns(self.feed_parser.revision, service_patterns)
        )

        created = pd.DataFrame(
            (
                {
                    "service_pattern_id": obj.service_pattern_id,
                    "id": obj.id,
                    "instance": obj,
                }
                for obj in created
            )
        ).set_index("service_pattern_id")

        service_patterns = service_patterns.join(created)

        # ADD ServicePattern Associations

        # Add ServicePattern m2m ServiceLink
        # TODO - associate ServiceLinks - need explicit through table as ServiceLink
        # can appear more than once on
        #  the ServicePattern
        # self.add_service_pattern_to_service_links(service_pattern_to_service_links)

        # Create ServicePatternStops and add to ServicePattern
        self.add_service_pattern_to_service_pattern_stops(
            service_pattern_stops, service_patterns
        )

        # Add ServiceLinks, ServicePatternStops, Localities, AdminAreas to
        # ServicePattern
        self.add_service_pattern_to_localities_and_admin_area(service_patterns)

        # Add ServicePatterns to Service
        self.add_service_associations(services, service_patterns)

        logger.info("[DataLoader] Finished load_service_patterns")
        return service_patterns

    @classmethod
    def add_service_associations(cls, services, service_patterns):
        through_model = Service.service_patterns.through

        def _inner(df: pd.DataFrame):
            for record in df[["id_service", "id_service_pattern"]].to_dict("records"):
                yield through_model(
                    service_id=record["id_service"],
                    servicepattern_id=record["id_service_pattern"],
                )

        service_to_service_patterns = services[["id"]].merge(
            service_patterns.reset_index()[["file_id", "service_code", "id"]],
            left_index=True,
            right_on=["file_id", "service_code"],
            suffixes=["_service", "_service_pattern"],
        )

        return through_model.objects.bulk_create(_inner(service_to_service_patterns))

    @classmethod
    def add_service_pattern_to_localities_and_admin_area(cls, df: pd.DataFrame):
        # Get implicit through-table for m2m
        locality_through_model = ServicePattern.localities.through

        def _inner_localities():
            the_localities = set()
            for record in df.to_dict("records"):
                for locality in record["localities"]:
                    if locality and locality != "None":
                        the_localities.add(locality)

                for locality_id in list(the_localities):
                    if locality_id:
                        yield locality_through_model(
                            servicepattern_id=record["id"], locality_id=locality_id
                        )

        _localities = list(_inner_localities())
        localities = None
        if len(_localities) > 0:
            localities = locality_through_model.objects.bulk_create(_localities)

        admin_area_through_model = ServicePattern.admin_areas.through

        def _inner_admin_areas():
            the_admin_areas = set()
            for record in df.to_dict("records"):
                for admin_area in record["admin_area_codes"]:
                    if admin_area:
                        the_admin_areas.add(admin_area)

                for admin_area_id in list(the_admin_areas):
                    if admin_area_id:
                        yield admin_area_through_model(
                            servicepattern_id=record["id"],
                            adminarea_id=admin_area_id,
                        )

        _admin_areas = list(_inner_admin_areas())
        admin_areas = None
        if len(_admin_areas) > 0:
            admin_areas = admin_area_through_model.objects.bulk_create(_admin_areas)
        return localities, admin_areas

    @classmethod
    def add_service_pattern_to_service_pattern_stops(
        cls, df: pd.DataFrame, service_patterns: pd.DataFrame
    ):
        def _inner():
            for record in df.to_dict("records"):
                service_pattern_id = service_patterns.xs(
                    record["service_pattern_id"], level="service_pattern_id"
                ).iloc[0]["id"]
                yield ServicePatternStop(
                    service_pattern_id=service_pattern_id,
                    sequence_number=record["order"],
                    naptan_stop_id=record["naptan_id"],
                    atco_code=record["stop_atco"],
                )

        stops = list(_inner())
        if stops:
            return ServicePatternStop.objects.bulk_create(stops)
        else:
            return None

    def create_feed_name(
        self, most_common_district, first_service_start, no_of_lines, lines
    ):
        first_service_start = first_service_start.strftime("%Y%m%d")

        # TODO - make functional - easier to test
        revision = self.feed_parser.revision
        organisation = revision.dataset.organisation.name

        if no_of_lines == 1:
            # Case 1, there is one line
            area = most_common_district[0]
            # line_string = lines[0]
            feed_name = f"{organisation}_{area}_{lines}_{first_service_start}"

        elif no_of_lines > 1:
            # Case 2, there are more than one lines
            area = "_".join(most_common_district[:2])
            feed_name = f"{organisation}_{area}_{first_service_start}"
        else:
            # not sure what could have happened here
            # just return the original name
            return revision.name

        # double check there are no clashes
        match = list(
            DatasetRevision.objects.filter(name__startswith=feed_name)
            .values("name")
            .order_by("name")
        )
        if not match:
            # nope we are good to go
            return feed_name

        if len(match) == 1 and match[0]["name"] == feed_name:
            # the first duplicate
            return f"{feed_name}_1"

        # We know the first element is the feed name without underscores
        # if it exists chop it out
        if match[0]["name"] == feed_name:
            match.pop(0)

        highest_match = max(match, key=lambda n: int(n["name"].split("_")[-1]))
        highest_match = highest_match["name"]

        # we just need to append increment end by 1
        clash_count = int(highest_match.split("_")[-1])
        clash_count += 1
        return f"{feed_name}_{clash_count}"

    # TODO - this is throwing a duplicate key error as there can be duplicate
    # service links on the service patterns
    # ServiceLinks are not particularly useful at the moment, so removing this
    # for now. Will need to create an
    # intermediate ServicePatternServiceLink model, which has a sequence number on
    # it to allow multiple membership
    def add_service_pattern_to_service_links(
        self, df: pd.DataFrame
    ) -> List[ServicePattern.service_links.through]:
        """Bulk create m2m association of ServicePattern to ServiceLink"""
        ThroughModel = ServicePattern.service_links.through
        created = ThroughModel.objects.bulk_create(
            self.df_to_service_pattern_service(df)
        )
        return created
