import config.hosts
from django_hosts import reverse

from transit_odp.avl.forms import EditFeedDescriptionForm
from transit_odp.organisation.constants import DatasetType
from transit_odp.publish.views.base import EditDescriptionBaseView


class EditLiveRevisionDescriptionView(EditDescriptionBaseView):
    template_name = "avl/feed_description_edit.html"
    form_class = EditFeedDescriptionForm
    dataset_type = DatasetType.AVL.value

    def get_object(self, queryset=None):
        dataset = super().get_object()
        self.object = dataset.live_revision
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"is_live": True})
        return context

    def get_dataset_url(self):
        self.object = self.get_object()
        org_id = self.kwargs.get("pk1", None)
        return reverse(
            "avl:feed-detail",
            kwargs={"pk": self.object.dataset_id, "pk1": org_id},
            host=config.hosts.PUBLISH_HOST,
        )


class EditDraftRevisionDescriptionView(EditDescriptionBaseView):
    template_name = "avl/feed_description_edit.html"
    form_class = EditFeedDescriptionForm
    dataset_type = DatasetType.AVL.value

    def get_object(self, queryset=None):
        dataset = super().get_object()
        self.object = dataset.revisions.latest("id")
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_revision_update = False
        if self.object.dataset.live_revision is not None:
            is_revision_update = True
        context.update({"is_live": False, "is_revision_update": is_revision_update})
        return context

    def get_dataset_url(self):
        org_id = self.kwargs.get("pk1", None)
        self.object = self.get_object()
        dataset = self.object.dataset

        if dataset.live_revision is None:
            # go to publish review page
            return reverse(
                "avl:revision-publish",
                kwargs={"pk": self.object.dataset_id, "pk1": org_id},
                host=config.hosts.PUBLISH_HOST,
            )
        else:
            # go to update review page
            return reverse(
                "avl:revision-update-publish",
                kwargs={"pk": self.object.dataset_id, "pk1": org_id},
                host=config.hosts.PUBLISH_HOST,
            )
