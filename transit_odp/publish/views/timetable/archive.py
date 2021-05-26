from transit_odp.organisation.constants import DatasetType
from transit_odp.publish.views.base import (
    FeedArchiveBaseView,
    FeedArchiveSuccessBaseView,
)


class TimetableFeedArchiveView(FeedArchiveBaseView):
    template_name = "publish/feed_archive.html"
    app_name = None
    dataset_type = DatasetType.TIMETABLE


class TimetableFeedArchiveSuccessView(FeedArchiveSuccessBaseView):
    app_name = None
