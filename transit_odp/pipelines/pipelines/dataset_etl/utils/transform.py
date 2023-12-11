import pandas as pd
from celery.utils.log import get_task_logger
from django.contrib.gis.geos import LineString

from transit_odp.naptan.models import Locality

from .dataframes import create_naptan_locality_df

logger = get_task_logger(__name__)


def create_stop_sequence(df: pd.DataFrame):
    df = df.reset_index().sort_values("order")

    stops_atcos = df[["from_stop_atco"]].rename(columns={"from_stop_atco": "stop_atco"})

    last_stop = (
        df[["to_stop_atco"]].iloc[[-1]].rename(columns={"to_stop_atco": "stop_atco"})
    )

    stops_atcos = pd.concat([stops_atcos, last_stop], ignore_index=True)
    stops_atcos.index.name = "order"
    return stops_atcos


def transform_service_pattern_stops(service_pattern_to_service_links:pd.DataFrame, stop_points):
    service_pattern_stops = (
        (
            service_pattern_to_service_links.reset_index()
            .groupby(["file_id", "service_pattern_id"])
            .apply(create_stop_sequence)
        )
        .reset_index()
        .set_index(["file_id", "service_pattern_id", "order"], verify_integrity=True)
    )

    # Merge with stops to have sequence of naptan_id, geometry, etc.
    stop_cols = ["naptan_id", "geometry", "locality_id", "admin_area_id"]
    service_pattern_stops = service_pattern_stops.merge(
        stop_points[stop_cols],
        how="left",
        left_on="stop_atco",
        right_index=True,
    )
    service_pattern_stops = service_pattern_stops.where(
        service_pattern_stops.notnull(), None
    )

    return service_pattern_stops


def agg_service_pattern_sequences(df: pd.DataFrame):
    geometry = None
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


def transform_stop_sequence(service_pattern_stops, service_patterns):
    sequence = (
        service_pattern_stops.reset_index()
        .groupby(["file_id", "service_pattern_id"])
        .apply(agg_service_pattern_sequences)
    )
    service_patterns = service_patterns.join(sequence)
    service_patterns = service_patterns.where(service_patterns.notnull(), None)

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
    route_links = (
        timing_links.reset_index()
        .drop_duplicates(["file_id", "route_link_ref"])
        .set_index(["file_id", "route_link_ref"])
        .loc[:, ["from_stop_ref", "to_stop_ref"]]
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


def create_hash(s: pd.Series):
    """Hash together values in pd.Series"""
    return hash(tuple(s))


def create_route_to_route_links(journey_patterns, jp_to_jps, timing_links):
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
    route_patterns = journey_patterns.reset_index().drop_duplicates(
        ["file_id", "route_hash"]
    )[["file_id", "route_hash", "journey_pattern_id"]]

    route_to_route_links = route_patterns.merge(
        jp_to_jps.reset_index(), how="left", on=["file_id", "journey_pattern_id"]
    ).merge(
        timing_links.reset_index(),
        left_on=["file_id", "jp_section_ref"],
        right_on=["file_id", "jp_section_id"],
        suffixes=["_section", "_link"],
    )

    # Build the new sequence. To get the final ordering of route_link_ref,
    # we sort each group by the two
    # orderings and use 'reset_index' to create a new sequential index in this order
    route_to_route_links = route_to_route_links.groupby(
        ["file_id", "route_hash"]
    ).apply(
        lambda g: g.sort_values(["order_section", "order_link"]).reset_index()[
            ["route_link_ref"]
        ]
    )
    route_to_route_links.index.names = ["file_id", "route_hash", "order"]

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


def transform_service_patterns(journey_patterns):
    # Create list of service patterns from journey patterns
    service_patterns = (
        journey_patterns.reset_index()
        .drop_duplicates(["service_code", "route_hash"])
        .drop("journey_pattern_id", axis=1)
    )

    # Create an id column for service_patterns. Note using the route_hash
    # won't result in the prettiest id
    service_patterns["service_pattern_id"] = service_patterns["service_code"].str.cat(
        service_patterns["route_hash"].astype(str), sep="-"
    )

    service_patterns.set_index(["file_id", "service_pattern_id"], inplace=True)

    return service_patterns


def transform_service_pattern_to_service_links(
    service_patterns, route_to_route_links, route_links
):
    logger.info("Starting transform_service_pattern_to_service_links")
    service_pattern_to_service_links = (
        service_patterns.reset_index()
        .merge(
            route_to_route_links.reset_index(),
            how="left",
            on=["file_id", "route_hash"],
        )
        .merge(
            route_links,
            how="left",
            left_on=["file_id", "route_link_ref"],
            right_index=True,
        )
    )

    # filter and rename columns
    service_pattern_to_service_links = service_pattern_to_service_links[
        ["file_id", "service_pattern_id", "order", "from_stop_atco", "to_stop_atco"]
    ].set_index(["file_id", "service_pattern_id", "order"])

    # no longer need route_hash
    service_patterns.drop("route_hash", axis=1, inplace=True)
    logger.info("Finished transform_service_pattern_to_service_links")
    return service_pattern_to_service_links
