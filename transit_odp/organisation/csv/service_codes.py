from datetime import datetime, timedelta
from typing import Dict, Optional

import pandas as pd
from waffle import flag_is_active

from transit_odp.avl.require_attention.abods.registery import AbodsRegistery
from transit_odp.avl.require_attention.weekly_ppc_zip_loader import (
    get_vehicle_activity_operatorref_linename,
)
from transit_odp.browse.common import (
    LTACSVHelper,
    get_all_naptan_atco_df,
    get_all_weca_traveline_region_map,
)
from transit_odp.browse.lta_column_headers import get_operator_name
from transit_odp.common.constants import FeatureFlags
from transit_odp.common.csv import CSVBuilder, CSVColumn
from transit_odp.organisation.models import TXCFileAttributes
from transit_odp.organisation.models.data import SeasonalService, ServiceCodeExemption
from transit_odp.otc.constants import (
    API_TYPE_EP,
    API_TYPE_WECA,
    OTC_SCOPE_STATUS_IN_SCOPE,
    OTC_SCOPE_STATUS_OUT_OF_SCOPE,
    UNDER_MAINTENANCE,
)
from transit_odp.otc.models import Service as OTCService
from transit_odp.publish.requires_attention import (
    evaluate_staleness,
    get_all_line_level_otc_map,
    get_dq_critical_observation_services_map,
    get_fares_compliance_status,
    get_fares_dataset_map,
    get_fares_published_status,
    get_fares_requires_attention,
    get_fares_timeliness_status,
    get_line_level_txc_map_service_base,
    is_stale,
)

STALENESS_STATUS = [
    "42 day look ahead is incomplete",
    "Service hasn't been updated within a year",
    "OTC variation not published",
]


def get_42_day_look_ahead_date() -> str:
    """
    Calculate today + the date 42 days from now.

    Returns:
        str: 42 day look ahead date
    """
    return (datetime.now() + timedelta(days=42)).strftime("%Y-%m-%d")


def get_seasonal_service_status(otc_service: dict) -> str:
    """
    Returns a value for seasonal status for a service.

    Args:
        otc_service (dict): OTC Service dictionary

    Returns:
        str: Seasonal Status value
    """
    seasonal_service_status = otc_service.get("seasonal_status")
    return "In Season" if seasonal_service_status else "Out of Season"


def get_service_code_exemption_map(
    organisation_id: int,
) -> Dict[str, ServiceCodeExemption]:
    """
    Returns dictionary of service code that are exempt.

    Args:
        organisation_id (int): Organisation ID

    Returns:
        Dict [str, ServiceCodeExemption]: Exempt service map
    """
    return {
        service.registration_number.replace("/", ":"): service
        for service in ServiceCodeExemption.objects.add_registration_number().filter(
            licence__organisation__id=organisation_id
        )
    }


def get_all_otc_map(organisation_id: int) -> Dict[str, OTCService]:
    """
    Get a dictionary which includes all OTC Services for an organisation.

    Args:
        organisation_id (int): Organisation ID

    Returns:
        Dict [str, OTCService]: All OTC services
    """
    return {
        service.registration_number.replace("/", ":"): service
        for service in OTCService.objects.get_all_otc_data_for_organisation(
            organisation_id
        )
    }


def get_seasonal_service_map(organisation_id: int) -> Dict[str, SeasonalService]:
    """
    Get a dictionary which includes all the Seasonal Services
    for an organisation.

    Args:
        organisation_id (int): Organisation ID

    Returns:
        Dict [str, SeasonalService]: All seasonal services
    """
    return {
        service.registration_number.replace("/", ":"): service
        for service in SeasonalService.objects.filter(
            licence__organisation_id=organisation_id
        )
        .add_registration_number()
        .add_seasonal_status()
    }


