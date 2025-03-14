import uuid

import pandas as pd
from celery.utils.log import get_task_logger
from django.contrib.gis.geos import LineString

from transit_odp.naptan.models import Locality

from .dataframes import create_naptan_locality_df

logger = get_task_logger(__name__)


def transform_geometry(df: pd.DataFrame):
    """
    This function fills the empty flexible_location with geometry column and rename
    the column name flexible_location to geometry
    """
    if "flexible_location" in df.columns:
        df["flexible_location"] = df["flexible_location"].fillna(df["geometry"])
    else:
        df["flexible_location"] = df["geometry"]
    df.drop(["geometry"], axis=1, inplace=True)
    df.rename(columns={"flexible_location": "geometry"}, inplace=True)
    return df


def convert_to_time_field(time_delta_value):
    base_datetime = pd.to_datetime("2000-01-01")
    if pd.isna(time_delta_value):
        return "00:00:00"

    time_delta_value = base_datetime + time_delta_value
    return time_delta_value.strftime("%H:%M:%S")


def create_stop_sequence(df: pd.DataFrame) -> pd.DataFrame:
    """Generate sequence of stops ordered as per their sequence for a route.
    Additional fields are included so that these fields can be stored
    into ServicePatternStop model
    """
    original_df = df.copy()
    if "run_time" in df.columns:
        df["run_time"] = df["run_time"].shift(1, fill_value=pd.NaT)
    df = df.reset_index()
    df = df.sort_values("order")
    vehicle_journey_exists = False
    df_columns = df.columns
    last_stop_columns = [
        "to_stop_atco",
        "run_time",
        "wait_time",
        "to_is_timing_status",
        "to_stop_sequence_number",
        "to_activity_id",
    ]

    if "vehicle_journey_code" in df.columns:
        vehicle_journey_exists = True
        last_stop_columns.extend(["journey_pattern_id"])
    else:
        df = df.drop_duplicates(
            subset=[
                "file_id",
                "service_pattern_id",
                "route_link_ref",
                "from_stop_atco",
                "to_stop_atco",
            ]
        )

    departure_time = None

    use_vehicle_journey_runtime = False
    # run_time_vj is set only when run_time is found in VehicleJourney element
    # and hence needs to be conditionally removed to avoid exceptions in dataframes
    columns = [
        "from_stop_atco",
        "from_stop_sequence_number",
        "from_is_timing_status",
        "run_time",
        "wait_time",
        "from_activity_id",
    ]
    columns_to_drop = ["run_time", "wait_time"]
    if "run_time_vj" in df_columns:
        df["run_time_vj"] = df["run_time_vj"].shift(1, fill_value=pd.NaT)
        use_vehicle_journey_runtime = True
        columns.extend(
            [
                "run_time_vj",
                "wait_time_vj",
            ]
        )

        columns_to_drop.extend(
            [
                "run_time_vj",
                "wait_time_vj",
            ]
        )

        last_stop_columns.extend(
            [
                "run_time_vj",
                "wait_time_vj",
            ]
        )

    if vehicle_journey_exists:
        columns.extend(["journey_pattern_id"])

    # Extract all remaining stop to be placed below the principal stop
    stops_atcos = (
        original_df[last_stop_columns]
        .iloc[[-1]]
        .rename(
            columns={
                "to_stop_atco": "stop_atco",
                "to_stop_sequence_number": "sequence_number",
                "to_activity_id": "activity_id",
                "to_is_timing_status": "is_timing_status",
            }
        )
    )

    is_flexible_departure_time = False
    # Departure time for flexible stops is null
    if df["departure_time"].isna().any():
        is_flexible_departure_time = True

    departure_time = df.iloc[0]["departure_time"]

    main_set_stops = df[columns].rename(
        columns={
            "from_stop_atco": "stop_atco",
            "from_stop_sequence_number": "sequence_number",
            "from_activity_id": "activity_id",
            "from_is_timing_status": "is_timing_status",
        }
    )
    last_stop_columns.remove("to_stop_atco")
    last_stop_columns.remove("to_is_timing_status")
    columns.remove("from_stop_atco")
    columns.remove("from_is_timing_status")
    # Calculate departure time for standard stops where run_time is found in VehicleJourney
    if use_vehicle_journey_runtime and not is_flexible_departure_time:
        if not main_set_stops["wait_time_vj"].isnull().all():
            main_set_stops["wait_time"] = main_set_stops["wait_time_vj"].fillna(
                pd.Timedelta(0)
            )
        if not stops_atcos["wait_time_vj"].isnull().all():
            stops_atcos["wait_time"] = stops_atcos["wait_time_vj"].fillna(
                pd.Timedelta(0)
            )

        main_set_stops["departure_time"] = main_set_stops["run_time_vj"].replace(
            "", pd.NaT
        ).combine_first(main_set_stops["run_time"]).fillna(
            pd.Timedelta(0)
        ) + main_set_stops[
            "wait_time"
        ].fillna(
            pd.Timedelta(0)
        )
        stops_atcos["departure_time"] = stops_atcos["run_time_vj"].replace(
            "", pd.NaT
        ).combine_first(stops_atcos["run_time"]).fillna(pd.Timedelta(0)) + stops_atcos[
            "wait_time"
        ].fillna(
            pd.Timedelta(0)
        )
    # Calculate departure time for standard stops where run_time is NOT found in VehicleJourney
    elif not is_flexible_departure_time:
        main_set_stops["departure_time"] = main_set_stops["run_time"].fillna(
            pd.Timedelta(0)
        ) + main_set_stops["wait_time"].fillna(pd.Timedelta(0))

        stops_atcos["departure_time"] = stops_atcos["run_time"].fillna(
            pd.Timedelta(0)
        ) + stops_atcos["wait_time"].fillna(pd.Timedelta(0))
    # Calculate departure time for flexible stops
    else:
        main_set_stops["departure_time"] = None
        stops_atcos["departure_time"] = None

    main_set_stops.drop(columns=columns_to_drop, axis=1, inplace=True)
    stops_atcos = stops_atcos[main_set_stops.columns]
    # stops_atcos = pd.concat([stops_atcos, main_set_stops], ignore_index=True)
    stops_atcos = pd.concat([main_set_stops, stops_atcos], ignore_index=True)
    if not is_flexible_departure_time:
        stops_atcos["departure_time"] = stops_atcos["departure_time"].cumsum()
        stops_atcos["departure_time"] = stops_atcos["departure_time"] + departure_time
        stops_atcos["departure_time"] = stops_atcos["departure_time"].apply(
            convert_to_time_field
        )
    stops_atcos.index.name = "order"
    return stops_atcos


