from datetime import datetime
from typing import List

import attr
import pandas as pd


@attr.s(auto_attribs=True)
class ExtractedData(object):
    services: pd.DataFrame
    stop_points: pd.DataFrame
    flexible_stop_points: pd.DataFrame
    provisional_stops: pd.DataFrame
    journey_patterns: pd.DataFrame
    flexible_journey_details: pd.DataFrame
    jp_to_jps: pd.DataFrame
    jp_sections: pd.DataFrame
    timing_links: pd.DataFrame
    booking_arrangements: pd.DataFrame
    vehicle_journeys: pd.DataFrame
    serviced_organisations: pd.DataFrame
    operating_profiles: pd.DataFrame

    routes: pd.DataFrame
    route_to_route_links: pd.DataFrame
    route_links: pd.DataFrame

    schema_version: str
    creation_datetime: datetime
    modification_datetime: datetime
    import_datetime: datetime
    line_count: int
    line_names: List[str]
    stop_count: int
    timing_point_count: int


@attr.s(auto_attribs=True)
class TransformedData(object):
    services: pd.DataFrame
    service_patterns: pd.DataFrame
    service_pattern_to_service_links: pd.DataFrame
    service_links: pd.DataFrame
    stop_points: pd.DataFrame
    service_pattern_stops: pd.DataFrame
    booking_arrangements: pd.DataFrame
    vehicle_journeys: pd.DataFrame
    serviced_organisations: pd.DataFrame

    schema_version: str
    creation_datetime: datetime
    modification_datetime: datetime
    import_datetime: datetime
    line_count: int
    line_names: str
    stop_count: int
    most_common_localities: List[str]
    timing_point_count: int
