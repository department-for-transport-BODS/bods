from typing import Dict

import pandas as pd

from transit_odp.naptan.models import AdminArea
from transit_odp.organisation.constants import TravelineRegions
from transit_odp.otc.models import Service


def get_all_naptan_atco_df() -> pd.DataFrame:
    """
    Return a dataframe with is_english_region value (bool) if services is in english region,
    Services in engligh regions are considered as in scope
    """
    return pd.DataFrame.from_records(
        AdminArea.objects.add_is_english_region().values(
            "atco_code", "is_english_region", "ui_lta_id"
        )
    )


def get_lta_traveline_region_map(ui_lta) -> str:
    """
    Return a pipe "|" seprated list fo traveline regions names for a given ui_lta
    """
    return "|".join(
        [
            str(TravelineRegions(admin_area.traveline_region_id).label)
            for admin_area in AdminArea.objects.filter(ui_lta=ui_lta).all()
        ]
    )


def get_weca_traveline_region_map(ui_lta) -> Dict[str, str]:
    """
    Return a dictionary with key as atco code and value as the traveline region name,
    """
    return {
        admin_area.atco_code: TravelineRegions(admin_area.traveline_region_id).label
        for admin_area in AdminArea.objects.filter(ui_lta=ui_lta).all()
    }


def get_weca_services_register_numbers(ui_lta):
    """
    Return the WECA services for a given ui lta
    """
    return Service.objects.filter(
        atco_code__in=AdminArea.objects.filter(ui_lta=ui_lta).values("atco_code"),
        licence_id__isnull=False,
    ).values("id")


def get_service_ui_ltas(service):
    """
    Get a list of UI Ltas for a OTC service
    """
    service_registrations = service.registration.all()
    ui_ltas_list = []
    for lta in service_registrations:
        if lta.ui_lta:
            ui_ltas_list.append(lta.ui_lta)
    return ui_ltas_list


def ui_ltas_string(ui_ltas):
    """
    Create a string of ui lta names seprated by pipe "|"
    """
    return "|".join(set([ui_lta.name for ui_lta in ui_ltas]))


def get_service_traveline_regions(ui_ltas):
    """
    Create a string of traveline regions for UI LTAS
    """
    return "|".join(
        [
            str(TravelineRegions(admin_area.traveline_region_id).label)
            for admin_area in AdminArea.objects.filter(ui_lta__in=ui_ltas)
            .distinct("traveline_region_id")
            .order_by("traveline_region_id")
            .all()
        ]
    )
