from django_tables2 import SingleTableView

from transit_odp.avl.tables import AVLRequiresAttentionTable
from transit_odp.browse.common import get_in_scope_in_season_services_line_level
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
        context["services_requiring_attention"] = len(self.object_list)
        context["total_in_scope_in_season_services"] = len(
            get_in_scope_in_season_services_line_level(org_id)
        )
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
        return get_avl_requires_attention_line_level_data(org_id)
