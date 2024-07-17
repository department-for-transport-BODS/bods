from django.conf import settings
from django.urls import include, path

from transit_odp.browse.views.avl_views import (
    AVLChangeLogView,
    AVLDatasetDetailView,
    AVLSearchView,
    AvlSubscriptionSuccessView,
    AvlSubscriptionView,
    AvlUserFeedbackSuccessView,
    AvlUserFeedbackView,
    DownloadAVLView,
    DownloadGTFSRTDataArchiveView,
    DownloadSIRIVMDataArchiveView,
    DownloadSIRIVMTflDataArchiveView,
)

urlpatterns = [
    path(
        "",
        view=AVLSearchView.as_view(),
        name="avl-search",
    ),
    path(
        "download/",
        include(
            [
                path("", view=DownloadAVLView.as_view(), name="download-avl"),
                path(
                    "bulk_archive",
                    view=DownloadSIRIVMDataArchiveView.as_view(),
                    name="downloads-avl-bulk",
                ),
                path(
                    "gtfsrt",
                    view=DownloadGTFSRTDataArchiveView.as_view(),
                    name="download-gtfsrt-bulk",
                ),
                path(
                    "sirivm_tfl",
                    view=DownloadSIRIVMTflDataArchiveView.as_view(),
                    name="downloads-avl-bulk-tfl",
                ),
            ]
        ),
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
                                view=AVLDatasetDetailView.as_view(),
                                name="avl-feed-detail",
                            ),
                            path(
                                "changelog/",
                                view=AVLChangeLogView.as_view(),
                                name="avl-feed-changelog",
                            ),
                            path(
                                "subscription/",
                                view=AvlSubscriptionView.as_view(),
                                name="avl-feed-subscription",
                            ),
                            path(
                                "subscription/success/",
                                view=AvlSubscriptionSuccessView.as_view(),
                                name="avl-feed-subscription-success",
                            ),
                            path(
                                "feedback/",
                                view=AvlUserFeedbackView.as_view(),
                                name="avl-feed-feedback",
                            ),
                            path(
                                "feedback/success",
                                view=AvlUserFeedbackSuccessView.as_view(),
                                name="avl-feed-feedback-success",
                            ),
                        ]
                    ),
                )
            ]
        ),
    ),
]
if "django_axe" in settings.INSTALLED_APPS and settings.DJANGO_AXE_ENABLED:
    urlpatterns = [path("django_axe/", include("django_axe.urls"))] + urlpatterns
