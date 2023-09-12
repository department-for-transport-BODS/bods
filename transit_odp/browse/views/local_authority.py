from datetime import timedelta
from typing import Dict, Optional

from django.db.models import Subquery
from django.db.models.functions import Trim
from django.http import HttpResponse
from django.views import View

from transit_odp.browse.views.base_views import BaseListView
from transit_odp.common.csv import CSVBuilder, CSVColumn
from transit_odp.common.views import BaseDetailView
from transit_odp.organisation.models import Organisation, TXCFileAttributes
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


def get_operator_name(otc_service: dict) -> str:
    otc_licence_number = otc_service.get("otc_licence_number")
    operator_name = Organisation.objects.get_organisation_name(otc_licence_number)
    if not operator_name:
        return "Organisation not yet created"
    else:
        return operator_name


def get_all_otc_map_lta(lta_list) -> Dict[str, OTCService]:
    """
    Get a dictionary which includes all OTC Services for an organisation.
    """
    services_subquery_list = [
        x.registration_numbers.values("id")
        for x in lta_list
        if x.registration_numbers.values("id")
    ]

    final_subquery = None
    for service_queryset in services_subquery_list:
        if final_subquery is None:
            final_subquery = service_queryset
        else:
            final_subquery = final_subquery | service_queryset
    final_subquery = final_subquery.distinct()

    return {
        service.registration_number.replace("/", ":"): service
        for service in OTCService.objects.get_all_otc_data_for_lta(final_subquery)
    }


def get_seasonal_service_map(lta_list) -> Dict[str, SeasonalService]:
    """
    Get a dictionary which includes all the Seasonal Services
    for an organisation.
    """
    services_subquery_list = [
        x.registration_numbers.values("id")
        for x in lta_list
        if x.registration_numbers.values("id")
    ]

    final_subquery = None
    for service_queryset in services_subquery_list:
        if final_subquery is None:
            final_subquery = service_queryset
        else:
            final_subquery = final_subquery | service_queryset
    final_subquery = final_subquery.distinct()

    return {
        service.registration_number.replace("/", ":"): service
        for service in SeasonalService.objects.filter(
            licence__organisation__licences__number__in=Subquery(
                final_subquery.values("licence__number")
            )
        )
        .add_registration_number()
        .add_seasonal_status()
    }


def get_service_code_exemption_map(lta_list) -> Dict[str, ServiceCodeExemption]:
    services_subquery_list = [
        x.registration_numbers.values("id")
        for x in lta_list
        if x.registration_numbers.values("id")
    ]

    final_subquery = None
    for service_queryset in services_subquery_list:
        if final_subquery is None:
            final_subquery = service_queryset
        else:
            final_subquery = final_subquery | service_queryset
    final_subquery = final_subquery.distinct()

    return {
        service.registration_number.replace("/", ":"): service
        for service in ServiceCodeExemption.objects.add_registration_number().filter(
            licence__organisation__licences__number__in=Subquery(
                final_subquery.values("licence__number")
            )
        )
    }


