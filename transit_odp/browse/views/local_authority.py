from datetime import timedelta
from typing import Dict, Optional

from django.db.models import Subquery, Count

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

from datetime import timedelta
from transit_odp.browse.lta_column_headers import header_accessor_data

STALENESS_STATUS = [
    "42 day look ahead is incomplete",
    "Service hasn't been updated within a year",
    "OTC variation not published",
]


def create_columns(header_accessor_list):
    columns = [
        CSVColumn(header=header, accessor=accessor)
        for header, accessor in header_accessor_list
    ]
    return columns


def get_all_otc_map_lta(lta_list) -> Dict[str, OTCService]:
    """
    Get a dictionary which includes all OTC Services for an organisation.
    """
    services_subquery_list = [
        x.registration_numbers.values("id")
        for x in lta_list
        if x.registration_numbers.values("id")
    ]

    if services_subquery_list:
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
    else:
        return {}


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
    if services_subquery_list:
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
    else:
        return {}


def get_service_code_exemption_map(lta_list) -> Dict[str, ServiceCodeExemption]:
    services_subquery_list = [
        x.registration_numbers.values("id")
        for x in lta_list
        if x.registration_numbers.values("id")
    ]

    if services_subquery_list:
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
    else:
        return {}


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
            lta_list = (
                self.model.objects.annotate(ui_lta_name_trimmed=Trim("ui_lta_name"))
                .filter(ui_lta_name_trimmed=lta.ui_lta_name_trimmed)
                .all()
            )
            setattr(lta, "auth_ids", [x.id for x in lta_list])

            otc_qs = OTCService.objects.get_in_scope_in_season_lta_services(lta_list)
            if otc_qs:
                context["total_in_scope_in_season_services"] = otc_qs
            else:
                context["total_in_scope_in_season_services"] = 0
            requires_attention_data_qs = get_requires_attention_data_lta(lta_list)
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

        names = []
        name_set = set()

        all_ltas = self.get_queryset()
        for lta in all_ltas:
            cleaned_name = lta.ui_lta_name_trimmed.replace("\xa0", " ")
            if cleaned_name not in name_set:
                names.append(cleaned_name)
                name_set.add(cleaned_name)

        ltas = {"names": names}
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
        return qs.distinct("ui_lta_name_trimmed")

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
    columns = create_columns(header_accessor_data)

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
                "national_operator_code": file_attribute
                and file_attribute.national_operator_code,
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

            staleness_status = "Up to date"
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
