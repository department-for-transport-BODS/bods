import pandas as pd
from celery.utils.log import get_task_logger

from transit_odp.naptan.models import AdminArea, District, Locality, StopPoint

logger = get_task_logger(__name__)


def extract_stops_from_db():
    def inner():
        for stop in StopPoint.objects.all():
            yield {"atco_code": stop.atco_code, "obj": stop}

    df = pd.DataFrame(
        inner(),
        columns=["atco_code", "obj"],
    ).set_index("atco_code")
    return df


def extract_admin_areas_from_db():
    def inner():
        for admin_area in AdminArea.objects.all():
            yield {"id": admin_area.id, "obj": admin_area}

    df = pd.DataFrame(
        inner(),
        columns=["id", "obj"],
    ).set_index("id")
    return df


def extract_districts_from_db():
    def inner():
        for district in District.objects.all():
            yield {"id": district.id, "obj": district}

    df = pd.DataFrame(
        inner(),
        columns=["id", "obj"],
    ).set_index("id")
    return df


def extract_localities_from_db():
    def inner():
        for locality in Locality.objects.all():
            yield {"gazetteer_id": locality.gazetteer_id, "obj": locality}

    df = pd.DataFrame(
        inner(),
        columns=["gazetteer_id", "obj"],
    ).set_index("gazetteer_id")
    return df


def get_new_data(naptan_data, db_data):
    intersection = naptan_data[~naptan_data.index.isin(db_data.index)]
    return intersection


def get_existing_data(naptan_data, db_data, merge_on_field):
    existing_data = pd.merge(naptan_data, db_data, how="inner", on=merge_on_field)
    return existing_data
