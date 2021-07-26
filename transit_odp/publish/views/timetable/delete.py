from django.http import HttpResponseRedirect
from django_hosts import reverse

import config.hosts
from transit_odp.organisation.constants import DatasetType, FeedStatus
from transit_odp.publish.views.base import (
    BaseTemplateView,
    DeleteRevisionBaseView,
    PublishFeedDetailViewBase,
)
from transit_odp.users.views.mixins import OrgUserViewMixin

ExpiredStatus = FeedStatus.expired.value


class RevisionDeleteTimetableView(DeleteRevisionBaseView):
    template_name = "publish/feed_delete.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                organisation_id=self.organisation.id,
                dataset_type=DatasetType.TIMETABLE.value,
            )
        )

    def get_success_url(self):
        return reverse(
            "revision-delete-success",
            kwargs={"pk1": self.kwargs["pk1"]},
            host=config.hosts.PUBLISH_HOST,
        )

    def get_cancel_url(self, feed_id):
        if self.object.live_revision:
            if self.object.live_revision.status == ExpiredStatus:
                viewname = "feed-detail"
            else:
                viewname = "revision-update-publish"
        else:
            viewname = "revision-publish"
        return reverse(
            viewname,
            kwargs={"pk": feed_id, "pk1": self.kwargs["pk1"]},
            host=config.hosts.PUBLISH_HOST,
        )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["cancel_url"] = self.get_cancel_url(self.object.id)
        return data


class RevisionDeleteSuccessView(OrgUserViewMixin, BaseTemplateView):
    template_name = "publish/feed_delete_success.html"


class FeedDeleteView(OrgUserViewMixin, PublishFeedDetailViewBase):
    template_name = "publish/feed_list.html"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        # feed_object.status = FeedStatus.expired.value
        self.object.to_deleted()
        self.object.save()

        user = self.request.user
        if self.object.last_modified_user != user:
            self.object.last_modified_user = user
            self.object.save()
        # self.object.last_modified_user = user

        return HttpResponseRedirect(
            reverse(
                "feed-delete-success",
                kwargs={"pk": self.object.id if self.object is not None else None},
                host=config.hosts.PUBLISH_HOST,
            )
        )
