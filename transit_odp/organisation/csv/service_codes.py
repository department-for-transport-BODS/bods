from datetime import timedelta
from typing import Dict, Optional

from transit_odp.common.csv import CSVBuilder, CSVColumn
from transit_odp.organisation.models import TXCFileAttributes
from transit_odp.organisation.models.data import SeasonalService, ServiceCodeExemption
from transit_odp.otc.models import Service as OTCService
from transit_odp.publish.requires_attention import (
    evaluate_staleness,
    get_txc_map,
    is_stale,
)

STALENESS_STATUS = [
    "Stale - 42 day look ahead",
    "Stale - 12 months old",
    "Stale - OTC Variation",
]


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


class ServiceCodesCSV(CSVBuilder):
    columns = [
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
            header="OTC Status",
            accessor=lambda otc_service: "Registered"
            if otc_service.get("otc_licence_number")
            else "Unregistered",
        ),
        CSVColumn(
            header="Scope Status",
            accessor=lambda otc_service: "Out of Scope"
            if otc_service.get("scope_status")
            else "In Scope",
        ),
        CSVColumn(
            header="Seasonal Status",
            accessor=lambda otc_service: get_seasonal_service_status(otc_service)
            if otc_service.get("seasonal_status") is not None
            else "Not Seasonal",
        ),
        CSVColumn(
            header="Staleness Status",
            accessor=lambda otc_service: otc_service.get("staleness_status"),
        ),
        CSVColumn(
            header="Data set Licence Number",
            accessor=lambda otc_service: otc_service.get("licence_number"),
        ),
        CSVColumn(
            header="Data set Service Code",
            accessor=lambda otc_service: otc_service.get("service_code"),
        ),
        CSVColumn(
            header="Data set Line Name",
            accessor=lambda otc_service: otc_service.get("line_name"),
        ),
        CSVColumn(
            header="OTC Licence Number",
            accessor=lambda otc_service: otc_service.get("otc_licence_number"),
        ),
        CSVColumn(
            header="OTC Registration Number",
            accessor=lambda otc_service: otc_service.get("otc_registration_number"),
        ),
        CSVColumn(
            header="OTC Service Number",
            accessor=lambda otc_service: otc_service.get("otc_service_number"),
        ),
        CSVColumn(
            header="Data set Revision Number",
            accessor=lambda otc_service: otc_service.get("revision_number"),
        ),
        CSVColumn(
            header="Last Modified Date",
            accessor=lambda otc_service: otc_service.get("last_modified_date"),
        ),
        CSVColumn(
            header="Effective Last Modified Date",
            accessor=lambda otc_service: otc_service.get("last_modified_date"),
        ),
        CSVColumn(
            header="Operating Period Start Date",
            accessor=lambda otc_service: otc_service.get("operating_period_start_date"),
        ),
        CSVColumn(
            header="Operating Period End Date",
            accessor=lambda otc_service: otc_service.get("operating_period_end_date"),
        ),
        CSVColumn(
            header="XML Filename",
            accessor=lambda otc_service: otc_service.get("xml_filename"),
        ),
        CSVColumn(
            header="Dataset ID",
            accessor=lambda otc_service: otc_service.get("dataset_id"),
        ),
        CSVColumn(
            header="Effective Seasonal Start Date",
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
            header="Effective stale date due to end date",
            accessor=lambda otc_service: otc_service.get(
                "effective_stale_date_end_date"
            ),
        ),
        CSVColumn(
            header="Effective stale date due to Effective last modified date",
            accessor=lambda otc_service: otc_service.get(
                "effective_stale_date_last_modified_date"
            ),
        ),
        CSVColumn(
            header="Last modified date < Effective stale "
            "date due to OTC effective date",
            accessor=lambda otc_service: otc_service.get(
                "last_modified_lt_effective_stale_date_otc"
            ),
        ),
        CSVColumn(
            header="Effective stale date due to OTC effective date",
            accessor=lambda otc_service: otc_service.get(
                "effective_stale_date_otc_effective_date"
            ),
        ),
    ]

    def __init__(self, organisation_id: int):
        self._organisation_id = organisation_id
        self._object_list = []

    def _update_data(
        self,
        service: Optional[OTCService],
        file_attribute: Optional[TXCFileAttributes],
        seasonal_service: Optional[SeasonalService],
        exemption: Optional[ServiceCodeExemption],
        staleness_status: Optional[str],
        require_attention: str,
    ) -> None:
        self._object_list.append(
            {
                "require_attention": require_attention,
                "scope_status": exemption and exemption.registration_number,
                "otc_licence_number": service and service.otc_licence_number,
                "otc_registration_number": service and service.registration_number,
                "otc_service_number": service and service.service_number,
                "licence_number": file_attribute and file_attribute.licence_number,
                "service_code": file_attribute and file_attribute.service_code,
                "line_name": file_attribute
                and self.modify_dataset_line_name(file_attribute.line_names),
                "revision_number": file_attribute and file_attribute.revision_number,
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
                "effective_stale_date_end_date": file_attribute
                and file_attribute.effective_stale_date_end_date,
                "effective_stale_date_last_modified_date": file_attribute
                and file_attribute.effective_stale_date_last_modified_date,
                "last_modified_lt_effective_stale_date_otc": service
                and file_attribute
                and (
                    file_attribute.modification_datetime.date()
                    < service.effective_stale_date_otc_effective_date
                ),
                "effective_stale_date_otc_effective_date": service
                and (service.effective_stale_date_otc_effective_date),
            }
        )

    def modify_dataset_line_name(self, line_names: list) -> str:
        return " ".join(line_name for line_name in line_names)

    def _get_require_attention(
        self,
        exemption: Optional[ServiceCodeExemption],
        seasonal_service: Optional[SeasonalService],
    ) -> str:
        if exemption or (seasonal_service and not seasonal_service.seasonal_status):
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
        otc_map = get_all_otc_map(organisation_id)
        txcfa_map = get_txc_map(organisation_id)
        seasonal_service_map = get_seasonal_service_map(organisation_id)
        service_code_exemption_map = get_service_code_exemption_map(organisation_id)
        services_code = set(otc_map)
        services_code.update(set(txcfa_map))
        services_code = sorted(services_code)

        for service_code in services_code:
            service = otc_map.get(service_code)
            file_attribute = txcfa_map.get(service_code)
            seasonal_service = seasonal_service_map.get(service_code)
            exemption = service_code_exemption_map.get(service_code)

            staleness_status = "Not Stale"
            if file_attribute is None:
                require_attention = self._get_require_attention(
                    exemption, seasonal_service
                )
            elif service and is_stale(service, file_attribute):
                rad = evaluate_staleness(service, file_attribute)
                staleness_status = STALENESS_STATUS[rad.index(True)]
                require_attention = self._get_require_attention(
                    exemption, seasonal_service
                )
            else:
                require_attention = "No"
            self._update_data(
                service,
                file_attribute,
                seasonal_service,
                exemption,
                staleness_status,
                require_attention,
            )

    def get_queryset(self):
        self.get_otc_service_bods_data(self._organisation_id)
        return self._object_list
