from typing import Dict, List, Tuple

import pandas as pd

from transit_odp.naptan.models import AdminArea
from transit_odp.organisation.constants import TravelineRegions
from transit_odp.otc.models import Service, UILta


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
    for a specific ui lta
    """
    return {
        admin_area.atco_code: TravelineRegions(admin_area.traveline_region_id).label
        for admin_area in AdminArea.objects.filter(ui_lta=ui_lta).all()
    }


def get_all_weca_traveline_region_map() -> Dict[str, Dict[str, str]]:
    """
    Return a dictionary with key as atco code and value as a dictionary of region name and ui_lta_name
    """
    return {
        admin_area.atco_code: {
            "region": get_traveline_region_from_id(admin_area.traveline_region_id),
            "ui_lta_name": admin_area.ui_lta and admin_area.ui_lta.name,
        }
        for admin_area in AdminArea.objects.all()
    }


def get_traveline_region_from_id(id: str) -> str:
    """Return Region name if present in the enum field
    Else return id as it is

    Args:
        id (str): Traveline Region Key

    Returns:
        str: Region name
    """
    try:
        return TravelineRegions(id).label
    except Exception:
        return id


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


class LTACSVHelper:
    """Class with methods to compute LTA related information,
    Used in both LTA completeness report and Operator compleness report
    """

    def __init__(self) -> None:
        self.otc_service_traveline_region = {}
        self.otc_service_ui_ltas = {}
        self.weca_traveline_region_status = {}
        self.otc_traveline_region_status = {}

    def get_otc_service_traveline_region(
        self, ui_ltas: List[UILta], ui_ltas_dict_key: Tuple[UILta]
    ) -> str:
        """Returns a pipe "|" seprate list of all the traveline regions
        the UI LTAs belongs to, Dict will be prepared for the values

        Args:
            ui_ltas (List[UILta]): List of UI LTAs
            ui_ltas_dict_key (Tuple[UILta]): Tuple of UI LTAs to be used
            as key for the dictionary

        Returns:
            str: pipe "|" seprated string of UI LTA's
        """
        if ui_ltas_dict_key not in self.otc_service_traveline_region:
            self.otc_service_traveline_region[
                ui_ltas_dict_key
            ] = get_service_traveline_regions(ui_ltas)
        return self.otc_service_traveline_region.get(ui_ltas_dict_key, "")

    def get_otc_ui_lta(
        self, ui_ltas: List[UILta], ui_ltas_dict_key: Tuple[UILta]
    ) -> str:
        """Return a pipe "|" seprate string of the UI LTA names for the service
        dictionary of the ui ltas will be maintained in order to minimize the
        manipulations

        Args:
            ui_ltas (List[UILta]): List of UI LTAs the service belongs to
            ui_ltas_dict_key (Tuple[UILta]): Tuple of UI LTAs to make key in dict

        Returns:
            str: Pipe "|" seprated list of UI LTAs
        """
        if ui_ltas_dict_key not in self.otc_service_ui_ltas:
            self.otc_service_ui_ltas[ui_ltas_dict_key] = ui_ltas_string(ui_ltas)
        return self.otc_service_ui_ltas.get(ui_ltas_dict_key, "")

    def get_is_english_region_otc(
        self,
        ui_ltas: List[UILta],
        ui_ltas_dict_key: Tuple[UILta],
        naptan_adminarea_df: pd.DataFrame,
    ) -> bool:
        """Find if the annotated key is_english_region for naptan admin area is True or False for
        any of the UI LTAs this service belongs to

        Args:
            ui_ltas (List[UILta]): List of UI LTAs the service belongs to
            ui_ltas_dict_key (Tuple[UILta]): Tuple value of UI LTAs for keys
            naptan_adminarea_df (pd.DataFrame): Dataframe for the admin area values

        Returns:
            bool: Returns True is the atco code passed belongs to an enlish region
        """
        if ui_ltas_dict_key not in self.otc_traveline_region_status:
            self.otc_traveline_region_status[
                ui_ltas_dict_key
            ] = not naptan_adminarea_df.empty and any(
                (
                    naptan_adminarea_df[
                        naptan_adminarea_df["ui_lta_id"].isin(
                            [ui_lta.id for ui_lta in ui_ltas]
                        )
                    ]
                )["is_english_region"]
            )
        return self.otc_traveline_region_status.get(ui_ltas_dict_key, "")

    def get_is_english_region_weca(
        self, atco_code: str, naptan_adminarea_df: pd.DataFrame
    ) -> bool:
        """Find if the annotated key is_english_region is True or False for
        The provided atco code
        For weca services if atco code belongs to an Naptan Admin area
        Such services will be considered in english region.

        Args:
            atco_code (str): Atco code to be checked
            naptan_adminarea_df (pd.DataFrame): Naptan admin areas list

        Returns:
            bool: Returns True is the atco code passed belongs to an enlish region
        """
        if atco_code not in self.weca_traveline_region_status:
            self.weca_traveline_region_status[
                atco_code
            ] = not naptan_adminarea_df.empty and any(
                (naptan_adminarea_df[naptan_adminarea_df["atco_code"] == atco_code])[
                    "is_english_region"
                ]
            )
        return self.weca_traveline_region_status.get(atco_code, "")

    def get_otc_service_details(
        self, service: Service, naptan_adminarea_df: pd.DataFrame
    ) -> Tuple:
        """Get otc service details, UI LTA names, Traveline Regions,
        and is the service belongs to english

        Args:
            service (Service): Service to get details from
            naptan_adminarea_df (pd.DataFrame): naptan dataframe with the details

        Returns:
            Tuple:  is_english_region: str
                    ui_lta_name:str
                    traveline_region: str
        """
        ui_ltas = get_service_ui_ltas(service)
        ui_ltas_dict_key = tuple(ui_ltas)
        is_english_region = self.get_is_english_region_otc(
            ui_ltas, ui_ltas_dict_key, naptan_adminarea_df
        )
        ui_lta_name = self.get_otc_ui_lta(ui_ltas, ui_ltas_dict_key)
        traveline_region = self.get_otc_service_traveline_region(
            ui_ltas, ui_ltas_dict_key
        )

        return is_english_region, ui_lta_name, traveline_region
