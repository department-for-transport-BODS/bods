import numpy as np
import pandas as pd
from celery.utils.log import get_task_logger
from django.db.models import Q

from transit_odp.common.loggers import get_dataset_adapter_from_revision
from transit_odp.pipelines import exceptions
from transit_odp.pipelines.pipelines.dataset_etl.utils.dataframes import (
    create_service_link_df_from_queryset,
    df_to_flexible_service_operation_period,
    df_to_non_operating_dates_exceptions,
    df_to_operating_dates_exceptions,
    df_to_service_links,
    df_to_service_patterns,
    df_to_serviced_organisation_working_days,
    df_to_services,
    df_to_booking_arrangements,
    df_to_vehicle_journeys,
    df_to_serviced_organisations,
    df_to_operating_profiles,
    df_to_serviced_org_vehicle_journey,
    get_max_date_or_none,
    get_min_date_or_none,
    df_to_tracks,
    merge_vj_tracks_df,
    df_to_journeys_tracks,
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
from transit_odp.timetables.utils import (
    filter_rows_by_journeys,
    get_filtered_rows_by_journeys,
    get_journey_mappings,
)
from transit_odp.transmodel.models import (
    FlexibleServiceOperationPeriod,
    NonOperatingDatesExceptions,
    OperatingDatesExceptions,
    Service,
    ServiceLink,
    ServicePattern,
    BookingArrangements,
    ServicedOrganisationWorkingDays,
    VehicleJourney,
    ServicedOrganisations,
    OperatingProfile,
    ServicedOrganisationVehicleJourney,
    Tracks,
    TracksVehicleJourney,
)

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
        service_patterns = self.load_service_patterns(services, revision)
        adapter.info("Finished loading service patterns.")

        adapter.info("Loading serviced organisations.")
        serviced_organisations = self.load_serviced_organisation()
        adapter.info("Finished serviced organisations.")

        adapter.info("Loading vehicle journeys.")
        vehicle_journeys = self.load_vehicle_journeys(service_patterns)
        adapter.info("Finished vehicle journeys.")
        tracks = self.transformed.journey_pattern_tracks
        tracks_map = self.transformed.route_map
        if not tracks.empty and not vehicle_journeys.empty:
            adapter.info("Loading tracks.")
            tracks = self.load_journey_tracks()
            adapter.info("Finished Tracks")

            adapter.info("Loading vehicle_journeys tracks")
            self.load_vj_tracks(tracks, vehicle_journeys, tracks_map)
            adapter.info("Finished vehicle journey tracks")

        adapter.info("Loading flexible operation periods.")
        self.load_flexible_service_operation_periods(vehicle_journeys)
        adapter.info("Finished flexible operation periods.")

        adapter.info("Loading operating profiles.")
        self.load_operating_profiles_and_related_tables(vehicle_journeys)
        adapter.info("Finished loading operating profiles.")

        adapter.info("Loading serviced organisations vehicle journeys.")
        serviced_orgs_vjs = self.load_serviced_organisation_vehicle_journey(
            vehicle_journeys, serviced_organisations
        )
        adapter.info("Finished serviced organisations vehicle journeys.")

        adapter.info("Loading serviced organisations working dates.")
        self.load_serviced_organisation_working_days(
            serviced_organisations, serviced_orgs_vjs
        )
        adapter.info("Finished serviced organisationsworking dates.")

        adapter.info("Loading service pattern stops.")
        self.load_service_patterns_stops(service_patterns, vehicle_journeys, revision)
        adapter.info("Finished service pattern stops.")

        adapter.info("Loading booking arrangements.")
        self.load_booking_arrangements(services, revision)
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

    def load_vehicle_journeys(self, service_patterns):
        vehicle_journeys = self.transformed.vehicle_journeys
        if not vehicle_journeys.empty:
            if not service_patterns.empty:
                service_patterns = (
                    service_patterns.reset_index()[
                        ["service_pattern_id", "id", "file_id", "line_name"]
                    ]
                    .drop_duplicates()
                    .rename(columns={"id": "id_service"})
                )
                # # add line_name to the VJs
                # vehicle_journeys["line_name"] = (
                #     vehicle_journeys["line_ref"].str.split(":").str[-1]
                # )

                # Add line_name to the vehicle_journeys DataFrame if line_ref is not None 
                vehicle_journeys["line_name"] = vehicle_journeys["line_ref"].apply( lambda x: x.str.split(":")[-1] if pd.notnull(x) else None)


                vehicle_journeys = (
                    vehicle_journeys.reset_index()
                    .merge(
                        service_patterns,
                        on=["file_id", "service_pattern_id", "line_name"],
                        how="left",
                    )
                    .reset_index()
                )
                vehicle_journeys["id_service"].fillna("", inplace=True)

            vehicle_journeys_objs = list(df_to_vehicle_journeys(vehicle_journeys))
            created = VehicleJourney.objects.bulk_create(
                vehicle_journeys_objs, batch_size=BATCH_SIZE
            )
            vehicle_journeys["id"] = pd.Series(
                (obj.id for obj in created), index=vehicle_journeys.index
            )
        if "line_name" in vehicle_journeys.columns:
            vjs = vehicle_journeys.drop("line_name")
            return vjs
        else: 
            return vehicle_journeys

    def load_journey_tracks(self):
        """
        Load journey tracks and update the Tracks model.

        This method processes the transformed journey pattern tracks and updates the Tracks model
        using the update_or_create method to ensure records are created or updated based on the
        unique combination of 'from_atco_code' and 'to_atco_code'.

        Steps:
        1. Extract the journey pattern tracks from the transformed data.
        2. Convert the DataFrame of tracks into a list of dictionaries.
        3. Iterate through each track dictionary and use update_or_create to update existing records or create new ones in the Tracks model.
        4. Collect the created or updated track objects.
        5. Update the 'id' column in the original DataFrame with the IDs of the created or updated track objects.

        Returns:
            pd.DataFrame: The original DataFrame with the 'id' column updated to reflect the IDs of the created or updated track records.
        """
        create_or_update = []
        tracks = self.transformed.journey_pattern_tracks
        tracks_dicts = list(df_to_tracks(tracks))

        for track_dict in tracks_dicts:
            obj, created = Tracks.objects.update_or_create(
                from_atco_code=track_dict["from_atco_code"],
                to_atco_code=track_dict["to_atco_code"],
                defaults=track_dict,
            )
            create_or_update.append(obj)

        tracks["id"] = pd.Series(
            (obj.id for obj in create_or_update), index=tracks.index
        )
        return tracks

    def load_vj_tracks(self, tracks, vehicle_journeys, tracks_map):
        """
        Load vehicle journey tracks and update the TracksVehicleJourney model.

        Steps:
        1. Merge the tracks, vehicle journeys, and tracks map DataFrames using the `merge_vj_tracks_df` function.
        2. Convert the merged DataFrame to a list of TracksVehicleJourney model instances.
        3. Use `bulk_create` to insert the instances into the TracksVehicleJourney table in batches.
        4. Update the 'id' column in the original DataFrame with the IDs of the created track journey records.

        Returns:
            pd.DataFrame: The merged DataFrame with the 'id' column updated to reflect the IDs of the created track journey records.
        """
        tracks_vjs = merge_vj_tracks_df(tracks, vehicle_journeys, tracks_map)
        if tracks_vjs.empty:
            return
        vj_tracks_objs = list(df_to_journeys_tracks(tracks_vjs))
        created = TracksVehicleJourney.objects.bulk_create(
            vj_tracks_objs, batch_size=BATCH_SIZE
        )
        tracks_vjs["id"] = pd.Series(
            (obj.id for obj in created), index=tracks_vjs.index
        )
        return tracks_vjs

    def load_flexible_service_operation_periods(self, vehicle_journeys):
        flexible_service_operation_periods = self.transformed.flexible_operation_periods

        if not flexible_service_operation_periods.empty and not vehicle_journeys.empty:
            df_merged = pd.merge(
                flexible_service_operation_periods,
                vehicle_journeys.reset_index()[
                    ["file_id", "id", "vehicle_journey_code"]
                ],
                how="inner",
                left_on=["file_id", "vehicle_journey_code"],
                right_on=["file_id", "vehicle_journey_code"],
            )
            flexible_service_operation_period_objs = list(
                df_to_flexible_service_operation_period(df_merged)
            )

            FlexibleServiceOperationPeriod.objects.bulk_create(
                flexible_service_operation_period_objs, batch_size=BATCH_SIZE
            )

    def load_serviced_organisation(self):

        """Load the serviced organistion in the database"""

        df_serviced_organisations = self.transformed.serviced_organisations
        if not df_serviced_organisations.empty:
            df_serviced_organisations.reset_index(inplace=True)

            existing_serviced_orgs = ServicedOrganisations.objects.all()
            existing_serviced_orgs_list = existing_serviced_orgs.values_list(
                "name", "organisation_code"
            )
            existing_serviced_orgs_list = [
                "".join(serviced_org) for serviced_org in existing_serviced_orgs_list
            ]

            serviced_org_objs = list(
                df_to_serviced_organisations(
                    df_serviced_organisations, existing_serviced_orgs_list
                )
            )

            created = ServicedOrganisations.objects.bulk_create(
                serviced_org_objs, batch_size=BATCH_SIZE
            )
            created_serviced_orgs = pd.DataFrame(
                (
                    {
                        "id": obj.id,
                        "serviced_org_ref": obj.organisation_code,
                        "name": obj.name,
                    }
                    for obj in created
                )
            )

            df_existing_serviced_orgs = pd.DataFrame(
                existing_serviced_orgs.values(),
                columns=["id", "organisation_code", "name"],
            )
            df_existing_serviced_orgs.rename(
                columns={"organisation_code": "serviced_org_ref"}, inplace=True
            )

            df_merged_serviced_orgs = pd.concat(
                [created_serviced_orgs, df_existing_serviced_orgs], axis=0
            )
            df_merged_serviced_orgs["serviced_org_ref"] = df_merged_serviced_orgs[
                "serviced_org_ref"
            ].astype(object)

            df_merge_db_and_file_inputs = pd.merge(
                df_serviced_organisations,
                df_merged_serviced_orgs,
                on=["serviced_org_ref", "name"],
                how="inner",
                suffixes=["_file", "_db"],
            )

            return df_merge_db_and_file_inputs
        else:
            return pd.DataFrame()

    def load_serviced_organisation_working_days(
        self, serviced_organisations, serviced_orgs_vjs
    ):
        columns_to_drop_duplicates = ["start_date", "end_date", "serviced_org_vj_id"]
        if not serviced_orgs_vjs.empty:
            merged_df = pd.merge(
                serviced_organisations,
                serviced_orgs_vjs,
                on=["file_id", "serviced_org_ref"],
            )
            serviced_organisation_working_days_objs = list(
                df_to_serviced_organisation_working_days(
                    merged_df, columns_to_drop_duplicates
                )
            )
            ServicedOrganisationWorkingDays.objects.bulk_create(
                serviced_organisation_working_days_objs, batch_size=BATCH_SIZE
            )

    def load_operating_profiles(self, merged_operating_profiles_and_journeys):
        refined_operating_profiles_and_journeys = (
            merged_operating_profiles_and_journeys.drop(
                columns=["exceptions_operational", "exceptions_date"], errors="ignore"
            )
        )
        refined_operating_profiles_and_journeys = (
            refined_operating_profiles_and_journeys.reset_index().query(
                "day_of_week != ''"
            )
        )
        refined_operating_profiles_and_journeys.drop_duplicates(
            subset=["vehicle_journey_code", "service_code", "file_id", "day_of_week"],
            inplace=True,
        )
        operating_profiles_objs = list(
            df_to_operating_profiles(refined_operating_profiles_and_journeys)
        )
        OperatingProfile.objects.bulk_create(
            operating_profiles_objs, batch_size=BATCH_SIZE
        )

    def load_operating_dates_exceptions(self, merged_operating_profiles_and_journeys):
        merged_operating_profiles_and_journeys.drop_duplicates(inplace=True)
        journey_mapping = get_journey_mappings(merged_operating_profiles_and_journeys)

        merged_operating_profiles_and_journeys = get_filtered_rows_by_journeys(
            merged_operating_profiles_and_journeys, journey_mapping
        )

        df_to_load = merged_operating_profiles_and_journeys[
            ["id", "exceptions_operational", "exceptions_date"]
        ].drop_duplicates()

        operating_dates_obj = list(
            df_to_operating_dates_exceptions(
                df_to_load[df_to_load["exceptions_operational"] == True]
            )
        )

        non_operating_dates_obj = list(
            df_to_non_operating_dates_exceptions(
                df_to_load[df_to_load["exceptions_operational"] == False]
            )
        )

        OperatingDatesExceptions.objects.bulk_create(
            operating_dates_obj, batch_size=BATCH_SIZE
        )
        NonOperatingDatesExceptions.objects.bulk_create(
            non_operating_dates_obj, batch_size=BATCH_SIZE
        )

    def load_operating_profiles_and_related_tables(self, vehicle_journeys):
        operating_profiles = self.transformed.operating_profiles
        if not operating_profiles.empty and not vehicle_journeys.empty:
            operating_profiles = operating_profiles.reset_index()
            vehicle_journeys = vehicle_journeys.rename(
                columns={"service_code_vj": "service_code"}
            )
            columns_operating_profiles = operating_profiles.columns

            if "exceptions_operational" in columns_operating_profiles:
                operating_profiles = operating_profiles[
                    [
                        "vehicle_journey_code",
                        "day_of_week",
                        "service_code",
                        "file_id",
                        "exceptions_operational",
                        "exceptions_date",
                    ]
                ]
            else:
                # When SpecialOperations or BankHolidays are not mentioned
                # exceptions_operational and exceptions_date fields are not set
                operating_profiles = operating_profiles[
                    ["vehicle_journey_code", "day_of_week", "service_code", "file_id"]
                ]

            merged_df = pd.merge(
                vehicle_journeys[
                    ["id", "vehicle_journey_code", "service_code", "file_id"]
                ],
                operating_profiles,
                on=["file_id", "service_code", "vehicle_journey_code"],
                how="inner",
            )

            self.load_operating_profiles(merged_df)
            self.load_operating_dates_exceptions(merged_df)

    def load_serviced_organisation_vehicle_journey(
        self, vehicle_journeys, serviced_organisations
    ):
        operating_profiles = self.transformed.operating_profiles
        if (
            not vehicle_journeys.empty
            and not serviced_organisations.empty
            and not operating_profiles.empty
        ):
            df_vehicle_journeys = vehicle_journeys.rename(
                columns={"id": "vehicle_journey_id", "service_code_vj": "service_code"}
            )

            serviced_organisations.rename(
                columns={"id": "serviced_org_id"}, inplace=True
            )
            operating_profiles.reset_index(inplace=True)

            operating_profiles_serviced_orgs_merged_df = pd.merge(
                operating_profiles[
                    [
                        "file_id",
                        "service_code",
                        "vehicle_journey_code",
                        "serviced_org_ref",
                        "operational",
                    ]
                ],
                serviced_organisations[
                    [
                        "file_id",
                        "serviced_org_id",
                        "serviced_org_ref",
                    ]
                ],
                on=["file_id", "serviced_org_ref"],
                how="inner",
                suffixes=["_op", "_so"],
            )
            operating_profiles_serviced_orgs_merged_df.drop_duplicates(inplace=True)

            operating_profiles_serviced_orgs_vehicle_journeys_merged_df = pd.merge(
                operating_profiles_serviced_orgs_merged_df,
                df_vehicle_journeys[
                    [
                        "file_id",
                        "service_code",
                        "vehicle_journey_id",
                        "vehicle_journey_code",
                    ]
                ],
                on=["file_id", "service_code", "vehicle_journey_code"],
                how="inner",
            )
            operating_profiles_serviced_orgs_vehicle_journeys_merged_df.drop_duplicates(
                inplace=True
            )
            serviced_org_vehicle_journey_objs = list(
                df_to_serviced_org_vehicle_journey(
                    operating_profiles_serviced_orgs_vehicle_journeys_merged_df
                )
            )
            created = ServicedOrganisationVehicleJourney.objects.bulk_create(
                serviced_org_vehicle_journey_objs, batch_size=BATCH_SIZE
            )

            if not operating_profiles_serviced_orgs_vehicle_journeys_merged_df.empty:
                operating_profiles_serviced_orgs_vehicle_journeys_merged_df[
                    "serviced_org_vj_id"
                ] = [obj.id for obj in created]

            return operating_profiles_serviced_orgs_vehicle_journeys_merged_df

        return pd.DataFrame()

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

        adapter.info("Bulk creating service patterns.")
        service_pattern_objs = df_to_service_patterns(revision, service_patterns)
        created = ServicePattern.objects.bulk_create(
            service_pattern_objs, batch_size=BATCH_SIZE
        )

        if not service_patterns.empty:
            service_patterns["id"] = [obj.id for obj in created]

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

        adapter.info("Finished loading service pattern")
        return service_patterns

    def load_service_patterns_stops(
        self,
        service_patterns: pd.DataFrame,
        vehicle_journeys: pd.DataFrame,
        revision: pd.DataFrame,
    ):
        """Merge vehicle journeys if present to map the foreign key and load service pattern stops data."""
        # ADD ServicePattern Associations

        # Add ServicePattern m2m ServiceLink
        # TODO - associate ServiceLinks - need explicit through table as ServiceLink
        # can appear more than once on
        #  the ServicePattern
        # self.add_service_pattern_to_service_links(service_pattern_to_service_links)

        # Create ServicePatternStops and add to ServicePattern
        adapter = get_dataset_adapter_from_revision(logger, revision=revision)
        adapter.info("Creating service pattern stops.")
        service_pattern_stops = self.transformed.service_pattern_stops
        if (
            not vehicle_journeys.empty
            and "journey_pattern_ref" in vehicle_journeys.columns
        ):
            service_pattern_stops = service_pattern_stops.merge(
                vehicle_journeys.reset_index()[
                    ["file_id", "journey_pattern_ref", "vehicle_journey_code", "id"]
                ],
                left_on=["file_id", "journey_pattern_id", "vehicle_journey_code"],
                right_on=["file_id", "journey_pattern_ref", "vehicle_journey_code"],
            )

        if not service_patterns.empty:
            sp_records = service_patterns.copy()
            sp_records = sp_records.rename(columns={"id": "db_service_pattern_id"})
            service_pattern_stops = service_pattern_stops.merge(
                sp_records.reset_index()[
                    ["file_id", "service_pattern_id", "db_service_pattern_id"]
                ],
                on=["file_id", "service_pattern_id"],
            )

        add_service_pattern_to_service_pattern_stops(
            service_pattern_stops, service_patterns
        )

        adapter.info("Finished loading service pattern stops.")

    def load_booking_arrangements(self, services, revision):
        adapter = get_dataset_adapter_from_revision(logger, revision=revision)
        booking_arrangements = self.transformed.booking_arrangements
        if not booking_arrangements.empty:
            booking_arrangements_reset = booking_arrangements.reset_index()
            services_reset = services.reset_index()

            merged_df = booking_arrangements_reset.merge(
                services_reset[["file_id", "service_code", "id"]],
                on=["file_id", "service_code"],
                how="left",
            )
            merged_df.set_index(["service_code", "id"], inplace=True)

            adapter.info("Bulk creating booking arrangements")

            booking_arrangements_objs = list(
                df_to_booking_arrangements(revision, merged_df)
            )

            BookingArrangements.objects.bulk_create(
                booking_arrangements_objs, batch_size=BATCH_SIZE
            )

            return merged_df
