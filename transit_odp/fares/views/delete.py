from django.views.generic.detail import DetailView
from django_hosts import reverse

from config.hosts import PUBLISH_HOST
from transit_odp.organisation.constants import EXPIRED, FaresType
from transit_odp.organisation.models import Dataset
from transit_odp.publish.views.base import DeleteRevisionBaseView
from transit_odp.users.views.mixins import OrgUserViewMixin


class RevisionDeleteFaresView(DeleteRevisionBaseView):
    template_name = "fares/feed_delete.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(organisation_id=self.organisation.id, dataset_type=FaresType)
        )

    def get_success_url(self):
        kwargs = {"pk1": self.kwargs["pk1"], "pk": self.kwargs["pk"]}
        return reverse(
            "fares:revision-delete-success",
            kwargs=kwargs,
            host=PUBLISH_HOST,
        )

    def get_cancel_url(self, feed_id: int):
        kwargs = {"pk": feed_id, "pk1": self.kwargs["pk1"]}
        if self.object.live_revision is None:
            viewname = "fares:revision-publish"
        elif self.object.live_revision.status == EXPIRED:
            viewname = "fares:feed-detail"
        else:
            viewname = "fares:revision-update-publish"

        return reverse(viewname=viewname, kwargs=kwargs, host=PUBLISH_HOST)


class RevisionDeleteSuccessView(OrgUserViewMixin, DetailView):
    template_name = "fares/feed_delete_success.html"
    model = Dataset
