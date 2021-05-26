import logging

from cavl_client.rest import ApiException
from django.db import transaction

from transit_odp.bods.interfaces.plugins import get_cavl_service
from transit_odp.organisation.constants import DatasetType
from transit_odp.publish.views.base import (
    FeedArchiveBaseView,
    FeedArchiveSuccessBaseView,
)

APP_NAME = "avl"
_404 = 404
logger = logging.getLogger(__name__)


class AVLFeedArchiveView(FeedArchiveBaseView):
    template_name = "avl/feed_archive.html"
    app_name = APP_NAME
    dataset_type = DatasetType.AVL

    @transaction.atomic()
    def form_valid(self, form):
        dataset = self.get_object()
        cavl_service = get_cavl_service()

        try:
            cavl_service.delete_feed(feed_id=dataset.id)
        except ApiException as e:
            if e.status == _404:
                logger.error(
                    f"[CAVL] Dataset {dataset.id} => Does not exist in CAVL Service."
                )
        return super().form_valid(form)


class AVLFeedArchiveSuccessView(FeedArchiveSuccessBaseView):
    template_name = "avl/feed_archive_success.html"
    app_name = APP_NAME
