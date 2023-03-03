from django.views.generic import RedirectView
from django_hosts import reverse

from config.hosts import PUBLISH_HOST
from transit_odp.common.views import GuideMeBaseView, Section
from transit_odp.users.views.mixins import OrgUserViewMixin


class PublishGuideMeView(GuideMeBaseView):
    template_location = "publish/guideme"
    template_name = f"{template_location}/guide_me.html"

    SECTIONS = (
        Section(
            "Read supporting documents",
            f"{template_location}/read_supporting_documents.html",
        ),
        Section(
            "Set up your account",
            f"{template_location}/setup_your_account.html",
        ),
        Section(
            "Publish open data",
            f"{template_location}/publish_open_data.html",
        ),
        Section(
            "Review your data",
            f"{template_location}/review_your_data.html",
        ),
    )


class RedirectPublishView(OrgUserViewMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user
        if user.is_agent_user:
            return reverse("select-org", host=PUBLISH_HOST)
        return reverse(
            "select-data", kwargs={"pk1": user.organisation.id}, host=PUBLISH_HOST
        )


class RedirectDashBoardView(OrgUserViewMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user
        if user.is_agent_user:
            return reverse("agent-dashboard", host=PUBLISH_HOST)
        return reverse(
            "feed-list", kwargs={"pk1": user.organisation.id}, host=PUBLISH_HOST
        )


class RedirectDataActivityView(OrgUserViewMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user
        if user.is_agent_user:
            return (
                reverse("agent-dashboard", host=PUBLISH_HOST)
                + "?next=data-activity&prev=guide-me"
            )
        return (
            reverse(
                "data-activity", kwargs={"pk1": user.organisation.id}, host=PUBLISH_HOST
            )
            + "?prev=guide-me"
        )


class RedirectProfileView(OrgUserViewMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        user = self.request.user
        return reverse(
            "users:organisation-profile",
            host=PUBLISH_HOST,
            kwargs={"pk": user.organisation.id},
        )
