import numpy as np
import pandas as pd
from waffle import flag_is_active

from transit_odp.pipelines.pipelines.dataset_etl.utils.dataframes import (
    create_naptan_stoppoint_df,
    create_naptan_stoppoint_df_from_queryset,
    create_naptan_flexible_zone_df_from_queryset,
)
from transit_odp.pipelines.pipelines.dataset_etl.utils.models import (
    ExtractedData,
    TransformedData,
)
from transit_odp.pipelines.pipelines.dataset_etl.utils.transform import (
    create_route_links,
    create_route_to_route_links,
    create_routes,
    filter_operating_profiles,
    get_most_common_localities,
    get_vehicle_journey_with_timing_refs,
    get_vehicle_journey_without_timing_refs,
    merge_journey_pattern_with_vj_for_departure_time,
    merge_vehicle_journeys_with_jp,
    merge_serviced_organisations_with_operating_profile,
    merge_lines_with_vehicle_journey,
    sync_localities_and_adminareas,
    transform_line_names,
    transform_service_links,
    transform_service_pattern_stops,
    transform_service_pattern_to_service_links,
    transform_service_patterns,
    transform_stop_sequence,
    transform_geometry,
    transform_flexible_stop_sequence,
    transform_flexible_service_patterns,
    transform_flexible_service_pattern_to_service_links,
    create_flexible_routes,
    merge_flexible_jd_with_jp,
)
from transit_odp.naptan.models import StopPoint, FlexibleZone
from transit_odp.timetables.utils import get_line_description_based_on_direction


