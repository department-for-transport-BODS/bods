from collections import OrderedDict
from datetime import timedelta
from typing import Dict, Optional

from django.db.models import Subquery
from django.db.models.functions import Trim
from django.http import HttpResponse
from django.views import View

from transit_odp.browse.views.base_views import BaseListView
from transit_odp.common.csv import CSVBuilder, CSVColumn
from transit_odp.common.views import BaseDetailView
from transit_odp.organisation.models import TXCFileAttributes
from transit_odp.organisation.models.data import SeasonalService, ServiceCodeExemption
from transit_odp.otc.models import LocalAuthority
from transit_odp.otc.models import Service as OTCService
from transit_odp.publish.requires_attention import (
    evaluate_staleness,
    get_requires_attention_data_lta,
    get_txc_map_lta,
    is_stale,
)

STALENESS_STATUS = [
    "Stale - End date passed",
    "Stale - 12 months old",
    "Stale - OTC Variation",
]

COMBINED_AUTHORITY_DICT = OrderedDict()


def get_seasonal_service_status(otc_service: dict) -> str:
    seasonal_service_status = otc_service.get("seasonal_status")
    return "In Season" if seasonal_service_status else "Out of Season"


def get_all_otc_map_lta(lta) -> Dict[str, OTCService]:
    """
    Get a dictionary which includes all OTC Services for an organisation.
    """
    return {
        service.registration_number.replace("/", ":"): service
        for service in OTCService.objects.get_all_otc_data_for_lta(lta)
    }


def get_seasonal_service_map(lta) -> Dict[str, SeasonalService]:
    """
    Get a dictionary which includes all the Seasonal Services
    for an organisation.
    """
    services_subquery = lta.registration_numbers.values("id")
    return {
        service.registration_number.replace("/", ":"): service
        for service in SeasonalService.objects.filter(
            licence__organisation__licences__number__in=Subquery(
                services_subquery.values("licence__number")
            )
        )
        .add_registration_number()
        .add_seasonal_status()
    }


def get_service_code_exemption_map(lta) -> Dict[str, ServiceCodeExemption]:
    services_subquery = lta.registration_numbers.values("id")
    return {
        service.registration_number.replace("/", ":"): service
        for service in ServiceCodeExemption.objects.add_registration_number().filter(
            licence__organisation__licences__number__in=Subquery(
                services_subquery.values("licence__number")
            )
        )
    }


