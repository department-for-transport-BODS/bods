import numpy as np
import pandas as pd
from celery.utils.log import get_task_logger
from django.db.models import Q

from transit_odp.common.loggers import get_dataset_adapter_from_revision
from transit_odp.pipelines import exceptions
from transit_odp.pipelines.pipelines.dataset_etl.utils.dataframes import (
    create_service_link_df_from_queryset,
    df_to_service_links,
    df_to_service_patterns,
    df_to_services,
    df_to_booking_arrangements,
    get_max_date_or_none,
    get_min_date_or_none,
)
from transit_odp.pipelines.pipelines.dataset_etl.utils.extract_meta_result import (
    ETLReport,
)
from transit_odp.pipelines.pipelines.dataset_etl.utils.loaders import (
    add_service_associations,
    add_service_pattern_to_admin_area,
    add_service_pattern_to_localities,
    add_service_pattern_to_service_pattern_stops,
    create_feed_name,
)
from transit_odp.pipelines.pipelines.dataset_etl.utils.models import TransformedData
from transit_odp.pipelines.pipelines.dataset_etl.utils.timestamping import (
    empty_timestamp,
    starting_timestamp,
)
from transit_odp.transmodel.models import Service, ServiceLink, ServicePattern, BookingArrangements

BATCH_SIZE = 2000
logger = get_task_logger(__name__)


class TransXChangeDataLoader:
    def __init__(self, transformed: TransformedData, service_cache, service_link_cache):
        self.transformed = transformed
        self.service_cache = service_cache
        self.service_link_cache = service_link_cache

    def load(self, revision, start_time):
        adapter = get_dataset_adapter_from_revision(logger, revision)
        adapter.info("Loading TransXChange data set.")

        adapter.info("Loading services.")
        services = self.load_services(revision)
        adapter.info("Finished loading services.")

        adapter.info("Loading service patterns.")
        self.load_service_patterns(services, revision)
        adapter.info("Finished loading service patterns.")

        adapter.info("Loading booking arrangements.")
        self.load_booking_arrangements(revision)
        adapter.info("Finished loading booking arrangements.")

        adapter.info("Producing ETLReport.")
        report = self.produce_report(revision, start_time)
        adapter.info("Finished producing ETLReport.")

        if report.line_count == 0:
            raise exceptions.PipelineException(
                message="No results were loaded",
            )

        return report

    def produce_report(self, revision, start_time) -> ETLReport:
        loaded_services = list(self.service_cache.values())
        report = ETLReport()
        report.import_datetime = start_time

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

        report.schema_version = self.transformed.schema_version

        report.creation_datetime = self.transformed.creation_datetime
        report.modification_datetime = self.transformed.modification_datetime
        report.line_count = self.transformed.line_count
        report.stop_count = self.transformed.stop_count
        report.timing_point_count = self.transformed.timing_point_count

        report.name = create_feed_name(
            self.transformed.most_common_localities,
            report.first_service_start,
            report.line_count,
            self.transformed.line_names,
            revision,
        )

        return report

    def load_services(self, revision):
        """Load Services into DB"""
        # reset index so we can match up bulk created objects.
        # The bulk created objects should have the same order
        # as the services dataframe
        services = self.transformed.services
        services.reset_index(inplace=True)
        service_objs = list(df_to_services(revision, services))
        created = Service.objects.bulk_create(service_objs, batch_size=BATCH_SIZE)
        services["id"] = pd.Series((obj.id for obj in created))

        # set index back again
        services.set_index(["file_id", "service_code"], inplace=True)

        # Update cache with created services
        self.service_cache.update({service.id: service for service in created})

        return services

    def load_service_links(self, service_links: pd.DataFrame):
        """Load ServiceLinks into DB"""
        service_link_cache = self.service_link_cache
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

            service_link_objs = list(df_to_service_links(missing))
            created = create_service_link_df_from_queryset(
                ServiceLink.objects.bulk_create(
                    service_link_objs, batch_size=BATCH_SIZE
                )
            )

            # Update cache with fetched and newly created
            service_link_cache = pd.concat(
                [service_link_cache, fetched, created], sort=True
            )

        # Return updated services links referenced in doc rather than entire cache
        service_links = service_link_cache.loc[sorted(service_links_refs)]
        return service_links

    def load_service_patterns(self, services, revision):
        adapter = get_dataset_adapter_from_revision(logger, revision=revision)
        service_patterns = self.transformed.service_patterns
        service_pattern_stops = self.transformed.service_pattern_stops

        adapter.info("Bulk creating service patterns.")
        service_pattern_objs = df_to_service_patterns(revision, service_patterns)
        created = ServicePattern.objects.bulk_create(
            service_pattern_objs, batch_size=BATCH_SIZE
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
        )

        if not created.empty:
            created = created.set_index("service_pattern_id")

        service_patterns = service_patterns.join(created)

        # ADD ServicePattern Associations

        # Add ServicePattern m2m ServiceLink
        # TODO - associate ServiceLinks - need explicit through table as ServiceLink
        # can appear more than once on
        #  the ServicePattern
        # self.add_service_pattern_to_service_links(service_pattern_to_service_links)

        # Create ServicePatternStops and add to ServicePattern
        adapter.info("Creating service pattern stops.")
        add_service_pattern_to_service_pattern_stops(
            service_pattern_stops, service_patterns
        )

        # Add ServiceLinks, ServicePatternStops, Localities, AdminAreas to
        # ServicePattern
        adapter.info("Adding localities.")
        add_service_pattern_to_localities(service_patterns)

        adapter.info("Adding administrative areas.")
        add_service_pattern_to_admin_area(service_patterns)

        # Add ServicePatterns to Service
        adapter.info("Adding service associations.")
        if not service_patterns.empty:
            add_service_associations(services, service_patterns)

        adapter.info("Finished loading service patterns.")
        return service_patterns


    def load_booking_arrangements(self, revision):
        adapter = get_dataset_adapter_from_revision(logger, revision=revision)
        booking_arrangements = self.transformed.booking_arrangements
        booking_arrangements.reset_index(inplace=True)
        adapter.info("Bulk creating booking arrangements")
        booking_arrangements_objs = list(df_to_booking_arrangements(revision, booking_arrangements))

        created = BookingArrangements.objects.bulk_create(
            booking_arrangements_objs, batch_size=BATCH_SIZE
        )

        booking_arrangements["id"] = pd.Series((obj.id for obj in created))
        booking_arrangements.set_index(["id"], inplace=True)

        return booking_arrangements
