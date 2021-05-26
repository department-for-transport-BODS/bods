from transit_odp.organisation.constants import DatasetType
from transit_odp.publish.views.base import (
    FeedArchiveBaseView,
    FeedArchiveSuccessBaseView,
)

URL_NAMESPACE = "fares"


class FaresFeedArchiveView(FeedArchiveBaseView):
    template_name = "publish/feed_archive.html"
    app_name = URL_NAMESPACE
    dataset_type = DatasetType.FARES


class FaresFeedArchiveSuccessView(FeedArchiveSuccessBaseView):
    app_name = URL_NAMESPACE
