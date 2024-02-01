""" dataframes.py
A collection of utility functions for converting pandas dataframes to and from
BODS transxchange models.
"""
import logging
from collections import OrderedDict
from typing import Iterator

import geopandas
import pandas as pd
from shapely.geometry import Point

from transit_odp.organisation.models import DatasetRevision
from transit_odp.transmodel.models import (
    Service,
    ServiceLink,
    ServicePattern,
    StopPoint,
    BookingArrangements,
    VehicleJourney,
    ServicedOrganisations,
)

ServicePatternThrough = ServicePattern.service_links.through
logger = logging.getLogger(__name__)


def create_stop_point_cache(revision_id):
    stops = (
        StopPoint.objects.filter(
            service_pattern_stops__service_pattern__revision_id=revision_id
        )
        .distinct("id")
        .order_by("id")
    )
    return create_naptan_stoppoint_df_from_queryset(stops)


def create_service_link_cache(revision_id):
    service_links = ServiceLink.objects.filter(
        service_patterns__revision_id=revision_id
    ).distinct()

    return create_service_link_df_from_queryset(service_links)


def create_naptan_stoppoint_df(data=None):
    # Note id is float64 as it may contain missing values
    typings = OrderedDict(
        {
            "naptan_id": "object",
            "atco_code": "object",
            "geometry": "geometry",
            "locality_id": "str",
        }
    )
    return (
        geopandas.GeoDataFrame(data, columns=typings.keys())
        .astype(typings)
        .set_index("atco_code", verify_integrity=True)
    )


def create_naptan_stoppoint_df_from_queryset(queryset):
    stop_points = (
        {
            "naptan_id": obj.id,
            "atco_code": obj.atco_code,
            "locality_id": obj.locality_id,
            "geometry": Point(obj.location.x, obj.location.y),
        }
        for obj in queryset
    )
    return create_naptan_stoppoint_df(stop_points)


def create_service_df(data=None):
    columns = ["id", "service_code", "start_date", "end_date"]
    return pd.DataFrame(data, columns=columns).set_index(
        "service_code", verify_integrity=True
    )


def create_service_df_from_queryset(queryset):
    return create_service_df(
        (
            {
                "id": obj.id,
                "service_code": obj.service_code,
                "start_date": obj.start_date,
                "end_date": obj.end_date,
            }
            for obj in queryset
        )
    )


def create_service_link_df(data=None):
    columns = OrderedDict(
        {
            "id": "float64",
            "from_stop_atco": "object",
            "to_stop_atco": "object",
            "from_stop_id": "float64",
            "to_stop_id": "float64",
        }
    )
    return (
        pd.DataFrame(data, columns=columns.keys())
        .astype(columns)
        .set_index(["from_stop_atco", "to_stop_atco"], verify_integrity=True)
    )  # using a multiindex makes selections easier


def create_service_link_df_from_queryset(qs):
    return create_service_link_df(
        (
            {
                "id": obj.id,
                "from_stop_atco": obj.from_stop_atco,
                "to_stop_atco": obj.to_stop_atco,
                "from_stop_id": obj.from_stop_id,
                "to_stop_id": obj.to_stop_id,
            }
            for obj in qs
        )
    )


def create_naptan_locality_df(data=None):
    # Note id is float64 as it may contain missing values
    columns = OrderedDict(
        {"locality_id": "str", "locality_name": "str", "admin_area_id": "object"}
    )
    return (
        pd.DataFrame(data, columns=columns.keys())
        .astype(columns)
        .set_index("locality_id", verify_integrity=True)
    )


def df_to_service_patterns(
    revision: DatasetRevision, df: pd.DataFrame
) -> Iterator[ServicePattern]:
    for record in df.reset_index().to_dict("records"):
        yield ServicePattern(
            revision=revision,
            service_pattern_id=record["service_pattern_id"],
            geom=record["geometry"],
        )


def df_to_services(revision: DatasetRevision, df: pd.DataFrame) -> Iterator[Service]:
    for record in df.to_dict("records"):
        start_date = record["start_date"]
        if pd.isnull(start_date):
            start_date = None
        end_date = record["end_date"]
        if pd.isnull(end_date):
            end_date = None
        line_names = record["line_names"]
        service_type = record["service_type"]
        yield Service(
            revision=revision,
            service_code=record["service_code"],
            start_date=start_date,
            end_date=end_date,
            name=line_names[0],
            other_names=line_names[1:],
            service_type=service_type,
        )


def df_to_vehicle_journeys(df: pd.DataFrame) -> Iterator[VehicleJourney]:
    for record in df.to_dict("records"):
        yield VehicleJourney(
            journey_code=record["journey_code"],
            start_time=record["departure_time"],
            line_ref=record["line_ref"],
            direction=record["direction"],
        )


def df_to_serviced_organisations(
    df: pd.DataFrame, existing_serviced_orgs
) -> Iterator[ServicedOrganisations]:
    unique_names = df.loc[~df["name"].isin(existing_serviced_orgs), "name"].unique()

    for name in unique_names:
        yield ServicedOrganisations(name=name)


def df_to_service_links(df: pd.DataFrame) -> Iterator[ServiceLink]:
    for record in df.reset_index().to_dict("records"):
        from_stop_id = record["from_stop_id"]
        if pd.isnull(from_stop_id):
            from_stop_id = None
        to_stop_id = record["to_stop_id"]
        if pd.isnull(to_stop_id):
            to_stop_id = None
        yield ServiceLink(
            from_stop_atco=record["from_stop_atco"],
            to_stop_atco=record["to_stop_atco"],
            from_stop_id=from_stop_id,
            to_stop_id=to_stop_id,
        )


def df_to_service_pattern_service(
    df: pd.DataFrame,
) -> Iterator[ServicePatternThrough]:
    for record in df[["id", "service_link_id"]].to_dict("records"):
        yield ServicePatternThrough(
            servicepattern_id=record["id"], servicelink_id=record["service_link_id"]
        )


def get_first_and_last_expiration_dates(expiration_dates: list, start_dates: list):
    """Compute the first and last expiration dates (excluding '9999-09-09'
    which is declared as the default)"""
    first_expiring_service = None
    last_expiring_service = None
    first_service_start = None
    logger.info("[get_first_and_last_expiration_dates]:{start_dates}")
    for date in expiration_dates:
        if date:
            if first_expiring_service is None or date < first_expiring_service:
                first_expiring_service = date

            if last_expiring_service is None or date > last_expiring_service:
                last_expiring_service = date
    for date in start_dates:
        if date:
            if first_service_start is None or date < first_service_start:
                logger.info("[get_first_and_last_expiration_dates]:{date}")
                first_service_start = date
    return first_expiring_service, last_expiring_service, first_service_start


def get_min_date_or_none(dates):
    dates = [date for date in dates if date is not None]
    return min(dates) if dates else None


def get_max_date_or_none(dates):
    dates = [date for date in dates if date is not None]
    return max(dates) if dates else None


def df_to_booking_arrangements(
    revision: DatasetRevision, df: pd.DataFrame
) -> Iterator[BookingArrangements]:
    for record in df.reset_index().to_dict("records"):
        service_id = record["id"]

        yield BookingArrangements(
            service_id=service_id,
            description=record["description"],
            email=record["email"],
            phone_number=record["tel_national_number"],
            web_address=record["web_address"],
        )
