from datetime import timedelta
from math import ceil
from typing import Dict, Optional

from django.db.models import Case, CharField, Subquery, Value, When
from django.http import HttpResponse
from django.views import View

from transit_odp.browse.lta_constants import LTAS_DICT
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
        context["object_list"] = self.object_list_lta_mapping(context["object_list"])
        context["q"] = self.request.GET.get("q", "")
        context["ordering"] = self.request.GET.get("ordering", "mapped_name")
        all_ltas_current_page = context["object_list"]

        for lta in all_ltas_current_page:
            otc_qs = OTCService.objects.get_in_scope_in_season_lta_services(lta)
            if otc_qs:
                context["total_in_scope_in_season_services"] = otc_qs.count()
            else:
                context["total_in_scope_in_season_services"] = 0
            context["total_services_requiring_attention"] = len(
                get_requires_attention_data_lta(lta)
            )
            try:
                context["services_require_attention_percentage"] = ceil(
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

            context["ltas"] = {"names": lta.name}
        return context

    def object_list_lta_mapping(self, object_list):
        new_object_list = []
        for lta_object in object_list:
            for otc_name, value_name in LTAS_DICT.items():
                if lta_object.name == otc_name:
                    lta_object.name = value_name
                    new_object_list.append(lta_object)
        return new_object_list

    def get_queryset(self):
        lta_name_list = list(LTAS_DICT.keys())
        qs = self.model.objects.filter(name__in=lta_name_list)
        # Add annotated field "mapped_name"
        qs = qs.annotate(
            mapped_name=Case(
                *[
                    When(name=name, then=Value(mapped_name, output_field=CharField()))
                    for name, mapped_name in LTAS_DICT.items()
                ],
                default=Value("", output_field=CharField()),
            )
        )
        search_term = self.request.GET.get("q", "").strip()
        if search_term:
            qs = qs.filter(mapped_name__icontains=search_term)

        qs = qs.order_by(*self.get_ordering())
        return qs

    def get_ordering(self):
        ordering = self.request.GET.get("ordering", "mapped_name")
        if ordering == "mapped_name":
            ordering = ("mapped_name",)
        elif isinstance(ordering, str):
            ordering = (ordering,)
        return ordering


class LocalAuthorityDetailView(BaseDetailView):
    template_name = "browse/local_authority/local_authority_detail.html"
    model = LocalAuthority

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        local_authority = self.lta_name_mapping(self.object)
        otc_qs = OTCService.objects.get_in_scope_in_season_lta_services(local_authority)
        if otc_qs:
            context["total_in_scope_in_season_services"] = otc_qs.count()
        else:
            context["total_in_scope_in_season_services"] = 0

        context["total_services_requiring_attention"] = len(
            get_requires_attention_data_lta(local_authority)
        )

        try:
            context["services_require_attention_percentage"] = ceil(
                100
                * (
                    context["total_services_requiring_attention"]
                    / context["total_in_scope_in_season_services"]
                )
            )
        except ZeroDivisionError:
            context["services_require_attention_percentage"] = 0

        return context

    def lta_name_mapping(self, lta_object):
        for otc_name, value_name in LTAS_DICT.items():
            if lta_object.name == otc_name:
                lta_object.name = value_name
        return lta_object


class LocalAuthorityExportView(View):
    def get(self, *args, **kwargs):
        self.lta = LocalAuthority.objects.get(id=kwargs["pk"])
        return self.render_to_response()

    def lta_name_mapping(self):
        for otc_name, value_name in LTAS_DICT.items():
            if self.lta.name == otc_name:
                self.lta.name = value_name
        return self.lta

    def render_to_response(self):
        lta = self.lta_name_mapping()
        csv_filename = f"{lta.name}_detailed service code export detailed export.csv"
        csv_export = LTACSV(lta)
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

    def __init__(self, lta):
        self._lta = lta
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
        self.get_otc_service_bods_data(self._lta)
        return self._object_list