class LocalAuthorityView(BaseListView):
    template_name = "browse/local_authority.html"
    model = LocalAuthority
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        context["ordering"] = self.request.GET.get("ordering", "ui_lta_name").strip()
        all_ltas_current_page = context["object_list"]
        ids_list = {}

        for lta in all_ltas_current_page:
            otc_qs = OTCService.objects.get_in_scope_in_season_lta_services(lta)
            if otc_qs:
                context["total_in_scope_in_season_services"] = otc_qs.count()
            else:
                context["total_in_scope_in_season_services"] = 0
            setattr(
                lta,
                "total_in_scope_in_season_services",
                context["total_in_scope_in_season_services"],
            )
            context["total_services_requiring_attention"] = len(
                get_requires_attention_data_lta(lta)
            )
            try:
                context["services_require_attention_percentage"] = round(
                    100
                    * (
                        context["total_services_requiring_attention"]
                        / context["total_in_scope_in_season_services"]
                    )
                )
            except ZeroDivisionError:
                context["services_require_attention_percentage"] = 0
            setattr(
                lta,
                "services_require_attention_percentage",
                context["services_require_attention_percentage"],
            )

            if lta.ui_lta_name.strip() not in ids_list:
                ids_list[lta.ui_lta_name.strip()] = [lta.id]
            else:
                ids_list[lta.ui_lta_name.strip()].append(lta.id)

        all_ltas_current_page = self.combined_authorities_check(
            all_ltas_current_page, ids_list
        )

        ltas = {
            "names": list(
                set([lta.ui_lta_name.strip() for lta in all_ltas_current_page])
            )
        }
        context["ltas"] = ltas
        return context

    def combined_authorities_check(self, all_ltas_current_page, ids_dict):
        COMBINED_AUTHORITY_DICT.clear()

        for current_lta in all_ltas_current_page:
            for lta in ids_dict.values():
                if len(lta) > 1:
                    for lta_id in lta:
                        if current_lta.id == lta_id:
                            if (
                                current_lta.ui_lta_name.strip()
                                not in COMBINED_AUTHORITY_DICT
                            ):
                                COMBINED_AUTHORITY_DICT[current_lta.ui_lta_name] = {
                                    "ids": [lta_id],
                                    "services_require_attention_percentage": [
                                        current_lta.services_require_attention_percentage
                                    ],
                                    "total_in_scope_in_season_services": [
                                        current_lta.total_in_scope_in_season_services
                                    ],
                                }
                            else:
                                COMBINED_AUTHORITY_DICT[
                                    current_lta.ui_lta_name.strip()
                                ]["ids"].append(lta_id)
                                COMBINED_AUTHORITY_DICT[
                                    current_lta.ui_lta_name.strip()
                                ]["services_require_attention_percentage"].append(
                                    current_lta.services_require_attention_percentage
                                )
                                COMBINED_AUTHORITY_DICT[
                                    current_lta.ui_lta_name.strip()
                                ]["total_in_scope_in_season_services"].append(
                                    current_lta.total_in_scope_in_season_services
                                )

        return self.set_stats(COMBINED_AUTHORITY_DICT, all_ltas_current_page)

    def set_stats(self, combined_authority_dict, all_ltas_current_page):
        for current_lta in all_ltas_current_page:
            for ui_lta_name, values in combined_authority_dict.items():
                if current_lta.ui_lta_name == ui_lta_name:
                    current_lta.services_require_attention_percentage = int(
                        sum(values["services_require_attention_percentage"])
                        / len(values["services_require_attention_percentage"])
                    )
                    combined_authority_dict[current_lta.ui_lta_name.strip()][
                        "updated_services_require_attention_percentage"
                    ] = current_lta.services_require_attention_percentage

                    current_lta.total_in_scope_in_season_services = sum(
                        values["total_in_scope_in_season_services"]
                    )
                    combined_authority_dict[current_lta.ui_lta_name.strip()][
                        "updated_total_in_scope_in_season_services"
                    ] = current_lta.total_in_scope_in_season_services

        self.request.session["combined_authority_dict"] = combined_authority_dict

        return all_ltas_current_page

    def get_queryset(self):
        qs = self.model.objects.all()

        qs = qs.annotate(lta_name=Trim("ui_lta_name"))

        search_term = self.request.GET.get("q", "").strip()
        if search_term:
            qs = qs.filter(lta_name__icontains=search_term)

        qs = qs.order_by(*self.get_ordering())
        return qs

    def get_ordering(self):
        ordering = self.request.GET.get("ordering", "lta_name").strip()
        if isinstance(ordering, str):
            ordering = (ordering,)
        return ordering


