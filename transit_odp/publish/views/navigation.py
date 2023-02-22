from typing import Dict, List, TypedDict

from django.http import HttpResponseRedirect
from django.views.generic import FormView
from django_hosts import reverse
from django_tables2 import SingleTableView

from config.hosts import PUBLISH_HOST
from transit_odp.common.views import BaseTemplateView
from transit_odp.organisation.constants import AVLType, FaresType, TimetableType
from transit_odp.publish.forms import SelectDataTypeForm
from transit_odp.publish.requires_attention import get_requires_attention_data
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
    template_name = "publish/agent_dashboard.html"
    model = User.organisations.through
    table_class = AgentOrganisationsTable
    paginate_by = 10

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("organisation")
            .filter(user=self.request.user)
        )

    def get_table_data(self):
        next_page = self.request.GET.get("next", "feed-list")
        # Each record requires a separate request to the database which is in no way
        # ideal. We need to rethink the data model, possibly making the otc licence and
        # the organisation licence a foreign key.
        return [
            {
                "next": reverse(
                    next_page, args=[record.organisation_id], host=PUBLISH_HOST
                ),
                "organisation_id": record.organisation_id,
                "organisation": record.organisation.name,
                "requires_attention": len(
                    get_requires_attention_data(record.organisation_id)
                ),
            }
            for record in self.get_queryset()
        ]
