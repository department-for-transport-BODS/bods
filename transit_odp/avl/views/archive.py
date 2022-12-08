import logging

from django.db import transaction

from transit_odp.avl.client import CAVLService
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
