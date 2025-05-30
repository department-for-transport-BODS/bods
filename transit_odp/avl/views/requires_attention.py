from django_tables2 import SingleTableView
from waffle import flag_is_active

from transit_odp.avl.tables import AVLRequiresAttentionTable
from transit_odp.browse.common import get_in_scope_in_season_services_line_level
from transit_odp.common.constants import FeatureFlags
from transit_odp.organisation.models.organisations import Organisation
from transit_odp.organisation.models.report import ComplianceReport
from transit_odp.otc.models import Service as OTCService
from transit_odp.publish.requires_attention import (
    get_avl_requires_attention_line_level_data,
)
from transit_odp.users.views.mixins import OrgUserViewMixin


class AVLRequiresAttentionView(OrgUserViewMixin, SingleTableView):
    template_name = "avl/requires_attention.html"
    model = OTCService
    table_class = AVLRequiresAttentionTable
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org_id = self.kwargs["pk1"]
        context["org_id"] = org_id
        data_owner = self.organisation.name if self.request.user.is_agent_user else "My"
        context["ancestor"] = f"Review {data_owner} Bus Location Data"
        is_operator_prefetch_sra_active = flag_is_active(
            "", FeatureFlags.OPERATOR_PREFETCH_SRA.value
        )

        if is_operator_prefetch_sra_active:
            org_object = Organisation.objects.filter(id=org_id).first()
            total_inscope = org_object.total_inscope
            services_requiring_attention = org_object.avl_sra
        else:
            total_inscope = len(get_in_scope_in_season_services_line_level(org_id))
            services_requiring_attention = len(self.object_list)

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
                .filter(licence_organisation_id=org_id, avl_requires_attention="Yes")
                .order_by("otc_licence_number", "service_number")
                .values()
            )
        else:
            return get_avl_requires_attention_line_level_data(org_id)
