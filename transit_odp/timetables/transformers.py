import numpy as np
import pandas as pd

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
    get_most_common_localities,
    merge_vehicle_journeys_with_jp,
    merge_serviced_organisations_with_operating_profile,
    sync_localities_and_adminareas,
    transform_line_names,
    transform_service_links,
    transform_service_pattern_stops,
    transform_service_pattern_to_service_links,
    transform_service_patterns,
    transform_stop_sequence,
    transform_geometry,
    # create_flexible_jps,
    # create_flexible_route_links,
    # create_flexible_route_to_route_links,
    # transform_flexible_service_links,
    # create_flexible_routes,
    # transform_flexible_service_patterns,
    # transform_flexible_service_pattern_to_service_links,
    # transform_flexible_service_pattern_stops,
    transform_flexible_stop_sequence,
)
from transit_odp.transmodel.models import StopPoint, FlexibleZone


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
        flexible_stop_points = self.extracted_data.flexible_stop_points.copy()
        flexible_timing_links = self.extracted_data.flexible_timing_links.copy()
        flexible_journey_patterns = self.extracted_data.flexible_journey_patterns.copy()
        flexible_jp_to_jps = self.extracted_data.flexible_jp_to_jps.copy()
        flexible_jp_sections = self.extracted_data.flexible_jp_sections.copy()

        print(f"stop_points before removing flexible: {list(stop_points.index.values)}")
        # remove flexible stop points from stop points
        if not flexible_stop_points.empty:
            # get atco_code value from index
            flexible_stop_points_list = list(flexible_stop_points.index.values)
            print(f"flexible_stop_points_list: {flexible_stop_points_list}")
            # stop_points = stop_points.reset_index()
            stop_points = stop_points[
                ~stop_points.index.isin(flexible_stop_points_list)
            ]
            # stop_points = stop_points[~stop_points['atco_code'].isin(flexible_stop_points_list)]
            # stop_points.set_index("atco_code", inplace=True)

        print(f"stop_points after removing flexible: {list(stop_points.index.values)}")
        # Match stop_points with DB
        stop_points = self.sync_stop_points(stop_points, provisional_stops)
        stop_points = sync_localities_and_adminareas(stop_points)
        # stop_points = self.sync_admin_areas(stop_points)
        most_common_localities = get_most_common_localities(stop_points)

        df_merged_vehicle_journeys = pd.DataFrame()
        if not vehicle_journeys.empty and not journey_patterns.empty:
            df_merged_vehicle_journeys = merge_vehicle_journeys_with_jp(
                vehicle_journeys, journey_patterns
            )

        df_merged_serviced_organisations = pd.DataFrame()
        if not serviced_organisations.empty and not operating_profiles.empty:
            df_merged_serviced_organisations = (
                merge_serviced_organisations_with_operating_profile(
                    serviced_organisations, operating_profiles
                )
            )

        # Create missing route information
        route_links = pd.DataFrame()
        if not timing_links.empty:
            timing_links.to_csv("timing_links_before_routes.csv")
            route_links = create_route_links(timing_links, stop_points)
            route_links.to_csv("route_links_transform.csv")

        if (
            not journey_patterns.empty
            and not jp_to_jps.empty
            and not timing_links.empty
        ):
            journey_patterns.to_csv("journey_patterns_before_create_routes.csv")
            jp_to_jps.to_csv("jp_to_jps_before_create_routes.csv")
            jp_sections.to_csv("jp_sections_before_create_routes.csv")
            timing_links.to_csv("timing_links_before_create_routes.csv")
            create_routes(journey_patterns, jp_to_jps, jp_sections, timing_links)
            journey_patterns.to_csv("journey_patterns_after_create_routes.csv")
            jp_to_jps.to_csv("jp_to_jps_after_create_routes.csv")
            jp_sections.to_csv("jp_sections_after_create_routes.csv")
            timing_links.to_csv("timing_links_after_create_routes.csv")

        route_to_route_links = pd.DataFrame()
        if not journey_patterns.empty and not jp_to_jps.empty:
            route_to_route_links = create_route_to_route_links(
                journey_patterns, jp_to_jps, timing_links
            )
            route_to_route_links.to_csv("route_to_route_links_transform.csv")

        line_names = transform_line_names(self.extracted_data.line_names)

        # Transform route information into service patterns
        service_links = pd.DataFrame()
        if not route_links.empty:
            service_links = transform_service_links(route_links)

        service_patterns = pd.DataFrame()
        service_pattern_to_service_links = pd.DataFrame()
        service_pattern_stops = pd.DataFrame()
        if not journey_patterns.empty and not route_to_route_links.empty:
            service_patterns = transform_service_patterns(journey_patterns)
            service_patterns.to_csv("service_patterns_before.csv")
            route_to_route_links.to_csv("route_to_route_links_before_service_link.csv")
            route_links.to_csv("route_links_before_service_link.csv")
            service_pattern_to_service_links = (
                transform_service_pattern_to_service_links(  # noqa: E501
                    service_patterns, route_to_route_links, route_links
                )
            )
            service_pattern_to_service_links.to_csv(
                "service_pattern_to_service_links.csv"
            )

            # aggregate stop_sequence and geometry
            service_pattern_stops = transform_service_pattern_stops(
                service_pattern_to_service_links, stop_points
            )

            service_pattern_stops.to_csv("service_pattern_stops.csv")
            service_patterns = transform_stop_sequence(
                service_pattern_stops, service_patterns
            )
            service_patterns.to_csv("service_patterns_final.csv")

        ### logic for flexible stop points transformation
        if not flexible_stop_points.empty:
            # 1. extract naptan points data
            flexible_stop_points_with_naptan_id = self.sync_flexible_stop_points(
                flexible_stop_points
            )
            flexible_stop_points_with_naptan_id.to_csv(
                "flexible_stop_points_with_naptan_id.csv"
            )

            flexible_stop_points_with_naptan_id = sync_localities_and_adminareas(
                flexible_stop_points_with_naptan_id
            )
            flexible_stop_points_with_naptan_id.to_csv(
                "flexible_stop_points_with_naptan_id_adminarea.csv"
            )
            print(
                f"flexible_stop_points_with_naptan_id.columns: {flexible_stop_points_with_naptan_id.columns}"
            )
            print(
                f"flexible_stop_points_with_naptan_id.index: {flexible_stop_points_with_naptan_id.index}"
            )

            # 2. extract flexible zone data
            flexible_zone = self.sync_flexible_zone(flexible_stop_points_with_naptan_id)
            flexible_zone.to_csv("flexible_zone.csv")

            # 3. merge the flexible stop points and flexible zone to get the required geometry
            flexible_stop_points_with_geometry = (
                flexible_stop_points_with_naptan_id.merge(
                    flexible_zone, how="left", left_on="atco_code", right_on="atco_code"
                )
            )
            flexible_stop_points_with_geometry = transform_geometry(
                flexible_stop_points_with_geometry
            )
            flexible_stop_points_with_geometry.to_csv(
                "flexible_stop_points_with_geometry.csv"
            )

            # 4. create dummy route_link_ref (create from_atco and to_atco)
            # flexible_route_links = create_flexible_route_links(flexible_timing_links)
            flexible_route_links = create_route_links(
                flexible_timing_links, flexible_stop_points_with_geometry
            )
            flexible_route_links.to_csv("flexible_route_links_transform.csv")

            # 5. create flexible routes
            create_routes(
                flexible_journey_patterns,
                flexible_jp_to_jps,
                flexible_jp_sections,
                flexible_timing_links,
            )
            flexible_journey_patterns.to_csv(
                "flexible_journey_patterns_after_routes.csv"
            )
            flexible_jp_sections.to_csv("flexible_jp_sections_after_routes.csv")

            # 6. create route hash for flexible route link
            # flexible_route_to_route_links = create_flexible_route_to_route_links(flexible_journey_patterns, flexible_jp_to_jps, flexible_timing_links)
            flexible_route_to_route_links = create_route_to_route_links(
                flexible_journey_patterns, flexible_jp_to_jps, flexible_timing_links
            )
            flexible_route_to_route_links.to_csv("flexible_route_to_route_links.csv")

            # 7. create flexible service link
            # flexible_service_links = transform_flexible_service_links(flexible_route_links)
            flexible_service_links = transform_service_links(flexible_route_links)
            flexible_service_links.to_csv("flexible_service_links.csv")

            # 8. create flexible service_patterns and service_patterns_stops
            flexible_service_patterns = pd.DataFrame()
            flexible_service_pattern_to_service_links = pd.DataFrame()
            flexible_service_pattern_stops = pd.DataFrame()

            flexible_service_patterns = transform_service_patterns(
                flexible_journey_patterns
            )
            flexible_service_patterns.to_csv("flexible_service_patterns.csv")

            flexible_service_pattern_to_service_links = (
                transform_service_pattern_to_service_links(  # noqa: E501
                    flexible_service_patterns,
                    flexible_route_to_route_links,
                    flexible_route_links,
                )
            )
            flexible_service_pattern_to_service_links.to_csv(
                "flexible_service_pattern_to_service_links.csv"
            )

            flexible_service_pattern_stops = transform_service_pattern_stops(
                flexible_service_pattern_to_service_links,
                flexible_stop_points_with_geometry,
            )
            flexible_service_pattern_stops.to_csv("flexible_service_pattern_stops.csv")

            flexible_service_patterns = transform_flexible_stop_sequence(
                flexible_service_pattern_stops, flexible_service_patterns
            )
            flexible_service_patterns.to_csv("flexible_service_patterns_final.csv")

            service_patterns = pd.concat(
                [
                    service_patterns.reset_index(),
                    flexible_service_patterns.reset_index(),
                ]
            )

            print(f"service_pattern_stops.index: {service_pattern_stops.index}")
            print(
                f"flexible_service_pattern_stops.index: {flexible_service_pattern_stops.index}"
            )
            print(
                f"flexible_service_pattern_stops.columns: {flexible_service_pattern_stops.columns}"
            )
            service_pattern_stops = service_pattern_stops.reset_index().droplevel(
                level=0, axis=1
            )
            flexible_service_pattern_stops = (
                flexible_service_pattern_stops.reset_index().droplevel(level=0, axis=1)
            )
            print(
                f"flexible_service_pattern_stops after dropping: {flexible_service_pattern_stops.columns}"
            )
            service_pattern_stops = pd.concat(
                [service_pattern_stops, flexible_service_pattern_stops]
            )
            print(
                f"service_pattern_stops after concat: {service_pattern_stops.columns}"
            )
            print(f"service_pattern_stops index: {service_pattern_stops.index}")
            service_pattern_stops.set_index(
                ["file_id"], inplace=True, append=True, verify_integrity=True
            )
            print(f"service_pattern_stops after index: {service_pattern_stops.columns}")
            print(f"service_pattern_stops index1: {service_pattern_stops.index}")
            service_pattern_stops.to_csv("service_pattern_stops_final.csv")

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

            # update cache with fetched stops and missing stops
            stop_point_cache = pd.concat(
                [stop_point_cache, fetched, missing], sort=True
            )

        # Return the subselection of stop points seen in the doc (useful when
        # processing large zip files)
        return stop_point_cache.reindex(sorted(stop_point_refs))

    def sync_flexible_stop_points(self, flexible_stop_points):
        # get stop points from index
        stop_ponts_list = list(flexible_stop_points.index.values)
        qs = StopPoint.objects.filter(atco_code__in=stop_ponts_list)
        naptan_stop_points_df = create_naptan_stoppoint_df_from_queryset(qs)
        flexible_stop_points = flexible_stop_points.reset_index().merge(
            naptan_stop_points_df.reset_index(),
            how="left",
            left_on="atco_code",
            right_on="atco_code",
        )

        flexible_stop_points.set_index("atco_code", inplace=True)
        return flexible_stop_points

    def sync_flexible_zone(self, flexible_stop_points_with_naptan_id):
        filtered_stop_points = flexible_stop_points_with_naptan_id[
            flexible_stop_points_with_naptan_id["bus_stop_type"] == "flexible"
        ]
        filtered_stop_points_naptan_id = list(filtered_stop_points["naptan_id"].values)
        qs = FlexibleZone.objects.filter(
            naptan_stoppoint_id__in=filtered_stop_points_naptan_id
        )
        flexible_zone_df = create_naptan_flexible_zone_df_from_queryset(qs)
        filtered_stop_points_naptan_id = filtered_stop_points.reset_index().merge(
            flexible_zone_df.reset_index(),
            how="left",
            left_on="naptan_id",
            right_on="naptan_id",
        )
        filtered_stop_points_naptan_id = filtered_stop_points_naptan_id[
            ["atco_code", "flexible_location"]
        ]
        filtered_stop_points_naptan_id.set_index("atco_code", inplace=True)
        return filtered_stop_points_naptan_id