class LocalAuthorityView(BaseListView):
    template_name = "browse/local_authority.html"
    model = LocalAuthority
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["updated_result"] = (
            self.get_queryset().values("ui_lta_name_trimmed").distinct().count()
        )
        context["q"] = self.request.GET.get("q", "")
        context["ordering"] = self.request.GET.get("ordering", "ui_lta_name_trimmed")
        all_ltas_current_page = context["object_list"]
        ids_list = {}

        for lta in all_ltas_current_page:
            if lta.ui_lta_name_trimmed not in ids_list:
                ids_list[lta.ui_lta_name_trimmed] = [lta.id]
            else:
                ids_list[lta.ui_lta_name_trimmed].append(lta.id)

        for lta_id_list in ids_list.values():
            for lta in all_ltas_current_page:
                if lta.id in lta_id_list:
                    setattr(lta, "auth_ids", lta_id_list)

                    lta_list = [x for x in all_ltas_current_page if x.id in lta_id_list]
                    otc_qs = OTCService.objects.get_in_scope_in_season_lta_services(
                        lta_list
                    )
                    if otc_qs:
                        context["total_in_scope_in_season_services"] = otc_qs
                    else:
                        context["total_in_scope_in_season_services"] = 0
                    requires_attention_data_qs = get_requires_attention_data_lta(
                        lta_list
                    )
                    if requires_attention_data_qs:
                        context[
                            "total_services_requiring_attention"
                        ] = requires_attention_data_qs
                    else:
                        context["total_services_requiring_attention"] = 0

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

        ltas = {
            "names": list(
                set(
                    [
                        lta.ui_lta_name_trimmed.replace("\xa0", " ")
                        for lta in all_ltas_current_page
                    ]
                )
            )
        }
        context["ltas"] = ltas
        return context

    def get_queryset(self):
        qs = self.model.objects.filter(ui_lta_name__isnull=False).annotate(
            ui_lta_name_trimmed=Trim("ui_lta_name")
        )

        search_term = self.request.GET.get("q", "").strip()
        if search_term:
            qs = qs.filter(ui_lta_name_trimmed__icontains=search_term)

        qs = qs.order_by(*self.get_ordering())
        return qs

    def get_ordering(self):
        ordering = self.request.GET.get("ordering", "ui_lta_name_trimmed")
        if isinstance(ordering, str):
            ordering = (ordering,)
        return ordering


class LocalAuthorityDetailView(BaseDetailView):
    template_name = "browse/local_authority/local_authority_detail.html"
    model = LocalAuthority

    def get_object(self, queryset=None):
        combined_authority_ids = self.request.GET.get("auth_ids")
        if combined_authority_ids:
            combined_authority_ids = [
                int(lta_id.replace("[", "").replace("]", ""))
                for lta_id in combined_authority_ids.split(",")
            ]
        qs = self.model.objects.get(id=combined_authority_ids[0])
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        combined_authority_ids = self.request.GET.get("auth_ids")
        lta_objs = []
        context["auth_ids"] = combined_authority_ids

        if combined_authority_ids:
            combined_authority_ids = [
                int(lta_id.replace("[", "").replace("]", ""))
                for lta_id in combined_authority_ids.split(",")
            ]

        for combined_authority_id in combined_authority_ids:
            lta_objs.append(self.model.objects.get(id=combined_authority_id))

        otc_qs = OTCService.objects.get_in_scope_in_season_lta_services(lta_objs)
        if otc_qs:
            context["total_in_scope_in_season_services"] = otc_qs
        else:
            context["total_in_scope_in_season_services"] = 0

        context["total_services_requiring_attention"] = get_requires_attention_data_lta(
            lta_objs
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
        return self.render_to_response()

    def render_to_response(self):
        lta_objs = []
        combined_authority_ids = self.request.GET.get("auth_ids")

        if combined_authority_ids:
            combined_authority_ids = [
                int(lta_id.replace("[", "").replace("]", ""))
                for lta_id in combined_authority_ids.split(",")
            ]

        for combined_authority_id in combined_authority_ids:
            lta_objs.append(LocalAuthority.objects.get(id=combined_authority_id))

        updated_ui_lta_name = lta_objs[0].ui_lta_name.replace(",", " ").strip()
        csv_filename = (
            f"{updated_ui_lta_name}_detailed service code export detailed export.csv"
        )
        csv_export = LTACSV(lta_objs)
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
            accessor=lambda otc_service: get_operator_name(otc_service)
            if otc_service.get("operator_name") is None
            or otc_service.get("operator_name") == ""
            else otc_service.get("operator_name"),
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

    def get_otc_service_bods_data(self, lta_list) -> None:
        """
        Compares an LTA's OTC Services dictionaries list with
        TXCFileAttributes dictionaries list and the SeasonalService list
        to determine which OTC Services require attention and which
        doesn't ie. not live in BODS at all, or live but meeting new
        Staleness conditions.
        """
        otc_map = get_all_otc_map_lta(lta_list)
        txcfa_map = get_txc_map_lta(lta_list)
        seasonal_service_map = get_seasonal_service_map(lta_list)
        service_code_exemption_map = get_service_code_exemption_map(lta_list)
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
        self.get_otc_service_bods_data(self._combined_authorities)
        return self._object_list
