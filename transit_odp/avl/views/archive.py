import logging

from django.db import transaction
from django.http import FileResponse
from django.views.generic import View

from transit_odp.avl.client import CAVLService
from transit_odp.avl.post_publishing_checks.archive import PPCArchiveCreator
from transit_odp.organisation.constants import DatasetType
from transit_odp.publish.views.base import (
    FeedArchiveBaseView,
    FeedArchiveSuccessBaseView,
)

APP_NAME = "avl"
logger = logging.getLogger(__name__)


class AVLFeedArchiveView(FeedArchiveBaseView):
    template_name = "avl/feed_archive.html"
    app_name = APP_NAME
    dataset_type = DatasetType.AVL

    def get_queryset(self):
        return super().get_queryset().filter(is_dummy=False)

    @transaction.atomic()
    def form_valid(self, form):
        dataset = self.get_object()
        cavl_service = CAVLService()
        cavl_service.delete_feed(feed_id=dataset.id)

        return super().form_valid(form)


class AVLFeedArchiveSuccessView(FeedArchiveSuccessBaseView):
    template_name = "avl/feed_archive_success.html"
    app_name = APP_NAME


class PPCArchiveView(View):
    def get(self, *args, **kwargs):
        org_id = self.kwargs["pk1"]
        archiver = PPCArchiveCreator()
        four_week_buffer = archiver.create_archive(org_id)
        return self.render_to_response(
            four_week_buffer, "archived_avl_to_timetable_matching_all_feeds.zip"
        )

    def render_to_response(self, buffer, filename):
        response = FileResponse(buffer, as_attachment=True)
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response
