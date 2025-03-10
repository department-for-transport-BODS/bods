from typing import Dict, List, TypedDict

from django.http import HttpResponseRedirect
from django.views.generic import FormView
from django_hosts import reverse
from django_tables2 import SingleTableView
from waffle import flag_is_active

from config.hosts import PUBLISH_HOST
from transit_odp.common.constants import FeatureFlags
from transit_odp.common.views import BaseTemplateView
from transit_odp.organisation.constants import AVLType, FaresType, TimetableType
from transit_odp.publish.forms import SelectDataTypeForm
from transit_odp.publish.requires_attention import (
    FaresRequiresAttention,
    get_avl_requires_attention_line_level_data,
    get_requires_attention_line_level_data,
)
from transit_odp.publish.tables import AgentOrganisationsTable
from transit_odp.users.models import User
from transit_odp.users.views.mixins import OrgUserViewMixin

NAMESPACE_LOOKUP: Dict[int, str] = {
    TimetableType: "",
    AVLType: "avl:",
    FaresType: "fares:",
}


class PublishSelectDataTypeView(OrgUserViewMixin, BaseTemplateView, FormView):
    template_name = "publish/publish_select_type.html"
    form_class = SelectDataTypeForm

    def form_valid(self, form):
        org_id = self.kwargs["pk1"]
        selected_dataset_type = int(form.data.get("dataset_type"))
        namespace = NAMESPACE_LOOKUP.get(selected_dataset_type, "")
        url = reverse(
            namespace + "new-feed",
            kwargs={"pk1": org_id},
            host=PUBLISH_HOST,
        )
        return HttpResponseRedirect(url)


class SelectOrgView(OrgUserViewMixin, BaseTemplateView):
    template_name = "publish/select_org.html"

    class Context(TypedDict):
        organisations: List
        page_title: str
        view: "SelectOrgView"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organisations = self.request.user.organisations.all().order_by("name")
        context = self.Context(
            page_title="Operator Dashboard", organisations=organisations, **context
        )
        return context


class AgentDashboardView(OrgUserViewMixin, SingleTableView):
    """
    View for Agent Dashboard.
    """

    template_name = "publish/agent_dashboard.html"
    model = User.organisations.through
    table_class = AgentOrganisationsTable
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        users = self.model.objects.filter(user=self.request.user)
        context["is_complete_service_pages_active"] = flag_is_active(
            "", FeatureFlags.COMPLETE_SERVICE_PAGES.value
        )

        if users:
            org_names = {"names": [user.organisation.name for user in users]}
        else:
            org_names = {"names": []}

        context["org_names"] = org_names
        return context

    def get_queryset(self):
        qs = self.model.objects.filter(user=self.request.user)

        search_term = self.request.GET.get("q", "").strip()
        if search_term:
            qs = qs.filter(organisation__name__icontains=search_term)

        return qs

    def get_table_data(self):
        next_page = self.request.GET.get("next", "feed-list")
        prev_page = self.request.GET.get("prev")
        # Each record requires a separate request to the database which is in no way
        # ideal. We need to rethink the data model, possibly making the otc licence and
        # the organisation licence a foreign key.
        return [
            {
                "next": reverse(
                    next_page, args=[record.organisation_id], host=PUBLISH_HOST
                )
                + (f"?prev={prev_page}" if prev_page is not None else ""),
                "organisation_id": record.organisation_id,
                "organisation": record.organisation.name,
                "requires_attention": len(
                    get_requires_attention_line_level_data(record.organisation_id)
                ),
                "avl_requires_attention": len(
                    get_avl_requires_attention_line_level_data(record.organisation_id)
                ),
                "fares_requires_attention": len(
                    FaresRequiresAttention(
                        record.organisation_id
                    ).get_fares_requires_attention_line_level_data()
                ),
            }
            for record in self.get_queryset()
        ]
