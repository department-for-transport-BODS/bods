import numpy as np
import pandas as pd
import uuid

from celery.utils.log import get_task_logger

from transit_odp.naptan.models import StopPoint, FlexibleZone
from transit_odp.pipelines.pipelines.dataset_etl.utils.etl_base import ETLUtility
from transit_odp.pipelines.pipelines.dataset_etl.utils.models import (
    ExtractedData,
    TransformedData,
)

from .utils.dataframes import (
    create_naptan_stoppoint_df,
    create_naptan_stoppoint_df_from_queryset,
    create_naptan_flexible_zone_df_from_queryset,
)
from .utils.transform import (
    agg_service_pattern_sequences,
    create_route_links,
    create_route_to_route_links,
    create_routes,
    create_stop_sequence,
    get_most_common_districts,
    get_most_common_localities,
    sync_localities_and_adminareas,
    transform_line_names,
    transform_service_links,
    transform_service_pattern_stops,
    transform_service_pattern_to_service_links,
    transform_service_patterns,
    transform_stop_sequence,
    transform_geometry,
    transform_flexible_stop_sequence,
    merge_vehicle_journeys_with_jp,
    transform_flexible_service_patterns,
)

logger = get_task_logger(__name__)


class Transform(ETLUtility):
    def __init__(self, feed_parser):
        self.feed_parser = feed_parser

    def transform(self, extracted_data: ExtractedData) -> TransformedData:
        services = extracted_data.services.iloc[:]  # make transform immutable
        journey_patterns = extracted_data.journey_patterns.copy()
        jp_to_jps = extracted_data.jp_to_jps.copy()
        jp_sections = extracted_data.jp_sections.copy()
        timing_links = extracted_data.timing_links.copy()
        stop_points = extracted_data.stop_points.copy()
        vehicle_journeys = self.extracted_data.vehicle_journeys.copy()
        provisional_stops = extracted_data.provisional_stops.copy()
        flexible_stop_points = extracted_data.flexible_stop_points.copy()
        flexible_journey_details = extracted_data.flexible_journey_details.copy()

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

        if not vehicle_journeys.empty and not journey_patterns.empty:
            df_merged_vehicle_journeys = merge_vehicle_journeys_with_jp(
                vehicle_journeys, journey_patterns
            )

        # Create missing route information
        route_links = create_route_links(timing_links, stop_points)
        create_routes(journey_patterns, jp_to_jps, jp_sections, timing_links)
        route_to_route_links = create_route_to_route_links(
            journey_patterns, jp_to_jps, timing_links
        )

        line_names = transform_line_names(extracted_data.line_names)

        # Transform route information into service patterns
        service_links = transform_service_links(route_links)
        service_patterns = transform_service_patterns(journey_patterns)
        service_pattern_to_service_links = (
            transform_service_pattern_to_service_links(  # noqa: E501
                service_patterns, route_to_route_links, route_links
            )
        )

        # aggregate stop_sequence and geometry
        service_pattern_stops = transform_service_pattern_stops(
            service_pattern_to_service_links, stop_points
        )
        service_patterns = transform_stop_sequence(
            service_pattern_stops, service_patterns
        )

        ### logic for flexible stop points transformation
        if not flexible_stop_points.empty:
            # 2. extract flexible zone data
            flexible_zone = self.sync_flexible_zone(flexible_stop_points)
            # 3. merge the flexible stop points and flexible zone to get the required geometry
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
            flexible_stop_points_with_geometry = transform_geometry(
                flexible_stop_points_with_geometry
            )

            # creating flexible jp sections and jp to jps mapping
            if not flexible_journey_details.empty:
                # creating flexible timing link
                flexible_timing_links = self.create_flexible_timing_link(
                    flexible_journey_details
                )

                # 7. create flexible service link
                if not flexible_timing_links.empty:
                    flexible_service_links = transform_service_links(
                        flexible_timing_links
                    )
                # 8. create flexible service_patterns and service_patterns_stops
                flexible_service_patterns = pd.DataFrame()
                flexible_service_pattern_stops = pd.DataFrame()
                if not flexible_timing_links.empty:
                    # 1. create service_pattern_id in flexible_timing_links
                    flexible_service_patterns = transform_flexible_service_patterns(
                        flexible_timing_links
                    )

                    flexible_service_pattern_to_service_links = (
                        flexible_service_patterns.reset_index()[
                            [
                                "file_id",
                                "service_pattern_id",
                                "order",
                                "from_stop_atco",
                                "to_stop_atco",
                            ]
                        ].set_index(["file_id", "service_pattern_id", "order"])
                    )

                    flexible_service_pattern_stops = transform_service_pattern_stops(
                        flexible_service_pattern_to_service_links,
                        flexible_stop_points_with_geometry,
                    )

                    flexible_service_patterns = transform_flexible_stop_sequence(
                        flexible_service_pattern_stops, flexible_service_patterns
                    )

                    # merge the required dataframes for standard and flexible
                    service_links = pd.concat([service_links, flexible_service_links])
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

        return TransformedData(
            services=services,
            service_patterns=service_patterns,
            service_pattern_to_service_links=service_pattern_to_service_links,
            service_links=service_links,
            stop_points=stop_points,
            service_pattern_stops=service_pattern_stops,
            # carry forward metadata
            schema_version=extracted_data.schema_version,
            creation_datetime=extracted_data.creation_datetime,
            modification_datetime=extracted_data.modification_datetime,
            import_datetime=extracted_data.import_datetime,
            line_count=extracted_data.line_count,
            line_names=line_names,
            stop_count=len(stop_points),
            most_common_localities=most_common_localities,
            vehicle_journeys=df_merged_vehicle_journeys,
        )

    def create_route_links(self, timing_links, stop_points):
        return create_route_links(timing_links, stop_points)

    def create_routes(self, journey_patterns, jp_to_jps, jp_sections, timing_links):
        return create_routes(journey_patterns, jp_to_jps, jp_sections, timing_links)

    def create_route_to_route_links(self, journey_patterns, jp_to_jps, timing_links):
        return create_route_to_route_links(journey_patterns, jp_to_jps, timing_links)

    def transform_service_links(self, route_links):
        return transform_service_links(self, route_links)

    def transform_line_names(self, line_name_list):
        return transform_line_names(line_name_list)

    def transform_service_patterns(self, journey_patterns):
        return transform_service_patterns(journey_patterns)

    def transform_service_pattern_to_service_links(
        self, service_patterns, route_to_route_links, route_links
    ):
        return transform_service_pattern_to_service_links(
            service_patterns, route_to_route_links, route_links
        )

    def sync_stop_points(self, stop_points, provisional_stops):
        stop_point_cache = self.feed_parser.stop_point_cache

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

    def sync_localities_and_adminareas(self, stop_points):
        return sync_localities_and_adminareas(stop_points)

    def transform_service_pattern_stops(
        self, service_pattern_to_service_links, stop_points
    ):
        return transform_service_pattern_stops(
            service_pattern_to_service_links, stop_points
        )

    @classmethod
    def create_stop_sequence(cls, df: pd.DataFrame):
        return create_stop_sequence(df)

    def transform_stop_sequence(self, service_pattern_stops, service_patterns):
        return transform_stop_sequence(service_pattern_stops, service_patterns)

    @classmethod
    def agg_service_pattern_sequences(cls, df: pd.DataFrame):
        return agg_service_pattern_sequences(df)

    @staticmethod
    def get_most_common_districts(stops: pd.DataFrame):
        return get_most_common_districts(stops)

    @staticmethod
    def get_most_common_localities(stops: pd.DataFrame):
        return get_most_common_localities(stops)

    def sync_flexible_zone(self, flexible_stop_points):
        filtered_stop_points = flexible_stop_points[
            (flexible_stop_points["bus_stop_type"] == "flexible")
            & (~flexible_stop_points["naptan_id"].isna())
        ]
        filtered_stop_points_naptan_id = filtered_stop_points["naptan_id"].tolist()
        flexiblezone_qs = FlexibleZone.objects.filter(
            naptan_stoppoint_id__in=filtered_stop_points_naptan_id
        )
        flexible_zone_df = create_naptan_flexible_zone_df_from_queryset(flexiblezone_qs)
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
            filtered_stop_points_naptan_id.set_index("atco_code", inplace=True)
            return filtered_stop_points_naptan_id
        return pd.DataFrame()

    def create_flexible_timing_link(self, flexible_journey_details, flexible_jp_to_jps):
        def get_stop_sequence(group, jp_section_ref):
            group["order"] = range(len(group))
            group["route_link_ref"] = (
                str(jp_section_ref) + "RL" + (group["order"] + 1).astype(str)
            )
            group["jp_timing_link_id"] = (
                str(jp_section_ref) + "TL" + (group["order"] + 1).astype(str)
            )
            group["from_stop_ref"] = group["atco_code"].shift(0)
            group["to_stop_ref"] = group["atco_code"].shift(-1)
            return group.dropna(subset=["to_stop_ref"])

        if not flexible_journey_details.empty and not flexible_jp_to_jps.empty:
            flexible_jp_to_jps = flexible_jp_to_jps.reset_index()[
                ["journey_pattern_id", "jp_section_ref"]
            ]
            journey_patterns = flexible_journey_details.reset_index().merge(
                flexible_jp_to_jps,
                how="left",
                left_on="journey_pattern_id",
                right_on="journey_pattern_id",
            )
            grouped = journey_patterns.groupby("jp_section_ref")
            flexible_timing_links = pd.concat(
                [
                    get_stop_sequence(group, jp_section_ref)
                    for jp_section_ref, group in grouped
                ]
            )
            flexible_timing_links = (
                flexible_timing_links[
                    [
                        "file_id",
                        "jp_timing_link_id",
                        "route_link_ref",
                        "jp_section_ref",
                        "order",
                        "from_stop_ref",
                        "to_stop_ref",
                    ]
                ]
                .rename(columns={"jp_section_ref": "jp_section_id"})
                .set_index(["file_id", "jp_section_id"])
            )
            return flexible_timing_links
        return pd.DataFrame()

    def create_flexible_jps(self, flexible_journey_details):
        flexible_jps = flexible_journey_details.reset_index()[
            ["file_id", "journey_pattern_id", "service_code"]
        ].drop_duplicates(["file_id", "journey_pattern_id"])
        # generate unique id for flexible journey patterns
        flexible_jps["jp_section_ref"] = [
            uuid.uuid4() for _ in range(len(flexible_jps))
        ]
        flexible_jp_to_jps = flexible_jps[
            ["file_id", "journey_pattern_id", "jp_section_ref"]
        ]
        flexible_jp_to_jps["order"] = range(len(flexible_jp_to_jps))
        flexible_jps = (
            flexible_jps[["file_id", "jp_section_ref"]]
            .rename(columns={"jp_section_ref": "jp_section_id"})
            .set_index(["file_id", "jp_section_id"])
        )
        flexible_jp_to_jps.set_index(
            ["file_id", "journey_pattern_id", "order"], inplace=True
        )
        return flexible_jps, flexible_jp_to_jps
