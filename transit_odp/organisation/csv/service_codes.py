from datetime import datetime, timedelta
from typing import Dict, Optional

from transit_odp.browse.common import (
    LTACSVHelper,
    get_all_naptan_atco_df,
    get_all_weca_traveline_region_map,
)
from transit_odp.common.csv import CSVBuilder, CSVColumn
from transit_odp.organisation.models import TXCFileAttributes
from transit_odp.organisation.models.data import SeasonalService, ServiceCodeExemption
from transit_odp.otc.constants import (
    API_TYPE_WECA,
    OTC_SCOPE_STATUS_IN_SCOPE,
    OTC_SCOPE_STATUS_OUT_OF_SCOPE,
)
from transit_odp.otc.models import Service as OTCService
from transit_odp.publish.requires_attention import (
    evaluate_staleness,
    get_all_line_level_otc_map,
    get_line_level_txc_map,
    is_stale,
)

STALENESS_STATUS = [
    "42 day look ahead is incomplete",
    "Service hasn't been updated within a year",
    "OTC variation not published",
]


def get_42_day_look_ahead_date() -> str:
    # Calculate today's date and the date 42 days from now
    return (datetime.now() + timedelta(days=42)).strftime("%Y-%m-%d")


def get_seasonal_service_status(otc_service: dict) -> str:
    seasonal_service_status = otc_service.get("seasonal_status")
    return "In Season" if seasonal_service_status else "Out of Season"


def get_service_code_exemption_map(
    organisation_id: int,
) -> Dict[str, ServiceCodeExemption]:
    return {
        service.registration_number.replace("/", ":"): service
        for service in ServiceCodeExemption.objects.add_registration_number().filter(
            licence__organisation__id=organisation_id
        )
    }


def get_all_otc_map(organisation_id: int) -> Dict[str, OTCService]:
    """
    Get a dictionary which includes all OTC Services for an organisation.
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
            accessor=lambda otc_service: "Published"
            if otc_service.get("dataset_id")
            else "Unpublished",
        ),
        CSVColumn(
            header="Registration Status",
            accessor=lambda otc_service: "Registered"
            if otc_service.get("otc_licence_number")
            else "Unregistered",
        ),
        CSVColumn(
            header="Scope Status",
            accessor=lambda otc_service: OTC_SCOPE_STATUS_OUT_OF_SCOPE
            if otc_service.get("scope_status", False)
            else OTC_SCOPE_STATUS_IN_SCOPE,
        ),
        CSVColumn(
            header="Seasonal Status",
            accessor=lambda otc_service: get_seasonal_service_status(otc_service)
            if otc_service.get("seasonal_status") is not None
            else "Not Seasonal",
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

    def modify_dataset_line_name(self, line_names: list) -> str:
        return " ".join(line_name for line_name in line_names)

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
        txcfa_map = get_line_level_txc_map(organisation_id)

        seasonal_service_map = get_seasonal_service_map(organisation_id)
        service_code_exemption_map = get_service_code_exemption_map(organisation_id)
        naptan_adminarea_df = get_all_naptan_atco_df()
        traveline_region_map_weca = get_all_weca_traveline_region_map()
        services_code = set(otc_map)
        services_code = sorted(services_code)

        for (service_code, line_name) in services_code:
            service = otc_map.get((service_code, line_name))
            file_attribute = txcfa_map.get((service_code, line_name))
            seasonal_service = seasonal_service_map.get(service_code)
            exemption = service_code_exemption_map.get(service_code)
            is_english_region = False
            traveline_region = ui_lta_name = ""

            if service:
                if service.api_type == API_TYPE_WECA:
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
