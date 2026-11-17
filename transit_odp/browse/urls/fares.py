from django.urls import include, path

from transit_odp.browse.views.fares_views import (
    DownloadFaresBulkDataArchiveView,
    DownloadFaresView,
    FaresChangeLogView,
    FaresDatasetDetailView,
    FaresDatasetDownloadView,
    FaresSearchView,
    FaresSubscriptionSuccessView,
    FaresSubscriptionView,
    FaresUserFeedbackSuccessView,
    FaresUserFeedbackView,
)

urlpatterns = [
    path(
        "",
        view=FaresSearchView.as_view(),
        name="search-fares",
    ),
    path("download/", view=DownloadFaresView.as_view(), name="download-fares"),
    path(
        "download/bulk_archive",
        view=DownloadFaresBulkDataArchiveView.as_view(),
        name="downloads-fares-bulk",
    ),
    path(
        "dataset/",
        include(
            [
                path(
                    "<int:pk>/",
                    include(
                        [
                            path(
                                "",
                                view=FaresDatasetDetailView.as_view(),
                                name="fares-feed-detail",
                            ),
                            path(
                                "download/",
                                view=FaresDatasetDownloadView.as_view(),
                                name="fares-feed-download",
                            ),
                            path(
                                "changelog/",
                                view=FaresChangeLogView.as_view(),
                                name="fares-feed-changelog",
                            ),
                            path(
                                "subscription/",
                                view=FaresSubscriptionView.as_view(),
                                name="fares-feed-subscription",
                            ),
                            path(
                                "subscription/success/",
                                view=FaresSubscriptionSuccessView.as_view(),
                                name="fares-feed-subscription-success",
                            ),
                            path(
                                "feedback/",
                                view=FaresUserFeedbackView.as_view(),
                                name="fares-feed-feedback",
                            ),
                            path(
                                "feedback/success",
                                view=FaresUserFeedbackSuccessView.as_view(),
                                name="fares-feed-feedback-success",
                            ),
                        ]
                    ),
                )
            ]
        ),
    ),
    path("django_axe/", include("django_axe.urls")),
]
