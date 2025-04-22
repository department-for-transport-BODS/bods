from django.contrib.auth.mixins import LoginRequiredMixin
from django_hosts import reverse

from config.hosts import PUBLISH_HOST
from transit_odp.common.views import BaseTemplateView
from transit_odp.users.constants import AccountType
from django.shortcuts import redirect


class PublishHomeView(LoginRequiredMixin, BaseTemplateView):
    template_name = "publish/publish_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if not user.is_org_user:
            start_view = reverse("gatekeeper", host=PUBLISH_HOST)
            review_page = start_view
        elif user.account_type == AccountType.abods_user.value:
            start_view = reverse("abods-gatekeeper", host=PUBLISH_HOST)
            review_page = start_view
        elif user.is_agent_user:
            start_view = reverse("select-org", host=PUBLISH_HOST)
            review_page = reverse("agent-dashboard", host=PUBLISH_HOST)
        else:
            org_id = self.request.user.organisation.id
            start_view = reverse(
                "select-data",
                host=PUBLISH_HOST,
                kwargs={"pk1": org_id},
            )
            review_page = reverse(
                "feed-list",
                host=PUBLISH_HOST,
                kwargs={"pk1": org_id},
            )

        context["start_view"] = start_view
        context["review_page"] = review_page
        return context

    def dispatch(self, request, *args, **kwargs):
        if request.user.account_type == AccountType.abods_user.value:
            return redirect(reverse("abods-gatekeeper", host=PUBLISH_HOST))
        return super().dispatch(request, *args, **kwargs)
