import datetime
import logging
from itertools import chain
from typing import Iterable, List

import geopandas as gpd
import pandas as pd
from django.contrib.gis.geos import LineString, Point

from transit_odp.data_quality.models import (
    DataQualityReport,
    Service,
    ServiceLink,
    ServicePattern,
    ServicePatternServiceLink,
    ServicePatternStop,
    StopPoint,
    TimingPattern,
    TimingPatternStop,
    VehicleJourney,
)
from transit_odp.pipelines.pipelines.dqs_report_etl.models import (
    ExtractedData,
    TransformedModel,
)

logger = logging.getLogger(__name__)


def run(extracted: ExtractedData) -> TransformedModel:
    report = extracted.report

    logger.info("Transforming model")

    # create a copy of each DF
    stops = extracted.model.stops.copy()
    services = extracted.model.lines.copy()
    service_links = extracted.model.service_links.copy()
    service_patterns = extracted.model.service_patterns.copy()
    timing_patterns = extracted.model.timing_patterns.copy()
    vehicle_journeys = extracted.model.vehicle_journeys.copy()

    # transform data
    stops = transform_stops(stops)
    services = transform_lines(report, services)
    service_links = transform_service_links(service_links, stops)
    service_patterns = transform_service_patterns(services, service_patterns)
    service_pattern_stops = transform_service_pattern_stops(service_patterns, stops)
    service_pattern_service_links = transform_service_pattern_service_links(
        service_patterns, service_links
    )
    timing_patterns = transform_timing_patterns(service_patterns, timing_patterns)
    timing_pattern_stops = transform_timing_pattern_stops(
        timing_patterns, service_pattern_stops
    )
    vehicle_journeys = transform_vehicle_journeys(vehicle_journeys, timing_patterns)

    return TransformedModel(
        stops=stops,
        lines=services,
        service_patterns=service_patterns,
        service_links=service_links,
        service_pattern_stops=service_pattern_stops,
        service_pattern_service_links=service_pattern_service_links,
        timing_patterns=timing_patterns,
        timing_pattern_stops=timing_pattern_stops,
        vehicle_journeys=vehicle_journeys,
    )


