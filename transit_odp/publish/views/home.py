from config.hosts import PUBLISH_HOST
from django_hosts import reverse

from transit_odp.publish.views.base import BaseTemplateView
from transit_odp.users.constants import AccountType


class PublishHomeView(BaseTemplateView):
    template_name = "publish/publish_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        is_authenticated = user.is_authenticated
        feature = context.get("feature")
        account_type = (
            AccountType.org_admin.value,
            AccountType.org_staff.value,
            AccountType.agent_user.value,
        )

        if is_authenticated:
            if user.account_type not in account_type:
                start_view = reverse("gatekeeper", host=PUBLISH_HOST)
            elif user.is_agent_user:
                start_view = reverse("select-org", host=PUBLISH_HOST)
            elif feature.avl or feature.fares:
                start_view = reverse(
                    "select-data",
                    host=PUBLISH_HOST,
                    kwargs={"pk1": self.request.user.organisation.id},
                )
            else:
                start_view = reverse(
                    "feed-list",
                    host=PUBLISH_HOST,
                    kwargs={"pk1": self.request.user.organisation.id},
                )
        else:
            start_view = reverse("account_login", host=PUBLISH_HOST)

        context["start_view"] = start_view

        return context
