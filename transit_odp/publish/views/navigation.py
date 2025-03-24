from typing import Dict, List, TypedDict
import pandas as pd

from django.http import HttpResponseRedirect
from django.views.generic import FormView
from django_hosts import reverse
from django_tables2 import SingleTableView
from waffle import flag_is_active

from config.hosts import PUBLISH_HOST
from transit_odp.avl.require_attention.abods.registery import AbodsRegistery
from transit_odp.avl.require_attention.weekly_ppc_zip_loader import (
    get_vehicle_activity_operatorref_linename,
)
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

        org_list = []
        is_avl_require_attention_active = flag_is_active(
            "", FeatureFlags.AVL_REQUIRES_ATTENTION.value
        )
        is_fares_require_attention_active = flag_is_active(
            "", FeatureFlags.FARES_REQUIRE_ATTENTION.value
        )

        uncounted_activity_df = pd.DataFrame()
        synced_in_last_month = []

        if is_avl_require_attention_active:
            uncounted_activity_df = get_vehicle_activity_operatorref_linename()
            abods_registry = AbodsRegistery()
            synced_in_last_month = abods_registry.records()

        for record in self.get_queryset():
            fares_sra = 0
            avl_sra = 0

            if is_avl_require_attention_active:
                avl_sra = len(
                    get_avl_requires_attention_line_level_data(
                        record.organisation_id,
                        uncounted_activity_df,
                        synced_in_last_month,
                    )
                )

            if is_fares_require_attention_active:
                fares_sra = len(
                    FaresRequiresAttention(
                        record.organisation_id
                    ).get_fares_requires_attention_line_level_data()
                )

            org_list.append(
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
                    "avl_requires_attention": avl_sra,
                    "fares_requires_attention": fares_sra,
                }
            )

        return org_list