def transform_service_pattern_stops(
    service_pattern_to_service_links: pd.DataFrame,
    stop_points: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create service pattern stops sequence data which is ordered as per
    the stops mapped in journey pattern and journey pattern sections.

    Additionally, adding logic to handle populating 'auto_sequence_number'.
    """
    columns = ["file_id", "service_pattern_id"]
    if "vehicle_journey_code" in service_pattern_to_service_links.columns:
        columns.append("vehicle_journey_code")

    service_pattern_stops = (
        service_pattern_to_service_links.reset_index()
        .groupby(columns)
        .apply(create_stop_sequence)
    ).reset_index()
    # Merge with stops to have sequence of naptan_id, geometry, etc.
    stop_cols = ["naptan_id", "geometry", "locality_id", "admin_area_id", "common_name"]
    service_pattern_stops = service_pattern_stops.merge(
        stop_points[stop_cols],
        how="left",
        left_on="stop_atco",
        right_index=True,
    )
    service_pattern_stops = service_pattern_stops.where(
        service_pattern_stops.notnull(), None
    )

    columns = service_pattern_stops.drop(columns=["geometry"]).columns.to_list()
    service_pattern_stops = service_pattern_stops.drop_duplicates(subset=columns)
    service_pattern_stops.set_index(
        ["file_id"], append=True, verify_integrity=True, inplace=True
    )

    if "vehicle_journey_code" in service_pattern_stops.columns:
        service_pattern_stops["auto_sequence_number"] = service_pattern_stops.groupby(
            ["file_id", "vehicle_journey_code", "service_pattern_id"]
        ).cumcount()

    return service_pattern_stops


def agg_service_pattern_sequences(df: pd.DataFrame):
    geometry = None
    df = df.drop_duplicates(subset=["stop_atco"]).sort_values(
        by="sequence_number", key=pd.to_numeric
    )
    points = df["geometry"].values
    if len(list(point for point in points if point)) > 1:
        geometry = LineString(
            [[point.x, point.y] for point in points if point and pd.notna(point)]
        )

    return pd.Series(
        {
            "geometry": geometry,
            "localities": df["locality_id"].to_list(),
            "admin_area_codes": df["admin_area_id"].to_list(),
        }
    )


def agg_flexible_service_pattern_sequences(df: pd.DataFrame):
    """
    This function converts each shapely.geometry Point to list of points
    and create a LineString object from list of points
    """

    def flatten_list(nested_list):
        flattened_list = []
        for item in nested_list:
            if isinstance(item, list):
                flattened_list.extend(flatten_list(item))
            else:
                flattened_list.append(item)
        return flattened_list

    agg_points = df["geometry"].values
    agg_point_list = flatten_list(agg_points)
    geometry_points = []

    for point in agg_point_list:
        if point and pd.notna(point):
            geometry_points.append([point.x, point.y])
    geometry = LineString(geometry_points) if geometry_points else None
    return pd.Series(
        {
            "geometry": geometry,
            "localities": df["locality_id"].to_list(),
            "admin_area_codes": df["admin_area_id"].to_list(),
        }
    )


def transform_stop_sequence(service_pattern_stops, service_patterns):
    sequence = (
        service_pattern_stops.reset_index()
        .groupby(["file_id", "service_pattern_id"])
        .apply(agg_service_pattern_sequences)
    )
    service_patterns = service_patterns.join(sequence)
    service_patterns = service_patterns.where(service_patterns.notnull(), None)

    return service_patterns


def transform_flexible_stop_sequence(service_pattern_stops, service_patterns):
    """
    This function returns the linestring objects for each service pattern id
    """
    sequence = (
        service_pattern_stops.reset_index()
        .groupby(["file_id", "service_pattern_id"])
        .apply(agg_flexible_service_pattern_sequences)
    )
    service_patterns = service_patterns.join(sequence)
    service_patterns = service_patterns.where(service_patterns.notnull(), None)
    service_patterns.reset_index(inplace=True)
    service_patterns.drop_duplicates(["file_id", "service_pattern_id"], inplace=True)
    service_patterns.set_index(["file_id", "service_pattern_id", "order"], inplace=True)
    return service_patterns


def get_most_common_districts(stops: pd.DataFrame):
    """Returns top 5 most common district names for stops"""
    stops["district_name"] = stops["district_name"].replace(
        {"": "unknown", "None": "unknown", None: "unknown"}
    )
    count = stops["district_name"].value_counts()
    # Replace empty district name with "unknown"
    # count = count.rename({"": "unknown", "None": "unknown", None: "unknown"})
    # count = count.rename({"None": "unknown"})
    # Put unknown at the end of the list in case its singular. ie
    # this ["unknown"]. To protect against the unlikely event
    # that we have two lines with every district having an empty name
    return list(count.head().index) + ["unknown"]


def get_most_common_localities(stops: pd.DataFrame):
    """Returns top 5 most common localities names for stops"""
    stops["locality_name"] = stops["locality_name"].replace(
        {"": "unknown", "None": "unknown", None: "unknown"}
    )
    # Put unknown at the end of the list in case its singular. ie
    # this ["unknown"]. To protect against the unlikely event
    # that we have two lines with every district having an empty name
    count = stops["locality_name"].value_counts()
    count = count.sort_index(ascending=False).sort_values(
        ascending=False, kind="mergesort"
    )
    return list(count.head().index) + ["unknown"]


def sync_localities_and_adminareas(stop_points):
    locality_set = set(
        [
            locality if locality != "" else None
            for locality in stop_points["locality_id"].to_list()
        ]
    )

    if len(locality_set) != 0:
        qs = Locality.objects.filter(gazetteer_id__in=locality_set)

        fetched = create_naptan_locality_df(
            data=(
                {
                    "locality_name": obj.name,
                    "locality_id": obj.gazetteer_id,
                    "admin_area_id": obj.admin_area_id,
                }
                for obj in qs
            )
        )

        stop_points = stop_points.merge(
            fetched, how="left", left_on="locality_id", right_index=True
        )

    return stop_points


def create_route_links(timing_links, stop_points):
    """Reduce timing_links into route_links."""
    columns = timing_links.columns
    if "run_time" in columns:
        columns = [
            "file_id",
            "route_link_ref",
            "jp_section_id",
            "from_stop_ref",
            "to_stop_ref",
            "from_is_timing_status",
            "to_is_timing_status",
            "run_time",
            "wait_time",
        ]
    else:
        columns = [
            "file_id",
            "route_link_ref",
            "jp_section_id",
            "from_stop_ref",
            "to_stop_ref",
        ]

    route_links = (
        timing_links.reset_index()
        .drop_duplicates(["file_id", "route_link_ref", "jp_section_id"])
        .loc[:, columns]
        .set_index(["file_id", "route_link_ref", "jp_section_id"])
        .rename(
            columns={"from_stop_ref": "from_stop_atco", "to_stop_ref": "to_stop_atco"}
        )
    )

    # Note route_links are not unique (from_stop_ref, to_stop_ref) pairs,
    # get list of unique pairs
    return route_links


def create_routes(journey_patterns, jp_to_jps, jp_sections, timing_links):
    jp_sections["route_section_hash"] = timing_links.groupby(
        ["file_id", "jp_section_id"]
    )["route_link_ref"].apply(create_hash)

    # Calculate the 'route_hash' of the journey_pattern - this identifies
    # the Route of the JourneyPattern
    journey_patterns["route_hash"] = (
        jp_to_jps.reset_index()
        .merge(jp_sections, left_on=["file_id", "jp_section_ref"], right_index=True)
        .groupby(["file_id", "journey_pattern_id"])
        .apply(lambda df: create_hash(df.sort_values("order")["route_section_hash"]))
    )
    # Create Routes from journey_patterns with unique route_hash
    routes = (
        journey_patterns.reset_index()[["file_id", "route_hash"]]
        .drop_duplicates(["file_id", "route_hash"])
        .set_index(["file_id", "route_hash"])
    )

    if routes.empty:
        return pd.DataFrame()

    return routes


def create_flexible_routes(flexible_journey_patterns):
    """
    This function create a unique identifier for each journey pattern
    """
    df = flexible_journey_patterns.reset_index()
    grouped_df = (
        df.groupby(["file_id", "journey_pattern_id"])
        .apply(lambda x: pd.Series({"route_hash": uuid.uuid4()}))
        .reset_index()
    )
    merged_df = pd.merge(
        df, grouped_df, on=["file_id", "journey_pattern_id"], how="left"
    )
    merged_df.set_index(["file_id", "journey_pattern_id"], inplace=True)
    return merged_df


def create_hash(s: pd.Series):
    """Hash together values in pd.Series"""
    return hash(tuple(s))


def create_route_to_route_links(
    journey_patterns: pd.DataFrame,
    jp_to_jps: pd.DataFrame,
    timing_links: pd.DataFrame,
    vehicle_journeys_with_timing_refs: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge timing_links with jp_to_jps to get timing links for each journey
    pattern, Note 'order' column appears in both jp_to_jps and timing_links,
    so suffixes are used to distinguish them.
    """
    # TODO - this could be optimised, there is no need to generate timing link
    # sequence for every journey pattern
    #  to get the route_link sequences. We can drop the journey_patterns
    # we don't need

    # get journey_patterns with unique routes
    columns = ["file_id", "route_hash", "journey_pattern_id"]
    route_columns = ["file_id", "route_hash"]
    if "vehicle_journey_code" in journey_patterns.columns:
        columns.append("vehicle_journey_code")
        route_columns.append("vehicle_journey_code")

    route_patterns = journey_patterns.reset_index().drop_duplicates(route_columns)[
        columns
    ]

    route_to_route_links = route_patterns.merge(
        jp_to_jps.reset_index(), how="left", on=["file_id", "journey_pattern_id"]
    ).merge(
        timing_links.reset_index(),
        left_on=["file_id", "jp_section_ref"],
        right_on=["file_id", "jp_section_id"],
        suffixes=["_section", "_link"],
    )

    r2r_links_columns = [
        "jp_section_id",
        "route_link_ref",
        "from_stop_sequence_number",
        "to_stop_sequence_number",
        "from_activity_id",
        "to_activity_id",
    ]

    if not vehicle_journeys_with_timing_refs.empty:
        route_to_route_links = route_to_route_links.merge(
            vehicle_journeys_with_timing_refs.reset_index(),
            left_on=[
                "file_id",
                "journey_pattern_id",
                "vehicle_journey_code",
                "jp_timing_link_id",
            ],
            right_on=[
                "file_id",
                "journey_pattern_id",
                "vehicle_journey_code",
                "timing_link_ref",
            ],
            how="left",
            suffixes=["_rl", "_vj"],
        )
        r2r_links_columns.extend(["run_time_vj", "wait_time_vj"])

    route_to_route_links = route_to_route_links.groupby(route_columns).apply(
        lambda g: g.sort_values(["order_section", "order_link"]).reset_index()[
            r2r_links_columns
        ]
    )

    route_columns.append("order")
    route_to_route_links.index.names = route_columns

    return route_to_route_links


def transform_service_links(route_links):
    service_links = (
        route_links.reset_index()[["from_stop_atco", "to_stop_atco"]]
        .drop_duplicates(["from_stop_atco", "to_stop_atco"])
        .reset_index()
        .set_index(["from_stop_atco", "to_stop_atco"])
    )
    return service_links


def transform_line_names(line_name_list):
    if line_name_list:
        line_names = ",".join(key for key in line_name_list)
        return line_names


def get_vehicle_journey_without_timing_refs(vehicle_journeys):
    df_subset = vehicle_journeys[
        vehicle_journeys.columns.difference(
            ["timing_link_ref", "run_time", "wait_time"]
        )
    ]
    indexes = df_subset.index.names
    df_subset = df_subset.reset_index().drop_duplicates()
    df_subset = df_subset.drop(["service_code"], axis=1)
    return df_subset.set_index(indexes)


def filter_profiles_on_vehicle_journeys(
    operating_profiles: pd.DataFrame,
) -> pd.DataFrame:
    default_profiles = operating_profiles.reset_index().drop_duplicates("day_of_week")
    filtered_df = operating_profiles[
        (
            (operating_profiles["exceptions_date"].isna())
            | (
                (
                    operating_profiles["start_date"]
                    <= operating_profiles["compare_exceptions_date"]
                )
                & (
                    operating_profiles["end_date"]
                    >= operating_profiles["compare_exceptions_date"]
                )
            )
        )
    ]

    if not filtered_df.empty:
        return filtered_df

    return default_profiles


def filter_operating_profiles(
    operating_profiles: pd.DataFrame, services: pd.DataFrame
) -> pd.DataFrame:
    """Remove records from operating profiles where the date falls outside
    operating period start and end date
    """

    df_services = services.copy()

    df_services["end_date"] = df_services["end_date"].fillna(
        pd.Timestamp.max.tz_localize(None)
        .tz_localize("UTC")
        .tz_convert("Europe/London")
    )

    df_services["start_date"] = pd.to_datetime(
        df_services["start_date"]
    ).dt.tz_localize(None)
    df_services["end_date"] = pd.to_datetime(df_services["end_date"]).dt.tz_localize(
        None
    )

    if not operating_profiles.empty and not df_services.empty:
        service_columns = ["file_id", "service_code", "start_date", "end_date"]
        indexes = operating_profiles.index.names
        df_merged = pd.merge(
            operating_profiles.reset_index(),
            df_services.reset_index()[service_columns],
            left_on=["file_id", "service_code"],
            right_on=["file_id", "service_code"],
        )

        df_merged["compare_exceptions_date"] = pd.to_datetime(
            df_merged["exceptions_date"]
        )

        filtered_df = df_merged.groupby(
            ["file_id", "vehicle_journey_code", "serviced_org_ref"], dropna=False
        ).apply(filter_profiles_on_vehicle_journeys)
        filtered_df = filtered_df.drop(
            ["start_date", "end_date", "compare_exceptions_date"], axis=1
        ).set_index(indexes)
        return filtered_df
    return operating_profiles


def get_vehicle_journey_with_timing_refs(
    vehicle_journeys: pd.DataFrame,
) -> pd.DataFrame:
    """Get unique vehicle journeys with timing link elements"""
    df_subset = vehicle_journeys.loc[
        :,
        [
            "journey_pattern_ref",
            "service_code",
            "timing_link_ref",
            "run_time",
            "wait_time",
            "vehicle_journey_code",
        ],
    ]
    df_subset = df_subset.rename(
        columns={"journey_pattern_ref": "journey_pattern_id"}
    ).drop(["service_code"], axis=1)
    indexes = df_subset.index.names
    df_subset = df_subset[df_subset["timing_link_ref"].notna()].reset_index()
    df_subset = df_subset.drop_duplicates()
    return df_subset.set_index(indexes)


def merge_flexible_jp_with_vehicle_journey(
    vehicle_journeys: pd.DataFrame, journey_patterns: pd.DataFrame
) -> pd.DataFrame:
    """Map vehicle journey code to journey patterns to map vehicle journey codes to its stops, mainly intended for many to one relation ship between vehicle journeys and journey patterns"""
    columns = journey_patterns.columns.to_list()
    columns.extend(journey_patterns.index.names)
    columns.append("vehicle_journey_code")
    df_merged = pd.merge(
        journey_patterns.reset_index(),
        vehicle_journeys,
        right_on=["file_id", "journey_pattern_ref"],
        left_on=["file_id", "journey_pattern_id"],
        how="left",
        suffixes=("_jp", "_vj"),
    )

    if "route_hash" in df_merged.columns:
        df_merged["service_pattern_id"] = df_merged["service_code"].str.cat(
            df_merged["route_hash"].astype(str), sep="-"
        )

    return df_merged[columns]


def merge_vehicle_journeys_with_jp(vehicle_journeys, journey_patterns):
    df_merged = pd.merge(
        vehicle_journeys,
        journey_patterns,
        left_on=["file_id", "journey_pattern_ref"],
        right_index=True,
        how="left",
        suffixes=("_vj", "_jp"),
    )

    if "route_hash" in df_merged.columns:
        df_merged["service_pattern_id"] = df_merged["service_code"].str.cat(
            df_merged["route_hash"].astype(str), sep="-"
        )

    return df_merged


def merge_journey_pattern_with_vj_for_departure_time(
    vehicle_journeys: pd.DataFrame,
    journey_patterns: pd.DataFrame,
    timetable_visualiser_active: bool = False,
):
    """
    Merge journey patterns with vehicle journeys based on departure time.

    Parameters:
    - vehicle_journeys: DataFrame containing vehicle journey data.
    - journey_patterns: DataFrame containing journey pattern data.
    - timetable_visualiser_active (bool): Flag indicating if timetable visualizer is active.

    Returns:
    - DataFrame: Merged DataFrame containing journey pattern and vehicle journey data.

    Note:
    - DataFrames are expected to have columns 'file_id', 'journey_pattern_id', and 'departure_time'.
    - If `timetable_visualiser_active` is True, additional columns 'line_name', 'outbound_description', and 'inbound_description' are expected.
    """
    index = journey_patterns.index
    columns_to_merge = [
        "file_id",
        "journey_pattern_ref",
        "departure_time",
        "journey_code",
    ]
    if timetable_visualiser_active:
        columns_to_merge.extend(
            [
                "line_name",
                "outbound_description",
                "inbound_description",
                "vehicle_journey_code",
            ]
        )

    df_merged = pd.merge(
        journey_patterns.reset_index(),
        vehicle_journeys[columns_to_merge],
        left_on=["file_id", "journey_pattern_id"],
        right_on=["file_id", "journey_pattern_ref"],
        how="left",
        suffixes=("_vj", "_jp"),
    )
    df_merged = df_merged.drop(columns=["journey_pattern_ref"], axis=1)
    df_merged.set_index(index.names, inplace=True)
    df_merged.dropna(subset=["departure_time", "line_name"], how="all", inplace=True)
    return df_merged


def merge_serviced_organisations_with_operating_profile(
    serviced_organisations, operating_profiles
):
    serviced_organisations.reset_index(inplace=True)
    serviced_organisations.drop_duplicates(inplace=True)
    df_merged = pd.merge(
        serviced_organisations,
        operating_profiles,
        on=["serviced_org_ref", "file_id"],
        how="inner",
    )
    df_merged = df_merged[
        ["file_id", "serviced_org_ref", "name", "operational", "start_date", "end_date"]
    ]
    df_merged.drop_duplicates(inplace=True)
    df_merged["operational"] = df_merged["operational"].astype(bool)
    df_merged.set_index("file_id", inplace=True)

    return df_merged


def merge_lines_with_vehicle_journey(vehicle_journeys, lines):
    """
    Merge vehicle journeys with lines.
    Note:
    - DataFrames are expected to have columns 'file_id' and 'line_ref'.
    """
    df_merged = pd.merge(
        vehicle_journeys,
        lines,
        left_on=["file_id", "line_ref"],
        right_on=["file_id", "line_id"],
        how="inner",
    )
    return df_merged


def transform_service_patterns(
    journey_patterns: pd.DataFrame, drop_duplicates_columns: list
) -> pd.DataFrame:
    """
    Transform journey patterns into service patterns.
    Note:
    - DataFrame is expected to have columns 'route_hash', 'service_code', and 'file_id'.
    - Route hash at the time of this comment was null for flexible services
    - The 'route_hash' column should not contain NaN values.
    - The 'service_pattern_id' is created by concatenating 'service_code' and 'route_hash'.
    """
    service_patterns = journey_patterns.reset_index()

    service_patterns.dropna(subset=["route_hash"], inplace=True)
    service_patterns["service_pattern_id"] = service_patterns["service_code"].str.cat(
        service_patterns["route_hash"].astype(str), sep="-"
    )
    drop_columns_with_departure_time = drop_duplicates_columns.copy().append(
        "departure_time"
    )
    service_patterns = service_patterns.drop_duplicates(
        subset=drop_columns_with_departure_time
    )
    service_patterns.set_index(["file_id", "service_pattern_id"], inplace=True)

    return service_patterns


def transform_service_pattern_to_service_links(
    service_patterns: pd.DataFrame,
    route_to_route_links: pd.DataFrame,
    route_links: pd.DataFrame,
) -> pd.DataFrame:
    """Map route link references to journey patterns which is then used to map the stops to journeys based on route link refs"""
    logger.info("Starting transform_service_pattern_to_service_links")
    r2r_links_merge_on = ["file_id", "route_hash"]
    if "vehicle_journey_code" in route_to_route_links.index.names:
        r2r_links_merge_on.append("vehicle_journey_code")

    service_pattern_to_service_links = (
        service_patterns.reset_index()
        .merge(
            route_to_route_links.reset_index(),
            how="left",
            on=r2r_links_merge_on,
        )
        .merge(
            route_links,
            how="left",
            left_on=["file_id", "route_link_ref", "jp_section_id"],
            right_index=True,
        )
    )

    df_link_columns = service_pattern_to_service_links.columns
    if "departure_time" not in df_link_columns:
        service_pattern_to_service_links = service_pattern_to_service_links.set_index(
            ["file_id", "service_pattern_id", "order"]
        )
        service_pattern_to_service_links["departure_time"] = None
        service_pattern_to_service_links["from_is_timing_status"] = False
        service_pattern_to_service_links["to_is_timing_status"] = False
        service_pattern_to_service_links["run_time"] = pd.NaT
        service_pattern_to_service_links["wait_time"] = pd.NaT
        return service_pattern_to_service_links, []

    drop_columns = [
        "departure_time",
        "from_is_timing_status",
        "to_is_timing_status",
        "run_time",
        "wait_time",
    ]

    # subset of columns from df_link_columns
    link_columns = [
        "file_id",
        "service_pattern_id",
        "journey_pattern_id",
        "vehicle_journey_code",
        "journey_code",
        "order",
        "from_stop_atco",
        "to_stop_atco",
        "from_stop_sequence_number",
        "from_activity_id",
        "to_stop_sequence_number",
        "to_activity_id",
        "departure_time",
        "from_is_timing_status",
        "to_is_timing_status",
        "run_time",
        "wait_time",
    ]

    if "run_time_vj" in df_link_columns:
        link_columns.extend(["run_time_vj", "wait_time_vj"])
        drop_columns.extend(["run_time_vj", "wait_time_vj"])

    # filter and rename columns
    service_pattern_to_service_links = service_pattern_to_service_links[link_columns]
    service_pattern_to_service_links = (
        service_pattern_to_service_links.drop_duplicates()
    )

    logger.info("Finished transform_service_pattern_to_service_links")
    return service_pattern_to_service_links, drop_columns


def transform_flexible_service_pattern_to_service_links(flexible_service_patterns):
    """
    this function creates a set of columns departure_time, departure_time, run_time, wait_time
    with default values for flexible stops
    """
    logger.info("Starting transform_flexible_service_pattern_to_service_links")
    drop_columns = [
        "departure_time",
        "from_is_timing_status",
        "to_is_timing_status",
        "run_time",
        "wait_time",
    ]
    service_pattern_to_service_links = flexible_service_patterns.reset_index()
    service_pattern_to_service_links["departure_time"] = None
    service_pattern_to_service_links["from_is_timing_status"] = False
    service_pattern_to_service_links["to_is_timing_status"] = False
    service_pattern_to_service_links["run_time"] = pd.NaT
    service_pattern_to_service_links["wait_time"] = pd.NaT
    service_pattern_to_service_links[
        "from_stop_sequence_number"
    ] = service_pattern_to_service_links["order"]
    service_pattern_to_service_links["to_stop_sequence_number"] = (
        service_pattern_to_service_links["order"] + 1
    )
    service_pattern_to_service_links = service_pattern_to_service_links.set_index(
        ["file_id", "service_pattern_id", "order"]
    )
    return service_pattern_to_service_links, drop_columns


def transform_flexible_service_patterns(
    flexible_timing_links: pd.DataFrame,
) -> pd.DataFrame:
    """
    This function creates a column service_pattern_id which is a combination of
    service_pattern_id and service_code
    """
    flexible_service_patterns = flexible_timing_links.reset_index()
    flexible_service_patterns["service_pattern_id"] = flexible_service_patterns[
        "service_code"
    ].str.cat(flexible_service_patterns["route_hash"].astype(str), sep="-")
    flexible_service_patterns = flexible_service_patterns[
        [
            "file_id",
            "service_pattern_id",
            "order",
            "service_code",
            "from_stop_atco",
            "from_activity_id",
            "to_stop_atco",
            "to_activity_id",
            "vehicle_journey_code",
            "journey_pattern_id",
        ]
    ]
    flexible_service_patterns.set_index(
        ["file_id", "service_pattern_id", "order"], inplace=True
    )
    return flexible_service_patterns


def merge_flexible_jd_with_jp(
    flexible_journey_details: pd.DataFrame, flexible_journey_patterns: pd.DataFrame
) -> pd.DataFrame:
    """
    This function merge the flexible_journey_details and flexible_journey_patterns
    so the resulting dataframe will have the route_hash column
    """
    journey_details = flexible_journey_details.reset_index()
    journey_patterns = flexible_journey_patterns[
        ["file_id", "journey_pattern_id", "route_hash", "vehicle_journey_code"]
    ]
    journey_details = journey_details.merge(
        journey_patterns, how="left", on=["file_id", "journey_pattern_id"]
    )
    return journey_details


def transform_geometry_tracks(df):
    """
    Transforming geometry point lest to LinsString
    """
    if not df.empty and "geometry" in df.columns:
        df["geometry"] = df["geometry"].apply(
            lambda points: LineString(
                [(float(long), float(lat)) for long, lat in points]
            )
        )
    return df