class TransXChangeTransformer:
    def __init__(self, extracted_data: ExtractedData, stop_point_cache=None):
        self.extracted_data = extracted_data
        self.stop_point_cache = stop_point_cache

    def transform(self) -> TransformedData:
        """Transform various dataframes created during the extraction stage, so that these records can be loaded into expected tables in the loader stage"""
        services = self.extracted_data.services.iloc[:]  # make transform immutable
        journey_patterns = self.extracted_data.journey_patterns.copy()
        flexible_journey_patterns = self.extracted_data.flexible_journey_patterns.copy()
        flexible_vehicle_journeys = self.extracted_data.flexible_vehicle_journeys.copy()
        jp_to_jps = self.extracted_data.jp_to_jps.copy()
        jp_sections = self.extracted_data.jp_sections.copy()
        timing_links = self.extracted_data.timing_links.copy()
        stop_points = self.extracted_data.stop_points.copy()
        provisional_stops = self.extracted_data.provisional_stops.copy()
        booking_arrangements = self.extracted_data.booking_arrangements.copy()
        vehicle_journeys = self.extracted_data.vehicle_journeys.copy()
        serviced_organisations = self.extracted_data.serviced_organisations.copy()
        operating_profiles = self.extracted_data.operating_profiles.copy()
        flexible_stop_points = self.extracted_data.flexible_stop_points.copy()
        flexible_journey_details = self.extracted_data.flexible_journey_details.copy()
        df_flexible_operation_periods = (
            self.extracted_data.flexible_operation_periods.copy()
        )
        lines = self.extracted_data.lines.copy()
        is_timetable_visualiser_active = flag_is_active(
            "", "is_timetable_visualiser_active"
        )
        # Match stop_points with DB
        stop_points = self.sync_stop_points(stop_points, provisional_stops)
        stop_points = sync_localities_and_adminareas(stop_points)
        # stop_points = self.sync_admin_areas(stop_points)
        most_common_localities = get_most_common_localities(stop_points)

        flexible_stop_points = flexible_stop_points.merge(
            stop_points, left_index=True, right_index=True
        )
        stop_points = stop_points.loc[
            ~stop_points.index.isin(flexible_stop_points.index)
        ]

        # Create missing route information
        route_links = pd.DataFrame()
        if not timing_links.empty:
            route_links = create_route_links(timing_links, stop_points)

        if (
            not journey_patterns.empty
            and not jp_to_jps.empty
            and not timing_links.empty
        ):
            create_routes(journey_patterns, jp_to_jps, jp_sections, timing_links)

        df_merged_vehicle_journeys = pd.DataFrame()
        vehicle_journeys_with_timing_refs = pd.DataFrame()

        operating_profiles = filter_operating_profiles(operating_profiles, services)

        if not vehicle_journeys.empty and not journey_patterns.empty:
            vehicle_journeys_with_timing_refs = get_vehicle_journey_with_timing_refs(
                vehicle_journeys
            )
            vehicle_journeys = get_vehicle_journey_without_timing_refs(vehicle_journeys)

            df_merged_vehicle_journeys = merge_vehicle_journeys_with_jp(
                vehicle_journeys, journey_patterns
            )
            if is_timetable_visualiser_active:
                vehicle_journeys = merge_lines_with_vehicle_journey(
                    df_merged_vehicle_journeys.reset_index(), lines
                )

            journey_patterns = merge_journey_pattern_with_vj_for_departure_time(
                vehicle_journeys,
                journey_patterns,
                is_timetable_visualiser_active,
            )

        df_merged_serviced_organisations = pd.DataFrame()
        if not serviced_organisations.empty and not operating_profiles.empty:
            df_merged_serviced_organisations = (
                merge_serviced_organisations_with_operating_profile(
                    serviced_organisations, operating_profiles
                )
            )

        route_to_route_links = pd.DataFrame()
        if not journey_patterns.empty and not jp_to_jps.empty:
            route_to_route_links = create_route_to_route_links(
                journey_patterns,
                jp_to_jps,
                timing_links,
                vehicle_journeys_with_timing_refs,
            )
        line_names = transform_line_names(
            self.extracted_data.line_names
        )  # Transform route information into service patterns
        service_links = pd.DataFrame()
        if not route_links.empty:
            service_links = transform_service_links(route_links)

        service_patterns = pd.DataFrame()
        service_pattern_to_service_links = pd.DataFrame()
        service_pattern_stops = pd.DataFrame()
        if not journey_patterns.empty and not route_to_route_links.empty:
            if is_timetable_visualiser_active:
                drop_duplicates_columns_sp = ["service_code", "route_hash", "line_name"]
            else:
                drop_duplicates_columns_sp = ["service_code", "route_hash"]
            service_patterns = transform_service_patterns(
                journey_patterns, drop_duplicates_columns_sp
            )
            (
                service_pattern_to_service_links,
                drop_columns,
            ) = transform_service_pattern_to_service_links(  # noqa: E501
                service_patterns, route_to_route_links, route_links
            )
            # aggregate stop_sequence and geometry
            service_pattern_stops = transform_service_pattern_stops(
                service_pattern_to_service_links, stop_points
            )

            service_patterns = transform_stop_sequence(
                service_pattern_stops, service_patterns
            )
            if is_timetable_visualiser_active:
                service_patterns["description"] = service_patterns.apply(
                    get_line_description_based_on_direction, axis=1
                )
                service_patterns.drop(
                    columns=["inbound_description", "outbound_description"],
                    axis=1,
                    inplace=True,
                )
            service_pattern_to_service_links.drop(
                columns=drop_columns, axis=1, inplace=True
            )
            if drop_columns:
                service_patterns.drop(columns=["departure_time"], axis=1, inplace=True)

        stop_points.drop(columns=["common_name"], axis=1, inplace=True)

        ### logic for flexible stop points transformation
        if not flexible_stop_points.empty:
            # sync flexible stops with flexible zone
            flexible_zone = self.sync_flexible_zone(flexible_stop_points)

            # merge the flexible stop points and flexible zone to get the required geometry
            flexible_stop_points_with_geometry = (
                (
                    flexible_stop_points.merge(
                        flexible_zone,
                        how="left",
                        left_on="atco_code",
                        right_on="atco_code",
                    )
                )
                if not flexible_zone.empty
                else flexible_stop_points
            )
            # get the required geometry for flexible stops
            flexible_stop_points_with_geometry = transform_geometry(
                flexible_stop_points_with_geometry
            )
            if not flexible_journey_patterns.empty:
                # create unique route hash for flexible jp
                flexible_journey_patterns = create_flexible_routes(
                    flexible_journey_patterns
                )

                df_merged_flexible_vehicle_journeys = pd.DataFrame()

                if not flexible_vehicle_journeys.empty:
                    flexible_vehicle_journeys.drop(
                        columns=["service_code"], axis=1, inplace=True
                    )
                    flexible_vehicle_journeys.reset_index().set_index(
                        ["file_id", "journey_pattern_ref"], inplace=True
                    )
                    df_merged_flexible_vehicle_journeys = (
                        merge_vehicle_journeys_with_jp(
                            flexible_vehicle_journeys, flexible_journey_patterns
                        )
                    )

                if not flexible_journey_details.empty:
                    flexible_journey_details = merge_flexible_jd_with_jp(
                        flexible_journey_details, flexible_journey_patterns
                    )
                    # create flexible timing link
                    flexible_timing_links = self.create_flexible_timing_link(
                        flexible_journey_details
                    )

                    # create flexible service link
                    if not flexible_timing_links.empty:
                        flexible_service_links = transform_service_links(
                            flexible_timing_links
                        )

                        flexible_service_patterns = pd.DataFrame()
                        flexible_service_pattern_stops = pd.DataFrame()
                        # create flexible service_patterns and service_patterns_stops/
                        flexible_service_patterns = transform_flexible_service_patterns(
                            flexible_timing_links
                        )

                        (
                            flexible_service_pattern_to_service_links,
                            drop_columns,
                        ) = transform_flexible_service_pattern_to_service_links(
                            flexible_service_patterns
                        )

                        flexible_service_pattern_stops = (
                            transform_service_pattern_stops(
                                flexible_service_pattern_to_service_links,
                                flexible_stop_points_with_geometry,
                            )
                        )

                        flexible_service_patterns = transform_flexible_stop_sequence(
                            flexible_service_pattern_stops, flexible_service_patterns
                        )

                        flexible_service_pattern_to_service_links.drop(
                            columns=drop_columns, axis=1, inplace=True
                        )

                        # merge the required dataframes for standard and flexible
                        service_links = pd.concat(
                            [service_links, flexible_service_links]
                        )
                        service_pattern_to_service_links = pd.concat(
                            [
                                service_pattern_to_service_links,
                                flexible_service_pattern_to_service_links,
                            ]
                        )
                        service_patterns = pd.concat(
                            [service_patterns, flexible_service_patterns]
                        )
                        service_pattern_stops = pd.concat(
                            [
                                service_pattern_stops,
                                flexible_service_pattern_stops,
                            ]
                        )
                        service_pattern_stops.dropna(
                            subset=["stop_atco", "geometry"], inplace=True
                        )

                        df_merged_vehicle_journeys = pd.concat(
                            [
                                df_merged_flexible_vehicle_journeys,
                                df_merged_vehicle_journeys,
                            ]
                        )
        return TransformedData(
            services=services,
            service_patterns=service_patterns,
            service_pattern_to_service_links=service_pattern_to_service_links,
            service_links=service_links,
            stop_points=stop_points,
            service_pattern_stops=service_pattern_stops,
            booking_arrangements=booking_arrangements,
            # carry forward metadata
            schema_version=self.extracted_data.schema_version,
            creation_datetime=self.extracted_data.creation_datetime,
            modification_datetime=self.extracted_data.modification_datetime,
            import_datetime=self.extracted_data.import_datetime,
            line_count=self.extracted_data.line_count,
            line_names=line_names,
            stop_count=len(stop_points),
            most_common_localities=most_common_localities,
            timing_point_count=self.extracted_data.timing_point_count,
            vehicle_journeys=df_merged_vehicle_journeys,
            serviced_organisations=df_merged_serviced_organisations,
            flexible_operation_periods=df_flexible_operation_periods,
            operating_profiles=operating_profiles,
        )

    def sync_stop_points(self, stop_points, provisional_stops):
        stop_point_cache = self.stop_point_cache
        # Sync with DB
        stop_point_refs = set(stop_points.index).union(set(provisional_stops.index))
        cached_stops = set(stop_point_cache.index)

        # Fetch stops not in cache
        fetch_stops = stop_point_refs - cached_stops

        if fetch_stops != set():
            qs = StopPoint.objects.filter(atco_code__in=fetch_stops)
            fetched = create_naptan_stoppoint_df_from_queryset(qs)
            fetched["common_name"] = None

            # Create missing stops
            # Note we do not create any real StopPoints, just a lookup of atco_code
            # to id (nullable)
            # However, we do create ServicePatternStop for every StopPoint referenced
            # in the file. This allows us to
            # create ServiceLinks and thus the complete ServicePattern even if
            # some stops do not exist in Naptan db
            missing_stops = fetch_stops - set(fetched.index)

            # Handle non NAPTAN stops
            # There is a possibility of finding easting, northing (locations) of non
            # NAPTAN stops in TXC file,
            # so we do create ServicePattern geometries for those stops as well
            missing = create_naptan_stoppoint_df(
                data=(
                    {
                        "atco_code": index,
                        "naptan_id": np.nan,
                        "geometry": provisional_stops.loc[index, "geometry"]
                        if index in provisional_stops.index.values
                        else None,
                        "locality_id": provisional_stops.loc[index, "locality"]
                        if index in provisional_stops.index
                        else "",
                    }
                    for index in missing_stops
                )
            )
            provisional_stops = provisional_stops.drop(columns=["geometry", "locality"])
            stop_points = pd.concat([stop_points, provisional_stops], axis=0)
            df_missing_stops_merged = pd.merge(
                missing,
                stop_points,
                left_index=True,
                right_index=True,
                how="left",
                suffixes=["", ""],
            )
            # update cache with fetched stops and missing stops
            stop_point_cache = pd.concat(
                [stop_point_cache, fetched, df_missing_stops_merged], sort=True
            )
        else:
            if "common_name" not in stop_point_cache.columns:
                stop_point_cache["common_name"] = ""
        # Return the subselection of stop points seen in the doc (useful when
        # processing large zip files)
        return stop_point_cache.reindex(sorted(stop_point_refs))

    def sync_flexible_zone(self, flexible_stop_points):
        """
        This function performs below operations
        1. extract the flexible zone for stops with bus_stop_type = 'flexible'
        2. merge the provisional flexible stops with the extracted flexbile zone dataset
        """
        # get provisional flexible stop points with naptan_stoppoint_id nan
        provisional_flexible_stops = flexible_stop_points[
            flexible_stop_points["naptan_id"].isna()
        ].reset_index()

        if not provisional_flexible_stops.empty:
            provisional_flexible_stops[
                "flexible_location"
            ] = provisional_flexible_stops["geometry"].apply(
                lambda row: [row] if not isinstance(row, list) else row
            )

        filtered_stop_points = flexible_stop_points[
            (flexible_stop_points["bus_stop_type"] == "flexible")
            & (~flexible_stop_points["naptan_id"].isna())
        ]

        filtered_stop_points_naptan_id_list = filtered_stop_points["naptan_id"].tolist()
        flexiblezone_qs = FlexibleZone.objects.filter(
            naptan_stoppoint_id__in=filtered_stop_points_naptan_id_list
        )
        flexible_zone_df = create_naptan_flexible_zone_df_from_queryset(flexiblezone_qs)

        filtered_stop_points_naptan_id = pd.DataFrame()
        if not flexible_zone_df.empty:
            filtered_stop_points_naptan_id = filtered_stop_points.reset_index().merge(
                flexible_zone_df.reset_index(),
                how="left",
                left_on="naptan_id",
                right_on="naptan_id",
            )
            filtered_stop_points_naptan_id = filtered_stop_points_naptan_id[
                ["atco_code", "flexible_location"]
            ]

        # concatenate provisional flexible stops and flexible naptan stops
        filtered_stop_points_naptan_id = pd.concat(
            [filtered_stop_points_naptan_id, provisional_flexible_stops]
        )
        if not filtered_stop_points_naptan_id.empty:
            filtered_stop_points_naptan_id = filtered_stop_points_naptan_id[
                ["atco_code", "flexible_location"]
            ]
            filtered_stop_points_naptan_id.set_index("atco_code", inplace=True)
        return filtered_stop_points_naptan_id

    def create_flexible_timing_link(self, flexible_journey_details):
        """
        This function transform the flexible journery details to get the sequence of stops
        """

        def get_stop_sequence(group, journey_pattern_id):
            group["order"] = range(len(group))
            group["journey_pattern_id"] = journey_pattern_id
            group["from_stop_atco"] = group["atco_code"].shift(0)
            group["to_stop_atco"] = group["atco_code"].shift(-1)
            return group.dropna(subset=["to_stop_atco"])

        if not flexible_journey_details.empty:
            flexible_timing_links = (
                flexible_journey_details.reset_index()
                .groupby("journey_pattern_id")
                .apply(lambda group: get_stop_sequence(group, group.name))
            )

            flexible_timing_links = flexible_timing_links[
                [
                    "file_id",
                    "order",
                    "from_stop_atco",
                    "to_stop_atco",
                    "journey_pattern_id",
                    "service_code",
                    "route_hash",
                ]
            ].set_index(["file_id", "journey_pattern_id"])
            return flexible_timing_links
        return pd.DataFrame()
