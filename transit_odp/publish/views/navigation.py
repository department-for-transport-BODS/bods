from typing import Dict, List, TypedDict

from django.http import HttpResponseRedirect
from django.views.generic import FormView
from django_hosts import reverse

from config.hosts import PUBLISH_HOST
from transit_odp.organisation.constants import AVLType, FaresType, TimetableType
from transit_odp.publish.forms import SelectDataTypeForm
from transit_odp.publish.views.base import BaseTemplateView
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
            namespace + "feed-list",
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
