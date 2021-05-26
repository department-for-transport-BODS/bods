import attr
import geopandas as gpd
import pandas as pd

from transit_odp.data_quality.models import DataQualityReport


@attr.s(auto_attribs=True)
class ExtractedWarnings(object):
    service_link_missing_stops: pd.DataFrame
    timing_missing_point_15: pd.DataFrame
    timing_multiple: pd.DataFrame
    timing_first: pd.DataFrame
    timing_last: pd.DataFrame
    timing_fast_link: pd.DataFrame
    timing_fast: pd.DataFrame
    timing_slow: pd.DataFrame
    timing_slow_link: pd.DataFrame
    timing_backwards: pd.DataFrame
    timing_pick_up: pd.DataFrame
    timing_drop_off: pd.DataFrame
    journeys_without_headsign: pd.DataFrame
    journey_duplicate: pd.DataFrame
    journey_conflict: pd.DataFrame
    journey_date_range_backwards: pd.DataFrame
    stop_missing_naptan: pd.DataFrame
    journey_stop_inappropriate: pd.DataFrame
    stop_incorrect_type: pd.DataFrame


@attr.s(auto_attribs=True)
class ExtractedModel(object):
    stops: gpd.GeoDataFrame
    lines: pd.DataFrame
    service_patterns: gpd.GeoDataFrame
    service_links: gpd.GeoDataFrame
    timing_patterns: pd.DataFrame
    vehicle_journeys: pd.DataFrame


@attr.s(auto_attribs=True)
class ExtractedData(object):
    report: DataQualityReport
    warnings: ExtractedWarnings
    model: ExtractedModel


@attr.s(auto_attribs=True)
class TransformedModel(object):
    stops: gpd.GeoDataFrame
    lines: pd.DataFrame
    service_patterns: gpd.GeoDataFrame
    service_pattern_stops: pd.DataFrame
    service_pattern_service_links: pd.DataFrame
    service_links: gpd.GeoDataFrame
    timing_patterns: pd.DataFrame
    timing_pattern_stops: pd.DataFrame
    vehicle_journeys: pd.DataFrame