class ServiceCodesCSV(CSVBuilder, LTACSVHelper):
    """
    Line-level CSV operator report.
    """

    columns = [
        CSVColumn(
            header="Registration:Registration Number",
            accessor=lambda otc_service: otc_service.get("otc_registration_number"),
        ),
        CSVColumn(
            header="Registration:Service Number",
            accessor=lambda otc_service: otc_service.get("otc_service_number"),
        ),
        CSVColumn(
            header="Requires Attention",
            accessor=lambda otc_service: otc_service.get("require_attention"),
        ),
        CSVColumn(
            header="Published Status",
            accessor=lambda otc_service: (
                "Published" if otc_service.get("dataset_id") else "Unpublished"
            ),
        ),
        CSVColumn(
            header="Registration Status",
            accessor=lambda otc_service: (
                "Registered"
                if otc_service.get("otc_licence_number")
                else "Unregistered"
            ),
        ),
        CSVColumn(
            header="Scope Status",
            accessor=lambda otc_service: (
                OTC_SCOPE_STATUS_OUT_OF_SCOPE
                if otc_service.get("scope_status", False)
                else OTC_SCOPE_STATUS_IN_SCOPE
            ),
        ),
        CSVColumn(
            header="Seasonal Status",
            accessor=lambda otc_service: (
                get_seasonal_service_status(otc_service)
                if otc_service.get("seasonal_status") is not None
                else "Not Seasonal"
            ),
        ),
        CSVColumn(
            header="Timeliness Status",
            accessor=lambda otc_service: otc_service.get("staleness_status"),
        ),
        CSVColumn(
            header="Dataset ID",
            accessor=lambda otc_service: otc_service.get("dataset_id"),
        ),
        CSVColumn(
            header="XML:Filename",
            accessor=lambda otc_service: otc_service.get("xml_filename"),
        ),
        CSVColumn(
            header="XML:Last Modified Date",
            accessor=lambda otc_service: otc_service.get("last_modified_date"),
        ),
        CSVColumn(
            header="Operating Period End Date",
            accessor=lambda otc_service: otc_service.get("operating_period_end_date"),
        ),
        CSVColumn(
            header="Date Registration variation needs to be published",
            accessor=lambda otc_service: otc_service.get(
                "effective_stale_date_otc_effective_date"
            ),
        ),
        CSVColumn(
            header="Date for complete 42 day look ahead",
            accessor=lambda otc_service: get_42_day_look_ahead_date(),
        ),
        CSVColumn(
            header="Date when data is over 1 year old",
            accessor=lambda otc_service: otc_service.get(
                "effective_stale_date_last_modified_date"
            ),
        ),
        CSVColumn(
            header="Date seasonal service should be published",
            accessor=lambda otc_service: otc_service.get(
                "effective_seasonal_start_date"
            ),
        ),
        CSVColumn(
            header="Seasonal Start Date",
            accessor=lambda otc_service: otc_service.get("seasonal_start"),
        ),
        CSVColumn(
            header="Seasonal End Date",
            accessor=lambda otc_service: otc_service.get("seasonal_end"),
        ),
        CSVColumn(
            header="Registration:Operator Name",
            accessor=lambda otc_service: otc_service.get("registration_operator_name"),
        ),
        CSVColumn(
            header="Registration:Licence Number",
            accessor=lambda otc_service: otc_service.get("otc_licence_number"),
        ),
        CSVColumn(
            header="Registration:Service Type Description",
            accessor=lambda otc_service: otc_service.get("service_type_description"),
        ),
        CSVColumn(
            header="Registration:Variation Number",
            accessor=lambda otc_service: otc_service.get("variation_number"),
        ),
        CSVColumn(
            header="Registration:Expiry Date",
            accessor=lambda otc_service: otc_service.get("expiry_date"),
        ),
        CSVColumn(
            header="Registration:Effective Date",
            accessor=lambda otc_service: otc_service.get("effective_date"),
        ),
        CSVColumn(
            header="Registration:Received Date",
            accessor=lambda otc_service: otc_service.get("received_date"),
        ),
        CSVColumn(
            header="Traveline Region",
            accessor=lambda otc_service: otc_service.get("traveline_region"),
        ),
        CSVColumn(
            header="Local Transport Authority",
            accessor=lambda otc_service: otc_service.get("ui_lta_name"),
        ),
    ]

    def __init__(self, organisation_id: int):
        super().__init__()
        self._organisation_id = organisation_id
        self._object_list = []

    def _update_data(
        self,
        service: Optional[OTCService],
        file_attribute: Optional[TXCFileAttributes],
        seasonal_service: Optional[SeasonalService],
        exempted: Optional[bool],
        staleness_status: Optional[str],
        require_attention: str,
        traveline_region: str,
        ui_lta_name: str,
        line_name: str,
    ) -> None:
        self._object_list.append(
            {
                "require_attention": require_attention,
                "scope_status": exempted,
                "otc_licence_number": service and service.otc_licence_number,
                "otc_registration_number": service and service.registration_number,
                "otc_service_number": line_name,
                "last_modified_date": file_attribute
                and (file_attribute.modification_datetime.date()),
                "operating_period_start_date": file_attribute
                and (file_attribute.operating_period_start_date),
                "operating_period_end_date": file_attribute
                and (file_attribute.operating_period_end_date),
                "xml_filename": file_attribute and file_attribute.filename,
                "dataset_id": file_attribute and file_attribute.revision.dataset_id,
                "seasonal_status": seasonal_service
                and seasonal_service.seasonal_status,
                "seasonal_start": seasonal_service and seasonal_service.start,
                "seasonal_end": seasonal_service and seasonal_service.end,
                "staleness_status": staleness_status,
                "effective_seasonal_start_date": seasonal_service
                and seasonal_service.start - timedelta(days=42),
                "effective_stale_date_last_modified_date": file_attribute
                and file_attribute.effective_stale_date_last_modified_date,
                "effective_stale_date_otc_effective_date": service
                and (service.effective_stale_date_otc_effective_date),
                "traveline_region": traveline_region,
                "ui_lta_name": ui_lta_name,
                "variation_number": service and service.variation_number,
                "service_type_description": service
                and service.service_type_description,
                "registration_operator_name": (service and service.operator)
                and service.operator.operator_name,
                "expiry_date": service and service.licence.expiry_date,
                "effective_date": service and service.effective_date,
                "received_date": service and service.received_date,
            }
        )

    def _get_require_attention(
        self,
        exempted: Optional[bool],
        seasonal_service: Optional[SeasonalService],
    ) -> str:
        if exempted or (seasonal_service and not seasonal_service.seasonal_status):
            return "No"
        return "Yes"

    def get_otc_service_bods_data(self, organisation_id: int) -> None:
        """
        Compares an organisation's OTC Services dictionaries list with
        TXCFileAttributes dictionaries list and the SeasonalService list
        to determine which OTC Services require attention and which
        doesn't ie. not live in BODS at all, or live but meeting new
        Staleness conditions.
        """
        otc_map = get_all_line_level_otc_map(organisation_id)
        service_codes = [service_code for (service_code, line_name) in otc_map]
        txcfa_map = get_line_level_txc_map_service_base(service_codes)

        seasonal_service_map = get_seasonal_service_map(organisation_id)
        service_code_exemption_map = get_service_code_exemption_map(organisation_id)
        naptan_adminarea_df = get_all_naptan_atco_df()
        traveline_region_map_weca = get_all_weca_traveline_region_map()
        services_code = set(otc_map)
        services_code = sorted(services_code)

        for service_code, line_name in services_code:
            service = otc_map.get((service_code, line_name))
            file_attribute = txcfa_map.get((service_code, line_name))
            seasonal_service = seasonal_service_map.get(service_code)
            exemption = service_code_exemption_map.get(service_code)
            is_english_region = False
            traveline_region = ui_lta_name = ""

            if service:
                if service.api_type in [API_TYPE_WECA, API_TYPE_EP]:
                    is_english_region = self.get_is_english_region_weca(
                        service.atco_code, naptan_adminarea_df
                    )
                    traveline_region = traveline_region_map_weca.get(
                        service.atco_code, {"ui_lta_name": "", "region": ""}
                    )
                    ui_lta_name = traveline_region["ui_lta_name"]
                    traveline_region = traveline_region["region"]
                else:
                    (
                        is_english_region,
                        ui_lta_name,
                        traveline_region,
                    ) = self.get_otc_service_details(service, naptan_adminarea_df)

            exempted = False
            if not (
                not (exemption and exemption.registration_code) and is_english_region
            ):
                exempted = True

            staleness_status = "Up to date"
            if file_attribute is None:
                require_attention = self._get_require_attention(
                    exempted, seasonal_service
                )
            elif service and is_stale(service, file_attribute):
                rad = evaluate_staleness(service, file_attribute)
                staleness_status = STALENESS_STATUS[rad.index(True)]
                require_attention = self._get_require_attention(
                    exempted, seasonal_service
                )
            else:
                require_attention = "No"

            self._update_data(
                service,
                file_attribute,
                seasonal_service,
                exempted,
                staleness_status,
                require_attention,
                traveline_region,
                ui_lta_name,
                line_name,
            )

    def get_queryset(self):
        self.get_otc_service_bods_data(self._organisation_id)
        return self._object_list


