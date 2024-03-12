import numpy as np
import pandas as pd
from waffle import flag_is_active

from transit_odp.pipelines.pipelines.dataset_etl.utils.dataframes import (
    create_naptan_stoppoint_df,
    create_naptan_stoppoint_df_from_queryset,
)
from transit_odp.pipelines.pipelines.dataset_etl.utils.models import (
    ExtractedData,
    TransformedData,
)
from transit_odp.pipelines.pipelines.dataset_etl.utils.transform import (
    create_route_links,
    create_route_to_route_links,
    create_routes,
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
)
from transit_odp.timetables.utils import get_line_description_based_on_direction

from transit_odp.transmodel.models import StopPoint


class TransXChangeTransformer:
    def __init__(self, extracted_data: ExtractedData, stop_point_cache=None):
        self.extracted_data = extracted_data
        self.stop_point_cache = stop_point_cache

    def transform(self) -> TransformedData:
        services = self.extracted_data.services.iloc[:]  # make transform immutable
        journey_patterns = self.extracted_data.journey_patterns.copy()
        jp_to_jps = self.extracted_data.jp_to_jps.copy()
        jp_sections = self.extracted_data.jp_sections.copy()
        timing_links = self.extracted_data.timing_links.copy()
        stop_points = self.extracted_data.stop_points.copy()
        provisional_stops = self.extracted_data.provisional_stops.copy()
        booking_arrangements = self.extracted_data.booking_arrangements.copy()
        vehicle_journeys = self.extracted_data.vehicle_journeys.copy()
        serviced_organisations = self.extracted_data.serviced_organisations.copy()
        operating_profiles = self.extracted_data.operating_profiles.copy()
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
            operating_profiles=self.extracted_data.operating_profiles,
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