def transform_stops(stops: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Does a set intersection/diff of stops and StopPoint table in order to get
    internal ID of each stop. This method also creates new StopPoints for any new stops.
    """

    if len(stops) == 0:
        # Pandas doesn't play well where the is no data
        return

    # Create set of stop 'ito_ids'' to fetch from StopPoint table
    fetch_stops = set(stops.index)

    # Find intersection and difference of stops referenced in report
    # to what is in the DB
    qs = StopPoint.objects.filter(ito_id__in=fetch_stops)

    # Create set of ito_ids returned from the DB
    fetched = {item.ito_id for item in qs}

    # Create missing
    missing_stops = fetch_stops - fetched
    created = bulk_create_stoppoints(stops.loc[list(missing_stops)])

    # Create StopPoints and return id to ito_id
    id_map = create_id_map(chain(qs, created))

    # Join StopPoint id onto stops df
    stops = stops.join(id_map)

    return stops


def transform_lines(report: DataQualityReport, lines: pd.DataFrame) -> pd.DataFrame:

    if len(lines) == 0:
        # Pandas doesn't play well where the is no data
        return lines

    # Fetch services
    fetch = set(lines.index)
    qs = Service.objects.filter(ito_id__in=fetch)

    # Create set of ito_ids returned from the DB
    fetched = {item.ito_id for item in qs}

    # Create missing
    missing = fetch - fetched
    created = bulk_create_services(lines.loc[list(missing)])

    # Create ServiceLinks and return id to ito_id
    ito_id_to_id = create_id_map(chain(qs, created))

    # Associate all services with report
    add_services_to_report(report, list(ito_id_to_id["id"]))

    # Join service_ids onto lines df
    lines = lines.join(ito_id_to_id)

    return lines


def transform_service_patterns(
    services: pd.DataFrame, service_patterns: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """
    Creates Service objects in DB. Returns service_patterns DataFrame with DB id column.

    Associate service pattern with Service and set of StopPoints
    :return:
    """
    if len(service_patterns) == 0:
        # Pandas doesn't play well where the is no data
        return service_patterns

    # Join service ids onto service_patterns
    service_ids = services["id"].rename("service_id")
    service_patterns = (
        service_patterns.reset_index()
        .merge(service_ids, how="left", left_on="line", right_index=True)
        .set_index(service_patterns.index.name)
    )

    # Fetch SPs
    fetch = set(service_patterns.index)
    qs = ServicePattern.objects.filter(ito_id__in=fetch)

    # Create set of ito_ids returned from the DB
    fetched = {item.ito_id for item in qs}

    # Create missing
    missing = fetch - fetched
    created = bulk_create_service_patterns(service_patterns.loc[list(missing)])

    # Create ServiceLinks and return id to ito_id
    id_map = create_id_map(chain(qs, created))

    # Join DB ids onto service_patterns
    service_patterns = service_patterns.join(id_map)

    return service_patterns


def transform_service_pattern_stops(
    service_patterns: gpd.GeoDataFrame,
    stops: gpd.GeoDataFrame,
):
    if len(service_patterns) == 0:
        # Pandas doesn't play well where the is no data
        return

    # Create service_pattern_stops DataFrame
    # here we are 'unpacking' the lists within the stops column.
    # Using groupby allows DFs to be assembled as a multiindex.
    service_pattern_stops = (
        service_patterns.reset_index()[["id", "stops"]].groupby("id")
        # Note since groupby/apply works with DFs, we select stops from the first
        # row (there should only be one row)
        .apply(lambda df: pd.DataFrame(df["stops"].iloc[0], columns=["stop_ito_id"]))
    )

    # rename multiindex
    service_pattern_stops.index = service_pattern_stops.index.rename(
        ["service_pattern_id", "position"]
    )

    # Merge stop DB id onto SPS
    service_pattern_stops = (
        service_pattern_stops.reset_index().merge(
            stops["id"].rename("stop_id"),
            how="left",
            left_on="stop_ito_id",
            right_index=True,
        )
        # setting back to multiindex
        .set_index(service_pattern_stops.index.names)
    )

    # Fetch existing SPS - note we grab everything for each SP
    fetch = set(service_patterns.index)
    qs = (
        ServicePatternStop.objects.order_by("service_pattern", "position")
        .select_related("stop")
        .select_related("service_pattern")
        .filter(service_pattern__ito_id__in=fetch)
    )

    # Create set of ito_ids returned from the DB
    fetched = {item.service_pattern.ito_id for item in qs}

    # Create missing - note we're really just handling SPs without any stops
    # associations
    # If these associations have been created previously, we can skip those SPs.
    missing = fetch - fetched

    # missing above is expressed in 'ito_ids', convert to known SP ids
    missing_sp_ids = service_patterns.loc[list(missing), "id"]

    # note we are doing a 'partial' select on the first level of the multiindex
    created = bulk_create_service_pattern_stops(
        service_pattern_stops.loc[list(missing_sp_ids)]
    )

    # Create map of SPS DB ids
    id_map = pd.DataFrame(
        (obj.id for obj in chain(qs, created)),
        index=pd.MultiIndex.from_tuples(
            ((obj.service_pattern_id, obj.position) for obj in chain(qs, created)),
            names=["service_pattern_id", "position"],
        ),
        columns=["id"],
    )

    # Join DB ids onto service_patterns
    service_pattern_stops = service_pattern_stops.join(id_map)

    return service_pattern_stops


def transform_service_pattern_service_links(
    service_patterns: gpd.GeoDataFrame,
    service_links: gpd.GeoDataFrame,
):
    if len(service_patterns) == 0:
        # Pandas doesn't play well where the is no data
        return

    # Create service_pattern_service_links DataFrame
    # here we are 'unpacking' the lists within the service_links column. Using
    # groupby allows DFs to be
    # assembled as a multiindex.
    service_pattern_service_links = (
        service_patterns.reset_index()[["id", "service_links"]].groupby("id")
        # Note since groupby/apply works with DFs, we select service_links from the
        # first row (there should only be one row)
        .apply(
            lambda df: pd.DataFrame(
                df["service_links"].iloc[0], columns=["service_link_ito_id"]
            )
        )
    )

    # rename multiindex
    service_pattern_service_links.index = service_pattern_service_links.index.rename(
        ["service_pattern_id", "position"]
    )

    # Merge service_link DB id onto SPS
    service_pattern_service_links = (
        service_pattern_service_links.reset_index().merge(
            service_links["id"].rename("service_link_id"),
            how="left",
            left_on="service_link_ito_id",
            right_index=True,
        )
        # setting back to multiindex
        .set_index(service_pattern_service_links.index.names)
    )

    # Fetch existing SPS - note we grab everything for each SP
    fetch = set(service_patterns.index)
    qs = (
        ServicePatternServiceLink.objects.order_by("service_pattern", "position")
        .select_related("service_link")
        .select_related("service_pattern")
        .filter(service_pattern__ito_id__in=fetch)
    )

    # Create set of ito_ids returned from the DB
    fetched = {item.service_pattern.ito_id for item in qs}

    # Create missing - note we're really just handling SPs without any service_links
    # associations
    # If these associations have been created previously, we can skip those SPs.
    missing = fetch - fetched

    # missing above is expressed in 'ito_ids', convert to known SP ids
    missing_sp_ids = service_patterns.loc[list(missing), "id"]

    # note we are doing a 'partial' select on the first level of the multiindex
    created = bulk_create_service_pattern_service_links(
        service_pattern_service_links.loc[list(missing_sp_ids)]
    )

    # Create map of SPS DB ids
    id_map = pd.DataFrame(
        (obj.id for obj in chain(qs, created)),
        index=pd.MultiIndex.from_tuples(
            ((obj.service_pattern_id, obj.position) for obj in chain(qs, created)),
            names=["service_pattern_id", "position"],
        ),
        columns=["id"],
    )

    # Join DB ids onto service_patterns
    service_pattern_service_links = service_pattern_service_links.join(id_map)

    return service_pattern_service_links


def transform_service_links(
    service_links: gpd.GeoDataFrame, stops: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:

    if len(service_links) == 0:
        # Pandas doesn't play well where the is no data
        return service_links

    # Merge from_stop_id and to_stop_id
    service_links = service_links.merge(
        stops["id"].rename("from_stop_id"),
        how="left",
        left_on="from_stop",
        right_index=True,
    ).merge(
        stops["id"].rename("to_stop_id"),
        how="left",
        left_on="to_stop",
        right_index=True,
    )

    # Fetch service links
    fetch = set(service_links.index)

    # Find intersection and difference of stops referenced in report to what is
    # in the DB
    qs = ServiceLink.objects.filter(ito_id__in=fetch)

    # Create set of ito_ids returned from the DB
    fetched = {item.ito_id for item in qs}

    # Create missing
    missing = fetch - fetched
    created = bulk_create_service_links(service_links.loc[list(missing)])

    # Create id to ito_id map
    ito_id_to_id = create_id_map(chain(qs, created))

    # Join StopPoint id onto stops df
    service_links = service_links.join(ito_id_to_id)

    return service_links


def transform_timing_patterns(
    service_patterns: gpd.GeoDataFrame,
    timing_patterns: pd.DataFrame,
):

    if len(timing_patterns) == 0:
        # Pandas doesn't play well where the is no data
        return timing_patterns

    # Merge SP DB id on timing patterns
    timing_patterns = timing_patterns.merge(
        service_patterns["id"].rename("service_pattern_id"),
        how="left",
        left_on="service_pattern_ito_id",
        right_index=True,
    )

    # Fetch TPs
    fetch = set(timing_patterns.index)
    qs = TimingPattern.objects.filter(ito_id__in=fetch)

    # Create set of ito_ids returned from the DB
    fetched = {item.ito_id for item in qs}

    # Create missing
    missing = fetch - fetched
    created = bulk_create_timing_patterns(timing_patterns.loc[list(missing)])

    # Create ServiceLinks and return id to ito_id
    id_map = create_id_map(chain(qs, created))

    # Join DB ids onto service_patterns
    timing_patterns = timing_patterns.join(id_map)

    return timing_patterns


def transform_timing_pattern_stops(
    timing_patterns: pd.DataFrame,
    service_pattern_stops: pd.DataFrame,
) -> pd.DataFrame:

    if len(timing_patterns) == 0:
        # Pandas doesn't play well where the is no data
        return

    # Create timing pattern stops by unpacking lists of timing in the
    # timing_patterns DataFrame
    timing_pattern_stops = (
        timing_patterns.reset_index()[["id", "timings"]].groupby("id")
        # Note since groupby/apply works with DFs, we select stops from the first
        # row (there should only be one row)
        .apply(
            lambda df: pd.DataFrame(
                df["timings"].iloc[0],
                columns=[
                    "arrival_time_secs",
                    "departure_time_secs",
                    "pickup_allowed",
                    "setdown_allowed",
                    "timing_point",
                ],
            ),
        )
    )

    # rename multiindex
    timing_pattern_stops.index = timing_pattern_stops.index.rename(
        ["timing_pattern_id", "position"]
    )

    # Merge SPS id onto TPS
    tp_to_sp = timing_patterns.reset_index()[["id", "service_pattern_id"]].rename(
        columns={"id": "timing_pattern_id"}
    )
    sps = service_pattern_stops.reset_index()[
        ["service_pattern_id", "position", "id"]
    ].rename(columns={"id": "service_pattern_stop_id"})

    # the TPS DF now maps the timing information for each TP to each stop (via SPS)
    timing_pattern_stops = (
        timing_pattern_stops.reset_index()
        .merge(tp_to_sp, on="timing_pattern_id")
        .merge(sps, on=["service_pattern_id", "position"])
        .set_index(["timing_pattern_id", "position"])
    )

    # Load TPS into DB

    # Fetch existing TPS - note we grab everything for the TP
    fetch = set(timing_patterns.index)
    qs = (
        TimingPatternStop.objects.select_related("timing_pattern")
        .select_related("service_pattern_stop")
        .filter(timing_pattern__ito_id__in=fetch)
    )

    # Create set of ids returned from the DB
    fetched = {item.timing_pattern.ito_id for item in qs}

    # Create missing
    missing = fetch - fetched

    # missing above is expressed in 'ito_ids', convert to known SP ids
    missing_tp_ids = timing_patterns.loc[list(missing), "id"]

    if not missing_tp_ids.empty:
        # note we are doing a 'partial' select on the first level of the multiindex
        tps = timing_pattern_stops.loc[list(missing_tp_ids)]

        # convert 'arrival_time_secs' and 'departure_time_secs' into durations.
        tps["arrival"] = tps["arrival_time_secs"].apply(
            lambda x: datetime.timedelta(seconds=x)
        )
        tps["departure"] = tps["departure_time_secs"].apply(
            lambda x: datetime.timedelta(seconds=x)
        )
        created = bulk_create_timing_pattern_stops(tps)
    else:
        created = []

    # Create map of TPS DB ids
    id_map = pd.DataFrame(
        (
            (obj.id, obj.timing_pattern_id, obj.service_pattern_stop_id)
            for obj in chain(qs, created)
        ),
        columns=[
            "timing_pattern_stop_id",
            "timing_pattern_id",
            "service_pattern_stop_id",
        ],
    )

    timing_pattern_stops = timing_pattern_stops.reset_index().merge(
        id_map, on=["timing_pattern_id", "service_pattern_stop_id"]
    )

    return timing_pattern_stops.set_index(["timing_pattern_id", "position"])


def transform_vehicle_journeys(
    vehicle_journeys: pd.DataFrame, timing_patterns: pd.DataFrame
):
    if len(vehicle_journeys) == 0:
        # There appears to be a bug in Pandas which causes 'index.name' to be
        # set to None the selected DF is empty
        return vehicle_journeys

    # Merge timing_pattern_id onto VJs
    vehicle_journeys = vehicle_journeys.merge(
        timing_patterns["id"].rename("timing_pattern_id"),
        left_on="timing_pattern_ito_id",
        right_index=True,
    )

    # can't use datetime.min incase start is negative
    min_datetime = datetime.datetime.min + datetime.timedelta(days=7)
    # Convert start time from 'seconds past midnight' into time
    vehicle_journeys["start_time"] = vehicle_journeys["start"].apply(
        lambda x: (min_datetime + datetime.timedelta(seconds=x)).time()
    )

    # Load VJs into DB

    # Fetch existing DPS - note we grab everything for the TP
    fetch = set(vehicle_journeys.index)
    qs = VehicleJourney.objects.select_related("timing_pattern").filter(
        ito_id__in=fetch
    )

    # Create set of ids returned from the DB
    fetched = {item.ito_id for item in qs}

    # Create missing
    missing = fetch - fetched
    created = bulk_create_vehicle_journeys(vehicle_journeys.loc[list(missing)])

    # Create ServiceLinks and return id to ito_id
    id_map = create_id_map(chain(qs, created))

    # Join DB ids onto service_patterns
    vehicle_journeys = vehicle_journeys.join(id_map)

    return vehicle_journeys


# DataFrame factories


def create_id_map(data: Iterable):
    return (
        pd.DataFrame(
            ({"id": item.id, "ito_id": item.ito_id} for item in data),
            columns=["id", "ito_id"],
        )
        .astype({"id": "int", "ito_id": "object"})
        .set_index("ito_id", verify_integrity=True)
    )


# Bulk create methods


def add_services_to_report(
    report: DataQualityReport, service_ids: List[int]
) -> List[Service.reports.through]:
    """Adds service objects to report m2m using their id"""
    through = Service.reports.through

    def inner():
        for service_id in service_ids:
            yield through(dataqualityreport_id=report.id, service_id=service_id)

    return through.objects.bulk_create(inner(), ignore_conflicts=True)


def bulk_create_stoppoints(stops: pd.DataFrame) -> List[StopPoint]:
    """Creates StopPoints from the DataFrame"""

    if len(stops) == 0:
        # There appears to be a bug in Pandas which causes 'index.name' to be
        # set to None the selected DF is empty
        return []

    # Check required columns and index
    required_columns = {"name", "atco_code", "geometry", "bearing", "type", "synthetic"}
    assert (required_columns - set(stops.columns)) == set()
    assert stops.index.name == "ito_id"

    def inner():
        for record in stops.itertuples():
            yield StopPoint(
                ito_id=record.Index,
                atco_code=record.atco_code,
                is_provisional=record.synthetic,
                name=record.name,
                geometry=Point(record.geometry.x, record.geometry.y, srid=4326),
                bearing=record.bearing,
                type=record.type,
            )

    return StopPoint.objects.bulk_create(inner())


def bulk_create_services(lines: pd.DataFrame) -> List[Service]:
    """Creates Services from the DataFrame"""

    if len(lines) == 0:
        # There appears to be a bug in Pandas which causes 'index.name' to be
        # set to None the selected DF is empty
        return []

    # Check required columns and index
    required_columns = {"name"}
    assert (required_columns - set(lines.columns)) == set()
    assert lines.index.name == "ito_id"

    def inner():
        for record in lines.itertuples():
            yield Service(
                ito_id=record.Index,
                name=record.name,
            )

    return Service.objects.bulk_create(inner())


def bulk_create_service_patterns(
    service_patterns: pd.DataFrame,
) -> List[ServicePattern]:
    """Creates ServicePatterns from the DataFrame"""

    if len(service_patterns) == 0:
        # There appears to be a bug in Pandas which causes 'index.name' to be
        # set to None the selected DF is empty
        return []

    # Check required columns and index
    required_columns = {"name", "geometry", "service_id"}
    assert (required_columns - set(service_patterns.columns)) == set()
    assert service_patterns.index.name == "ito_id"

    def inner():
        for record in service_patterns.itertuples():
            yield ServicePattern(
                ito_id=record.Index,
                service_id=record.service_id,
                name=record.name,
                geometry=LineString(list(record.geometry.coords), srid=4326),
            )

    return ServicePattern.objects.bulk_create(inner())


def bulk_create_service_links(service_links: gpd.GeoDataFrame) -> List[ServiceLink]:
    """Creates ServiceLinks from the GeoDataFrame"""

    if len(service_links) == 0:
        # There appears to be a bug in Pandas which causes 'index.name'
        # to be set to None the selected DF is empty
        return []

    # Check service_patterns has required columns and index
    required_columns = {"geometry", "from_stop_id", "to_stop_id"}
    assert (required_columns - set(service_links.columns)) == set()
    assert service_links.index.name == "ito_id"

    def inner():
        for record in service_links.itertuples():
            yield ServiceLink(
                ito_id=record.Index,
                from_stop_id=record.from_stop_id,
                to_stop_id=record.to_stop_id,
                geometry=LineString(list(record.geometry.coords), srid=4326),
            )

    return ServiceLink.objects.bulk_create(inner())


def bulk_create_service_pattern_stops(
    service_pattern_stops: pd.DataFrame,
) -> List[ServicePatternStop]:
    """Creates ServiceLinks from the GeoDataFrame"""

    if len(service_pattern_stops) == 0:
        # There appears to be a bug in Pandas which causes 'index.name' to be
        # set to None the selected DF is empty
        return []

    # Check service_patterns has required columns and index
    required_columns = {
        "stop_id",
    }
    assert (required_columns - set(service_pattern_stops.columns)) == set()
    assert tuple(service_pattern_stops.index.names) == (
        "service_pattern_id",
        "position",
    )

    def inner():
        for record in service_pattern_stops.itertuples():
            yield ServicePatternStop(
                service_pattern_id=record.Index[0],
                position=record.Index[1],
                stop_id=record.stop_id,
            )

    return ServicePatternStop.objects.bulk_create(inner())


def bulk_create_service_pattern_service_links(
    service_pattern_service_links: pd.DataFrame,
) -> List[ServicePatternStop]:
    """Creates ServiceLinks from the GeoDataFrame"""

    if len(service_pattern_service_links) == 0:
        # There appears to be a bug in Pandas which causes 'index.name' to be
        # set to None the selected DF is empty
        return []

    # Check service_patterns has required columns and index
    required_columns = {
        "service_link_id",
    }
    assert (required_columns - set(service_pattern_service_links.columns)) == set()
    assert tuple(service_pattern_service_links.index.names) == (
        "service_pattern_id",
        "position",
    )

    def inner():
        for record in service_pattern_service_links.itertuples():
            yield ServicePatternServiceLink(
                service_pattern_id=record.Index[0],
                position=record.Index[1],
                service_link_id=record.service_link_id,
            )

    return ServicePatternServiceLink.objects.bulk_create(inner())


def bulk_create_timing_patterns(
    timing_patterns: pd.DataFrame,
) -> List[TimingPattern]:
    """Creates TimingPatterns from the DataFrame"""

    if len(timing_patterns) == 0:
        # There appears to be a bug in Pandas which causes 'index.name'
        # to be set to None the selected DF is empty
        return []

    # Check required columns and index
    required_columns = {"service_pattern_id"}
    assert (required_columns - set(timing_patterns.columns)) == set()
    assert timing_patterns.index.name == "ito_id"

    def inner():
        for record in timing_patterns.itertuples():
            yield TimingPattern(
                ito_id=record.Index,
                service_pattern_id=record.service_pattern_id,
            )

    return TimingPattern.objects.bulk_create(inner())


def bulk_create_timing_pattern_stops(
    timing_pattern_stops: pd.DataFrame,
) -> List[TimingPatternStop]:
    """Creates TimingPatternStops from the DataFrame"""

    if len(timing_pattern_stops) == 0:
        # There appears to be a bug in Pandas which causes 'index.name' to be
        # set to None the selected DF is empty
        return []

        # Check required columns and index
    required_columns = {
        "service_pattern_stop_id",
        # "arrival_time_secs",
        # "departure_time_secs",
        "arrival",
        "departure",
        "pickup_allowed",
        "setdown_allowed",
        "timing_point",
        # "distance",
        # "speed",
    }
    assert (required_columns - set(timing_pattern_stops.columns)) == set()
    assert tuple(timing_pattern_stops.index.names) == ("timing_pattern_id", "position")

    def inner():
        for record in timing_pattern_stops.itertuples():
            yield TimingPatternStop(
                timing_pattern_id=record.Index[0],
                service_pattern_stop_id=record.service_pattern_stop_id,
                arrival=record.arrival,
                departure=record.departure,
                pickup_allowed=record.pickup_allowed,
                setdown_allowed=record.setdown_allowed,
                timing_point=record.timing_point,
            )

    return TimingPatternStop.objects.bulk_create(inner())


def bulk_create_vehicle_journeys(
    vehicle_journeys: pd.DataFrame,
) -> List[VehicleJourney]:
    """Creates VehicleJourneys from the DataFrame"""

    if len(vehicle_journeys) == 0:
        # There appears to be a bug in Pandas which causes 'index.name' to
        # be set to None the selected DF is empty
        return []

        # Check required columns and index
    required_columns = {
        "timing_pattern_id",
        "start_time",
    }
    assert (required_columns - set(vehicle_journeys.columns)) == set()
    assert vehicle_journeys.index.name == "ito_id"

    def inner():
        for record in vehicle_journeys.itertuples():
            yield VehicleJourney(
                ito_id=record.Index,
                timing_pattern_id=record.timing_pattern_id,
                start_time=record.start_time,
                dates=record.dates,
            )

    return VehicleJourney.objects.bulk_create(inner())
