from django_hosts import reverse

import config.hosts
from transit_odp.common.views import BaseTemplateView
from transit_odp.organisation.constants import DatasetType
from transit_odp.publish.views.base import DeleteRevisionBaseView
from transit_odp.users.views.mixins import OrgUserViewMixin


class RevisionDeleteAVLView(DeleteRevisionBaseView):
    template_name = "avl/feed_delete.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                organisation_id=self.organisation.id,
                dataset_type=DatasetType.AVL.value,
            )
        )

    def get_cancel_url(self, feed_id):
        return (
            reverse(
                "avl:revision-publish",
                kwargs={"pk": feed_id, "pk1": self.kwargs["pk1"]},
                host=config.hosts.PUBLISH_HOST,
            )
            if self.object.live_revision is None
            else reverse(
                "avl:revision-update-publish",
                kwargs={"pk": feed_id, "pk1": self.kwargs["pk1"]},
                host=config.hosts.PUBLISH_HOST,
            )
        )

    def get_success_url(self):
        return reverse(
            "avl:revision-delete-success",
            kwargs={"pk1": self.kwargs["pk1"]},
            host=config.hosts.PUBLISH_HOST,
        )


class RevisionDeleteSuccessView(OrgUserViewMixin, BaseTemplateView):
    template_name = "avl/feed_delete_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pk1"] = self.kwargs["pk1"]
        return context
