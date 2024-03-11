from transit_odp.naptan.models import AdminArea
from transit_odp.otc.models import Service
from transit_odp.organisation.constants import TravelineRegions
from typing import Dict


def get_all_naptan_atco_map() -> Dict[str, str]:
    """
    Return a dictionary with key as atco code and value (bool) if services is in english region,
    Services in engligh regions are considered as in scope
    """
    return {
        admin_area.atco_code: admin_area.is_english_region
        for admin_area in AdminArea.objects.add_is_english_region().all()
    }


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