class LocalAuthorityDetailView(BaseDetailView):
    template_name = "browse/local_authority/local_authority_detail.html"
    model = LocalAuthority

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        local_authority = self.object
        combined_authority_dict = self.request.session.get("combined_authority_dict")

        if combined_authority_dict.values():
            for combined_authority in combined_authority_dict.values():
                if local_authority.id in combined_authority["ids"]:
                    context["total_in_scope_in_season_services"] = combined_authority[
                        "updated_total_in_scope_in_season_services"
                    ]
                    context[
                        "services_require_attention_percentage"
                    ] = combined_authority[
                        "updated_services_require_attention_percentage"
                    ]
                else:
                    otc_qs = OTCService.objects.get_in_scope_in_season_lta_services(
                        local_authority
                    )
                    if otc_qs:
                        context["total_in_scope_in_season_services"] = otc_qs.count()
                    else:
                        context["total_in_scope_in_season_services"] = 0

                    context["total_services_requiring_attention"] = len(
                        get_requires_attention_data_lta(local_authority)
                    )

                    try:
                        context["services_require_attention_percentage"] = round(
                            100
                            * (
                                context["total_services_requiring_attention"]
                                / context["total_in_scope_in_season_services"]
                            )
                        )
                    except ZeroDivisionError:
                        context["services_require_attention_percentage"] = 0
        else:
            otc_qs = OTCService.objects.get_in_scope_in_season_lta_services(
                local_authority
            )
            if otc_qs:
                context["total_in_scope_in_season_services"] = otc_qs.count()
            else:
                context["total_in_scope_in_season_services"] = 0

            context["total_services_requiring_attention"] = len(
                get_requires_attention_data_lta(local_authority)
            )

            try:
                context["services_require_attention_percentage"] = round(
                    100
                    * (
                        context["total_services_requiring_attention"]
                        / context["total_in_scope_in_season_services"]
                    )
                )
            except ZeroDivisionError:
                context["services_require_attention_percentage"] = 0

        return context


class LocalAuthorityExportView(View):
    def get(self, *args, **kwargs):
        self.lta = LocalAuthority.objects.get(id=kwargs["pk"])
        self.combined_authority_dict = self.request.session.get(
            "combined_authority_dict"
        )
        return self.render_to_response()

    def render_to_response(self):
        lta = self.lta
        combined_authority_dict = self.combined_authority_dict
        combined_authorities = []
        updated_ui_lta_name = lta.ui_lta_name.replace(",", " ").strip()
        csv_filename = (
            f"{updated_ui_lta_name}_detailed service code export detailed export.csv"
        )

        if combined_authority_dict.values():
            for combined_authority in combined_authority_dict.values():
                if lta.id in combined_authority["ids"]:
                    combined_authorities = [
                        LocalAuthority.objects.get(id=lta_id)
                        for lta_id in combined_authority["ids"]
                    ]
                    break
                else:
                    combined_authorities = [lta]
        csv_export = LTACSV(combined_authorities)
        file_ = csv_export.to_string()
        response = HttpResponse(file_, content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={csv_filename}"
        return response


class LTACSV(CSVBuilder):
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
            header="Operator Name",
            accessor=lambda otc_service: otc_service.get("operator_name"),
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
            accessor=lambda otc_service: otc_service.get("line_number"),
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
            header="Last modified date < Effective "
            "stale date due to OTC effective date",
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
                "operator_name": file_attribute and file_attribute.organisation_name,
                "licence_number": file_attribute and file_attribute.licence_number,
                "service_code": file_attribute and file_attribute.service_code,
                "line_name": file_attribute
                and self.modify_dataset_line_name(file_attribute.line_names),
                "operating_period_start_date": file_attribute
                and (file_attribute.operating_period_start_date),
                "operating_period_end_date": file_attribute
                and (file_attribute.operating_period_end_date),
                "revision_number": file_attribute and file_attribute.revision_number,
                "last_modified_date": file_attribute
                and (file_attribute.modification_datetime.date()),
                "dataset_id": file_attribute and file_attribute.revision.dataset_id,
                "xml_filename": file_attribute and file_attribute.filename,
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

    def __init__(self, combined_authorities):
        self._combined_authorities = combined_authorities
        self._object_list = []

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

    def get_otc_service_bods_data(self, lta) -> None:
        """
        Compares an LTA's OTC Services dictionaries list with
        TXCFileAttributes dictionaries list and the SeasonalService list
        to determine which OTC Services require attention and which
        doesn't ie. not live in BODS at all, or live but meeting new
        Staleness conditions.
        """
        otc_map = get_all_otc_map_lta(lta)
        txcfa_map = get_txc_map_lta(lta)
        seasonal_service_map = get_seasonal_service_map(lta)
        service_code_exemption_map = get_service_code_exemption_map(lta)
        services_code = set(otc_map)
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
        for lta in self._combined_authorities:
            self.get_otc_service_bods_data(lta)
        return self._object_list
