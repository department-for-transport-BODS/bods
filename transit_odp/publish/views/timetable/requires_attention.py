from django.http import HttpResponse
from django.utils.timezone import now
from django.views import View
from django_tables2 import SingleTableView
from waffle import flag_is_active

from transit_odp.browse.common import get_in_scope_in_season_services_line_level
from transit_odp.common.constants import FeatureFlags
from transit_odp.organisation.csv.service_codes import (
    ComplianceReportCSV,
    ComplianceReportDBCSV,
    ServiceCodesCSV,
)
from transit_odp.organisation.models import Organisation
from transit_odp.organisation.models.report import ComplianceReport
from transit_odp.otc.models import Service as OTCService
from transit_odp.publish.requires_attention import (
    get_requires_attention_line_level_data,
)
from transit_odp.timetables.tables import RequiresAttentionTable
from transit_odp.users.views.mixins import OrgUserViewMixin


class RequiresAttentionView(OrgUserViewMixin, SingleTableView):
    template_name = "publish/requires_attention.html"
    model = OTCService
    table_class = RequiresAttentionTable
    paginate_by = 10

    def get_context_data(self, **kwargs):
        is_avl_require_attention_active = flag_is_active(
            "", "is_avl_require_attention_active"
        )
        context = super().get_context_data(**kwargs)
        org_id = self.kwargs["pk1"]
        context["org_id"] = org_id
        data_owner = self.organisation.name if self.request.user.is_agent_user else "My"

        context["is_avl_require_attention_active"] = is_avl_require_attention_active
        context["ancestor"] = f"Review {data_owner} Timetables Data"
        is_operator_prefetch_active = flag_is_active(
            "", FeatureFlags.OPERATOR_PREFETCH_SRA.value
        )

        if is_operator_prefetch_active:
            org_object = Organisation.objects.filter(id=org_id).first()
            total_inscope = org_object.total_inscope
            services_requiring_attention = org_object.timetable_sra
        else:
            services_requiring_attention = len(self.object_list)
            total_inscope = len(get_in_scope_in_season_services_line_level(org_id))

        context["services_requiring_attention"] = services_requiring_attention
        context["total_in_scope_in_season_services"] = total_inscope
        try:
            context["services_require_attention_percentage"] = round(
                100
                * (
                    context["services_requiring_attention"]
                    / context["total_in_scope_in_season_services"]
                )
            )
        except ZeroDivisionError:
            context["services_require_attention_percentage"] = 0

        context["q"] = self.request.GET.get("q", "").strip()
        return context

    def get_table_data(self):
        keywords = self.request.GET.get("q", "").strip().lower()
        if keywords:
            return [
                service
                for service in self.object_list
                if keywords in service["licence_number"].lower()
                or keywords in service["service_code"].lower()
                or keywords in service["line_number"].lower()
            ]
        return self.object_list

    def get_queryset(self):
        org_id = self.kwargs["pk1"]
        is_prefetch_compliance_report = flag_is_active(
            "", FeatureFlags.PREFETCH_DATABASE_COMPLIANCE_REPORT.value
        )

        if is_prefetch_compliance_report:
            return (
                ComplianceReport.objects.extra(
                    select={
                        "licence_number": "otc_licence_number",
                        "service_code": "registration_number",
                        "line_number": "service_number",
                    }
                )
                .filter(licence_organisation_id=org_id, requires_attention="Yes")
                .order_by("otc_licence_number", "service_number")
                .values()
            )
        else:
            return get_requires_attention_line_level_data(org_id)


class ServiceCodeView(View):
    def get(self, *args, **kwargs):
        self.org = Organisation.objects.get(id=kwargs["pk1"])
        return self.render_to_response()

    def render_to_response(self):
        csv_filename = (
            f"{now():%d%m%y}_timetables_datastatus_by_service_code_"
            f"{self.org.name}.csv"
        )
        csv_export = ServiceCodesCSV(self.org.id)
        file_ = csv_export.to_string()
        response = HttpResponse(file_, content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={csv_filename}"
        return response


class ComplianceReportView(View):
    def get(self, *args, **kwargs):
        self.org = Organisation.objects.get(id=kwargs["pk1"])
        return self.render_to_response()

    def render_to_response(self):
        csv_filename = f"{self.org.name} compliance report.csv"
        is_prefetch_db_compliance_report_active = flag_is_active(
            "", FeatureFlags.PREFETCH_DATABASE_COMPLIANCE_REPORT.value
        )
        if is_prefetch_db_compliance_report_active:
            csv_export = ComplianceReportDBCSV(self.org.id)
        else:
            csv_export = ComplianceReportCSV(self.org.id)
        file_ = csv_export.to_string()
        response = HttpResponse(file_, content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={csv_filename}"
        return response
