from typing import Final

from django.urls import include, path, re_path
from django.views.generic import RedirectView
from django_axe import urls

from transit_odp.browse.views.timetable_views import (
    DatasetChangeLogView,
    DatasetDetailView,
    DatasetDownloadView,
    DatasetSubscriptionSuccessView,
    DatasetSubscriptionView,
    DownloadBulkDataArchiveRegionsView,
    DownloadBulkDataArchiveView,
    DownloadChangeDataArchiveView,
    DownloadCompliantBulkDataArchiveView,
    DownloadRegionalGTFSFileView,
    DownloadTimetablesView,
    LineMetadataDetailView,
    SearchView,
    UserFeedbackSuccessView,
    UserFeedbackView,
)

DATASET_PATHS: Final = [
    path(
        "<int:pk>/",
        include(
            [
                path(
                    "",
                    view=DatasetDetailView.as_view(),
                    name="feed-detail",
                ),
                path(
                    "detail/",
                    view=LineMetadataDetailView.as_view(),
                    name="feed-line-detail",
                ),
                path(
                    "subscription/",
                    view=DatasetSubscriptionView.as_view(),
                    name="feed-subscription",
                ),
                path(
                    "subscription/success/",
                    view=DatasetSubscriptionSuccessView.as_view(),
                    name="feed-subscription-success",
                ),
                path(
                    "download/",
                    view=DatasetDownloadView.as_view(),
                    name="feed-download",
                ),
                path(
                    "changelog/",
                    view=DatasetChangeLogView.as_view(),
                    name="feed-changelog",
                ),
                path(
                    "feedback/",
                    view=UserFeedbackView.as_view(),
                    name="feed-feedback",
                ),
                path(
                    "feedback/success",
                    view=UserFeedbackSuccessView.as_view(),
                    name="feed-feedback-success",
                ),
            ]
        ),
    ),
]


urlpatterns = [
    # Find data routes
    path("", view=SearchView.as_view(), name="search"),
    path(
        "download/",
        view=DownloadTimetablesView.as_view(),
        name="download-timetables",
    ),
    path(
        "download/bulk_archive",
        view=DownloadBulkDataArchiveView.as_view(),
        name="downloads-bulk",
    ),
    path(
        "download/bulk_archive/<str:region_code>",
        view=DownloadBulkDataArchiveRegionsView.as_view(),
        name="downloads-bulk-region",
    ),
    path(
        "download/compliant_bulk_archive",
        view=DownloadCompliantBulkDataArchiveView.as_view(),
        name="downloads-compliant-bulk",
    ),
    path(
        "download/change_archive/<slug:published_at>/",
        view=DownloadChangeDataArchiveView.as_view(),
        name="downloads-change",
    ),
    path(
        "download/gtfs-file/<str:id>/",
        DownloadRegionalGTFSFileView.as_view(),
        name="gtfs-file-download",
    ),
    re_path(
        r"^category/(?P<path>.*)/$",
        RedirectView.as_view(url="/timetable/%(path)s/", permanent=True),
    ),
    path("dataset/", include(DATASET_PATHS)),
    path("axe/", include(urls, namespace="django_axe")),
]
