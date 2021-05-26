import numpy as np
import pandas as pd
from celery.utils.log import get_task_logger

from transit_odp.naptan.models import StopPoint
from transit_odp.pipelines.pipelines.dataset_etl.utils.etl_base import ETLUtility
from transit_odp.pipelines.pipelines.dataset_etl.utils.models import (
    ExtractedData,
    TransformedData,
)

from .utils.dataframes import (
    create_naptan_stoppoint_df,
    create_naptan_stoppoint_df_from_queryset,
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
        provisional_stops = extracted_data.provisional_stops.copy()

        # Match stop_points with DB
        stop_points = self.sync_stop_points(stop_points, provisional_stops)
        stop_points = sync_localities_and_adminareas(stop_points)
        # stop_points = self.sync_admin_areas(stop_points)
        most_common_localities = get_most_common_localities(stop_points)

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
