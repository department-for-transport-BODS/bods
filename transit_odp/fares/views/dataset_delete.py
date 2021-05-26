from django.views.generic import TemplateView
from django_hosts import reverse

import config.hosts
from transit_odp.organisation.constants import DatasetType
from transit_odp.publish.views.base import DeleteRevisionBaseView
from transit_odp.users.views.mixins import OrgUserViewMixin


class RevisionDeleteFaresView(DeleteRevisionBaseView):
    template_name = "fares/feed_delete.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                organisation_id=self.organisation.id,
                dataset_type=DatasetType.FARES.value,
            )
        )

    def get_success_url(self):
        return reverse(
            "fares:revision-delete-success",
            kwargs={"pk1": self.kwargs["pk1"]},
            host=config.hosts.PUBLISH_HOST,
        )

    def get_cancel_url(self, feed_id):
        return (
            reverse(
                "fares:revision-publish",
                kwargs={"pk": feed_id, "pk1": self.kwargs["pk1"]},
                host=config.hosts.PUBLISH_HOST,
            )
            if self.object.live_revision is None
            else reverse(
                "fares:revision-publish",
                kwargs={"pk": feed_id, "pk1": self.kwargs["pk1"]},
                host=config.hosts.PUBLISH_HOST,
            )
            #  TODO: add this back when Fares update flow is done
            # reverse(
            #     "fares:revision-update-publish",
            #     kwargs={"pk": feed_id},
            #     host=config.hosts.PUBLISH_HOST,
            # )
        )


class RevisionDeleteSuccessView(OrgUserViewMixin, TemplateView):
    template_name = "fares/feed_delete_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pk1"] = self.kwargs["pk1"]
        return context