class ComplianceReportCSV(CSVBuilder, LTACSVHelper):
    """
    Compliance CSV operator report.
    """

    columns = [
        CSVColumn(
            header="Registration:Registration Number",
            accessor=lambda otc_service: otc_service.get("otc_registration_number"),
        ),
        CSVColumn(
            header="Registration:Service Number",
            accessor=lambda otc_service: otc_service.get("otc_service_number"),
        ),
        CSVColumn(
            header="Registration Status",
            accessor=lambda otc_service: (
                "Registered"
                if otc_service.get("otc_licence_number")
                else "Unregistered"
            ),
        ),
        CSVColumn(
            header="Scope Status",
            accessor=lambda otc_service: (
                OTC_SCOPE_STATUS_OUT_OF_SCOPE
                if otc_service.get("scope_status", False)
                else OTC_SCOPE_STATUS_IN_SCOPE
            ),
        ),
        CSVColumn(
            header="Seasonal Status",
            accessor=lambda otc_service: (
                get_seasonal_service_status(otc_service)
                if otc_service.get("seasonal_status") is not None
                else "Not Seasonal"
            ),
        ),
        CSVColumn(
            header="Organisation Name",
            accessor=lambda otc_service: (
                get_operator_name(otc_service)
                if otc_service.get("operator_name") is None
                or otc_service.get("operator_name") == ""
                else otc_service.get("operator_name")
            ),
        ),
        CSVColumn(
            header="Requires Attention",
            accessor=lambda otc_service: otc_service.get("overall_requires_attention"),
        ),
        CSVColumn(
            header="Timetables requires attention",
            accessor=lambda otc_service: otc_service.get("require_attention"),
        ),
        CSVColumn(
            header="Timetables Published Status",
            accessor=lambda otc_service: (
                "Published" if otc_service.get("dataset_id") else "Unpublished"
            ),
        ),
        CSVColumn(
            header="Timetables Timeliness Status",
            accessor=lambda otc_service: otc_service.get("staleness_status"),
        ),
        CSVColumn(
            header="Timetables critical DQ issues",
            accessor=lambda otc_service: otc_service.get("dq_require_attention"),
        ),
        CSVColumn(
            header="AVL requires attention",
            accessor=lambda otc_service: otc_service.get("avl_requires_attention"),
        ),
        CSVColumn(
            header="AVL Published Status",
            accessor=lambda otc_service: otc_service.get("avl_published_status"),
        ),
        CSVColumn(
            header="Error in AVL to Timetable Matching",
            accessor=lambda otc_service: otc_service.get(
                "error_in_avl_to_timetable_matching"
            ),
        ),
        CSVColumn(
            header="Fares requires attention",
            accessor=lambda otc_service: otc_service.get("fares_requires_attention"),
        ),
        CSVColumn(
            header="Fares Published Status",
            accessor=lambda otc_service: otc_service.get("fares_published_status"),
        ),
        CSVColumn(
            header="Fares Timeliness Status",
            accessor=lambda otc_service: otc_service.get("fares_timeliness_status"),
        ),
        CSVColumn(
            header="Fares Compliance Status",
            accessor=lambda otc_service: otc_service.get("fares_compliance_status"),
        ),
        CSVColumn(
            header="Timetables Data set ID",
            accessor=lambda otc_service: otc_service.get("dataset_id"),
        ),
        CSVColumn(
            header="TXC:Filename",
            accessor=lambda otc_service: otc_service.get("xml_filename"),
        ),
        CSVColumn(
            header="TXC:NOC",
            accessor=lambda otc_service: otc_service.get("national_operator_code"),
        ),
        CSVColumn(
            header="TXC:Last Modified Date",
            accessor=lambda otc_service: otc_service.get("last_modified_date"),
        ),
        CSVColumn(
            header="Date when timetable data is over 1 year old",
            accessor=lambda otc_service: otc_service.get(
                "effective_stale_date_last_modified_date"
            ),
        ),
        CSVColumn(
            header="TXC:Operating Period End Date",
            accessor=lambda otc_service: otc_service.get("operating_period_end_date"),
        ),
        CSVColumn(
            header="Fares Data set ID",
            accessor=lambda otc_service: otc_service.get("fares_dataset_id"),
        ),
        CSVColumn(
            header="NETEX:Filename",
            accessor=lambda otc_service: otc_service.get("fares_filename"),
        ),
        CSVColumn(
            header="NETEX:Last Modified Date",
            accessor=lambda otc_service: otc_service.get("fares_last_modified_date"),
        ),
        CSVColumn(
            header="Date when fares data is over 1 year old",
            accessor=lambda otc_service: otc_service.get("fares_data_over_one_year"),
        ),
        CSVColumn(
            header="NETEX:Operating Period End Date",
            accessor=lambda otc_service: otc_service.get(
                "fares_operating_period_end_date"
            ),
        ),
        CSVColumn(
            header="Date Registration variation needs to be published",
            accessor=lambda otc_service: otc_service.get(
                "effective_stale_date_otc_effective_date"
            ),
        ),
        CSVColumn(
            header="Date for complete 42 day look ahead",
            accessor=lambda otc_service: get_42_day_look_ahead_date(),
        ),
        CSVColumn(
            header="Date seasonal service should be published",
            accessor=lambda otc_service: otc_service.get(
                "effective_seasonal_start_date"
            ),
        ),
        CSVColumn(
            header="Seasonal Start Date",
            accessor=lambda otc_service: otc_service.get("seasonal_start"),
        ),
        CSVColumn(
            header="Seasonal End Date",
            accessor=lambda otc_service: otc_service.get("seasonal_end"),
        ),
        CSVColumn(
            header="Registration:Operator Name",
            accessor=lambda otc_service: otc_service.get("registration_operator_name"),
        ),
        CSVColumn(
            header="Registration:Licence Number",
            accessor=lambda otc_service: otc_service.get("otc_licence_number"),
        ),
        CSVColumn(
            header="Registration:Service Type Description",
            accessor=lambda otc_service: otc_service.get("service_type_description"),
        ),
        CSVColumn(
            header="Registration:Variation Number",
            accessor=lambda otc_service: otc_service.get("variation_number"),
        ),
        CSVColumn(
            header="Registration:Expiry Date",
            accessor=lambda otc_service: otc_service.get("expiry_date"),
        ),
        CSVColumn(
            header="Registration:Effective Date",
            accessor=lambda otc_service: otc_service.get("effective_date"),
        ),
        CSVColumn(
            header="Registration:Received Date",
            accessor=lambda otc_service: otc_service.get("received_date"),
        ),
        CSVColumn(
            header="Traveline Region",
            accessor=lambda otc_service: otc_service.get("traveline_region"),
        ),
        CSVColumn(
            header="Local Transport Authority",
            accessor=lambda otc_service: otc_service.get("ui_lta_name"),
        ),
    ]

    def __init__(self, organisation_id: int):
        super().__init__()
        self._organisation_id = organisation_id
        self._object_list = []

    def _update_data(
        self,
        service: Optional[OTCService],
        file_attribute: Optional[TXCFileAttributes],
        seasonal_service: Optional[SeasonalService],
        exempted: Optional[bool],
        staleness_status: Optional[str],
        require_attention: str,
        traveline_region: str,
        ui_lta_name: str,
        line_name: str,
        avl_published_status: str,
        error_in_avl_to_timetable_matching: str,
        avl_requires_attention: str,
        fares_published_status: str,
        fares_timeliness_status: str,
        fares_compliance_status: str,
        fares_requires_attention: str,
        fares_dataset_id: int,
        fares_filename: str,
        fares_last_modified_date: str,
        fares_operating_period_end_date: str,
        fares_data_over_one_year: str,
        overall_requires_attention: str,
        dq_require_attention: str,
    ) -> None:
        self._object_list.append(
            {
                "require_attention": require_attention,
                "scope_status": exempted,
                "otc_licence_number": service and service.otc_licence_number,
                "otc_registration_number": service and service.registration_number,
                "otc_service_number": line_name,
                "last_modified_date": file_attribute
                and (file_attribute.modification_datetime.date()),
                "operating_period_start_date": file_attribute
                and (file_attribute.operating_period_start_date),
                "operating_period_end_date": file_attribute
                and (file_attribute.operating_period_end_date),
                "xml_filename": file_attribute and file_attribute.filename,
                "dataset_id": file_attribute and file_attribute.revision.dataset_id,
                "operator_name": file_attribute and file_attribute.organisation_name,
                "national_operator_code": file_attribute
                and file_attribute.national_operator_code,
                "seasonal_status": seasonal_service
                and seasonal_service.seasonal_status,
                "seasonal_start": seasonal_service and seasonal_service.start,
                "seasonal_end": seasonal_service and seasonal_service.end,
                "staleness_status": staleness_status,
                "effective_seasonal_start_date": seasonal_service
                and seasonal_service.start - timedelta(days=42),
                "effective_stale_date_last_modified_date": file_attribute
                and file_attribute.effective_stale_date_last_modified_date,
                "effective_stale_date_otc_effective_date": service
                and (service.effective_stale_date_otc_effective_date),
                "traveline_region": traveline_region,
                "ui_lta_name": ui_lta_name,
                "variation_number": service and service.variation_number,
                "service_type_description": service
                and service.service_type_description,
                "registration_operator_name": (service and service.operator)
                and service.operator.operator_name,
                "expiry_date": service and service.licence.expiry_date,
                "effective_date": service and service.effective_date,
                "received_date": service and service.received_date,
                "avl_published_status": avl_published_status,
                "error_in_avl_to_timetable_matching": error_in_avl_to_timetable_matching,
                "avl_requires_attention": avl_requires_attention,
                "fares_published_status": fares_published_status,
                "fares_timeliness_status": fares_timeliness_status,
                "fares_compliance_status": fares_compliance_status,
                "fares_requires_attention": fares_requires_attention,
                "fares_dataset_id": fares_dataset_id,
                "fares_filename": fares_filename,
                "fares_last_modified_date": fares_last_modified_date,
                "fares_data_over_one_year": fares_data_over_one_year,
                "fares_operating_period_end_date": fares_operating_period_end_date,
                "overall_requires_attention": overall_requires_attention,
                "dq_require_attention": dq_require_attention,
            }
        )

    def get_overall_requires_attention(
        self,
        timetable_requires_attention: Optional[str],
        avl_requires_attention: Optional[str],
        fares_requires_attention: Optional[str],
        exempted: Optional[bool],
        seasonal_service: Optional[SeasonalService],
    ) -> str:
        """
        Returns value for 'Requires attention' column based on the following logic:
            If 'Scope Status' = Out of Scope OR 'Seasonal Status' = Out of Season,
            then 'Requires attention' = No.
            If 'Timetables requires attention' = No AND 'AVL requires attention' = No
            AND 'Fares requires attention' = No,
            then 'Requires attention' = No.
            If 'Timetables requires attention' = Yes OR 'AVL requires attention' = Yes
            OR 'Fares requires attention' = Yes,
            then 'Requires attention' = Yes.

        Args:
            otc_service (dict): OTC Service dictionary

        Returns:
            str: Yes or No for 'Requires attention' column
        """
        if exempted or (seasonal_service and not seasonal_service.seasonal_status):
            return "No"
        if (
            (timetable_requires_attention == "No")
            and (avl_requires_attention == "No")
            and (fares_requires_attention == "No")
        ):
            return "No"
        return "Yes"

    def _get_require_attention(
        self,
        exempted: Optional[bool],
        seasonal_service: Optional[SeasonalService],
        service: Optional[OTCService],
        file_attribute: Optional[TXCFileAttributes],
        staleness_status: Optional[str],
        dq_require_attention: str,
    ) -> str:
        """
        Returns value for 'Timetables requires attention' column based on the following logic:
            Yes if all of these are true:
                Scope Status = In scope AND
                Seasonal Status = Not Seasonal or In Season AND
                Registration Status = Registered
                AND
                Published Status = Unpublished OR
                Timeliness Status != Up to Date OR
                Critical DQ Issues = Yes
            No if all of these are true:
                Scope Status = Out of Scope OR
                Seasonal Status = Out of Season

                Scope Status = In scope AND
                Seasonal Status = Not Seasonal or In Season AND
                Registration Status = Registered AND
                Published Status = Published AND
                Timeliness Status = Up to Date AND
                Critical DQ Issues = No

        Args:
            exempted (Optional[bool]): Boolean value for exempted service
            seasonal_service (Optional[SeasonalService]): Seasonal Service obj
            service (Optional[OTCService]): OTC Service obj
            file_attribute (Optional[TXCFileAttributes]): TXC file attribute obj
            staleness_status (Optional[str]): Staleness Status value
            dq_require_attention (str): Data quality require attention value

        Returns:
            str: Yes or No value for 'Timetables requires attention' column
        """
        if exempted or (seasonal_service and not seasonal_service.seasonal_status):
            return "No"
        if file_attribute is not None:
            registered_status = True if service.otc_licence_number else False
            published_status = True if file_attribute.revision.dataset_id else False

            if (
                registered_status
                and (not seasonal_service or seasonal_service.seasonal_status)
                and (not exempted)
                and published_status
                and (staleness_status == "Up to date")
                and dq_require_attention == "No"
            ):
                return "No"
        return "Yes"

    def get_avl_published_status(
        self, operator_ref: str, line_name: str, synced_in_last_month
    ) -> str:
        """
        Returns value for 'AVL Published Status' column.

        Args:
            operator_ref (str): National Operator Code
            line_name (str): Service Number
            synced_in_last_month: Records from ABODS API

        Returns:
            str: Yes or No for 'AVL Published Status' column
        """
        if f"{line_name}__{operator_ref}" in synced_in_last_month:
            return "Yes"
        return "No"

    def get_error_in_avl_to_timetable_matching(
        self, operator_ref: str, line_name: str, uncounted_activity_df: pd.DataFrame
    ) -> str:
        """
        Returns value for 'Error in AVL to Timetable Matching' column.

        Args:
            operator_ref (str): National Operator Code
            line_name (str): Service Number

        Returns:
            str: Yes or No for 'Error in AVL to Timetable Matching' column
        """

        if not uncounted_activity_df.loc[
            (uncounted_activity_df["OperatorRef"] == operator_ref)
            & (
                uncounted_activity_df["LineRef"].isin(
                    [line_name, line_name.replace(" ", "_")]
                )
            )
        ].empty:
            return "Yes"
        return "No"

    def get_avl_requires_attention(
        self, avl_published_status: str, error_in_avl_to_timetable_matching: str
    ) -> str:
        """
        Returns value for 'AVL requires attention' column based on the following logic:
            If both 'AVL Published Status' equal to Yes or 'Error in AVL to Timetable Matching'
            equal to No, then 'AVL requires attention' = No.
            Else
            the 'AVL requires attention' = Yes.

        Args:
            avl_published_status (str): Value of 'AVL Published Status'
            avl_to_timetable__match_status (str): Value of 'Error in AVL to Timetable Matching'

        Returns:
            str: Yes or No for 'AVL requires attention' column
        """
        if (avl_published_status == "Yes") and (
            error_in_avl_to_timetable_matching == "No"
        ):
            return "No"
        return "Yes"

    def get_otc_service_bods_data(self, organisation_id: int) -> None:
        """
        Compares an organisation's OTC Services dictionaries list with
        TXCFileAttributes dictionaries list and the SeasonalService list
        to determine which OTC Services require attention and which
        doesn't ie. not live in BODS at all, or live but meeting new
        Staleness conditions.

        Args:
            organisation_id (int): Organisation ID
        """
        otc_map = get_all_line_level_otc_map(organisation_id)
        service_codes = [service_code for (service_code, line_name) in otc_map]
        txcfa_map = get_line_level_txc_map_service_base(service_codes)
        uncounted_activity_df = get_vehicle_activity_operatorref_linename()

        dq_require_attention_active = flag_is_active(
            "", FeatureFlags.DQS_REQUIRE_ATTENTION.value
        )
        if dq_require_attention_active:
            dq_critical_observations_map = get_dq_critical_observation_services_map(
                txcfa_map
            )

        is_fares_require_attention_active = flag_is_active(
            "", FeatureFlags.FARES_REQUIRE_ATTENTION.value
        )
        if is_fares_require_attention_active:
            fares_dataset_df = get_fares_dataset_map(txcfa_map)

        seasonal_service_map = get_seasonal_service_map(organisation_id)
        service_code_exemption_map = get_service_code_exemption_map(organisation_id)
        naptan_adminarea_df = get_all_naptan_atco_df()
        traveline_region_map_weca = get_all_weca_traveline_region_map()
        services_code = set(otc_map)
        services_code = sorted(services_code)
        abods_registry = AbodsRegistery()
        synced_in_last_month = abods_registry.records()

        for service_code, line_name in services_code:
            service = otc_map.get((service_code, line_name))
            file_attribute = txcfa_map.get((service_code, line_name))
            seasonal_service = seasonal_service_map.get(service_code)
            exemption = service_code_exemption_map.get(service_code)
            is_english_region = False
            traveline_region = ui_lta_name = ""

            if service:
                if service.api_type in [API_TYPE_WECA, API_TYPE_EP]:
                    is_english_region = self.get_is_english_region_weca(
                        service.atco_code, naptan_adminarea_df
                    )
                    traveline_region = traveline_region_map_weca.get(
                        service.atco_code, {"ui_lta_name": "", "region": ""}
                    )
                    ui_lta_name = traveline_region["ui_lta_name"]
                    traveline_region = traveline_region["region"]
                else:
                    (
                        is_english_region,
                        ui_lta_name,
                        traveline_region,
                    ) = self.get_otc_service_details(service, naptan_adminarea_df)

            exempted = False
            if not (
                not (exemption and exemption.registration_code) and is_english_region
            ):
                exempted = True

            dq_require_attention = (
                "Yes"
                if dq_require_attention_active
                and (service_code, line_name) in dq_critical_observations_map
                else "No"
            )

            staleness_status = "Up to date"
            if file_attribute is None:
                require_attention = self._get_require_attention(
                    exempted,
                    seasonal_service,
                    service,
                    None,
                    staleness_status,
                    dq_require_attention,
                )
            elif service and is_stale(service, file_attribute):
                rad = evaluate_staleness(service, file_attribute)
                staleness_status = STALENESS_STATUS[rad.index(True)]
                require_attention = self._get_require_attention(
                    exempted,
                    seasonal_service,
                    service,
                    file_attribute,
                    staleness_status,
                    dq_require_attention,
                )
            else:
                require_attention = dq_require_attention

            if file_attribute is not None:
                avl_published_status = self.get_avl_published_status(
                    file_attribute.national_operator_code,
                    line_name,
                    synced_in_last_month,
                )
                error_in_avl_to_timetable_matching = (
                    self.get_error_in_avl_to_timetable_matching(
                        file_attribute.national_operator_code,
                        line_name,
                        uncounted_activity_df,
                    )
                )
            else:
                avl_published_status = self.get_avl_published_status(
                    "", line_name, synced_in_last_month
                )
                error_in_avl_to_timetable_matching = (
                    self.get_error_in_avl_to_timetable_matching(
                        "", line_name, uncounted_activity_df
                    )
                )

            avl_requires_attention = self.get_avl_requires_attention(
                avl_published_status,
                error_in_avl_to_timetable_matching,
            )

            if is_fares_require_attention_active:
                fares_dataset_id = None
                fares_filename = None
                fares_last_modified_date = None
                fares_operating_period_end_date = None
                fares_data_over_one_year = None
                is_fares_compliant = None

                if file_attribute is not None and not fares_dataset_df.empty:
                    national_operator_code = file_attribute.national_operator_code
                    fares_noc = fares_dataset_df["national_operator_code"]
                    fares_line_name = fares_dataset_df["line_name"]
                    row = fares_dataset_df.loc[
                        (fares_noc == national_operator_code)
                        & (fares_line_name == line_name)
                    ]

                    if not row.empty:
                        row = row.iloc[0]
                        fares_dataset_id = row["dataset_id"]
                        fares_filename = row["xml_file_name"]
                        fares_last_modified_date = row["last_updated_date"].date()
                        fares_operating_period_end_date = row["valid_to"].date()
                        fares_data_over_one_year = fares_last_modified_date + timedelta(
                            days=365
                        )
                        is_fares_compliant = row["is_fares_compliant"]
                        fares_published_status = get_fares_published_status(
                            fares_dataset_id
                        )
                        fares_timeliness_status = get_fares_timeliness_status(
                            fares_operating_period_end_date,
                            fares_last_modified_date,
                        )
                        fares_compliance_status = get_fares_compliance_status(
                            is_fares_compliant
                        )
                else:
                    fares_published_status = get_fares_published_status(
                        fares_dataset_id
                    )
                    fares_timeliness_status = get_fares_timeliness_status(
                        fares_operating_period_end_date,
                        fares_last_modified_date,
                    )
                    fares_compliance_status = get_fares_compliance_status(
                        is_fares_compliant
                    )

                fares_requires_attention = get_fares_requires_attention(
                    fares_published_status,
                    fares_timeliness_status,
                    fares_compliance_status,
                )

                overall_requires_attention = self.get_overall_requires_attention(
                    require_attention,
                    avl_requires_attention,
                    fares_requires_attention,
                    exempted,
                    seasonal_service,
                )
            else:
                fares_dataset_id = UNDER_MAINTENANCE
                fares_filename = UNDER_MAINTENANCE
                fares_last_modified_date = UNDER_MAINTENANCE
                fares_operating_period_end_date = UNDER_MAINTENANCE
                fares_data_over_one_year = UNDER_MAINTENANCE
                fares_published_status = UNDER_MAINTENANCE
                fares_timeliness_status = UNDER_MAINTENANCE
                fares_compliance_status = UNDER_MAINTENANCE
                fares_requires_attention = UNDER_MAINTENANCE

                overall_requires_attention = self.get_overall_requires_attention(
                    require_attention,
                    avl_requires_attention,
                    "No",
                    exempted,
                    seasonal_service,
                )

            if not dq_require_attention_active:
                dq_require_attention = UNDER_MAINTENANCE

            self._update_data(
                service,
                file_attribute,
                seasonal_service,
                exempted,
                staleness_status,
                require_attention,
                traveline_region,
                ui_lta_name,
                line_name,
                avl_published_status,
                error_in_avl_to_timetable_matching,
                avl_requires_attention,
                fares_published_status,
                fares_timeliness_status,
                fares_compliance_status,
                fares_requires_attention,
                fares_dataset_id,
                fares_filename,
                fares_last_modified_date,
                fares_operating_period_end_date,
                fares_data_over_one_year,
                overall_requires_attention,
                dq_require_attention,
            )

    def get_queryset(self):
        self.get_otc_service_bods_data(self._organisation_id)
        return self._object_list
