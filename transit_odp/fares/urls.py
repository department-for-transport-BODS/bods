from django.urls import include, path

from transit_odp.fares import views
from transit_odp.fares.views.edit_description import (
    EditDraftRevisionDescriptionView,
    EditLiveRevisionDescriptionView,
)

app_name = "fares"

urlpatterns = [
    path("", views.ListView.as_view(), name="feed-list"),
    path(
        "new/",
        views.FaresUploadWizard.as_view(),
        name="new-feed",
    ),
    path(
        "<int:pk>/",
        include(
            [
                path(
                    "",
                    views.FaresFeedDetailView.as_view(),
                    name="feed-detail",
                ),
                path(
                    "review/",
                    include(
                        [
                            path(
                                "",
                                view=views.ReviewView.as_view(),
                                name="revision-publish",
                            ),
                            path(
                                "update",
                                view=views.FaresDatasetUploadModify.as_view(),
                                name="upload-modify",
                            ),
                        ]
                    ),
                ),
                path(
                    "delete/",
                    view=views.RevisionDeleteFaresView.as_view(),
                    name="revision-delete",
                ),
                path(
                    "delete-success",
                    view=views.RevisionDeleteSuccessView.as_view(),
                    name="revision-delete-success",
                ),
                path(
                    "success/",
                    view=views.RevisionPublishSuccessView.as_view(),
                    name="revision-publish-success",
                ),
                path(
                    "update/",
                    include(
                        [
                            path(
                                "",
                                view=views.FeedUpdateWizard.as_view(),
                                name="feed-update",
                            ),
                            path(
                                "review/",
                                include(
                                    [
                                        path(
                                            "",
                                            view=views.UpdateRevisionPublishView.as_view(),  # noqa E501
                                            name="revision-update-publish",
                                        ),
                                        path(
                                            "update",
                                            view=views.DatasetUpdateModify.as_view(),  # noqa E501
                                            name="update-modify",
                                        ),
                                    ]
                                ),
                            ),
                            path(
                                "success/",
                                view=views.RevisionUpdateSuccessView.as_view(),
                                name="revision-update-success",
                            ),
                            path(
                                "draft-exists/",
                                view=views.DraftExistsView.as_view(),
                                name="feed-draft-exists",
                            ),
                        ]
                    ),
                ),
                path(
                    "dataset-edit/",
                    view=EditLiveRevisionDescriptionView.as_view(),
                    name="dataset-edit",
                ),
                path(
                    "revision-edit/",
                    view=EditDraftRevisionDescriptionView.as_view(),
                    name="revision-edit",
                ),
                path(
                    "download",
                    view=views.DownloadFaresFileView.as_view(),
                    name="feed-download",
                ),
                path(
                    "deactivate/",
                    include(
                        [
                            path(
                                "",
                                view=views.FaresFeedArchiveView.as_view(),
                                name="feed-archive",
                            ),
                            path(
                                "success",
                                view=views.FaresFeedArchiveSuccessView.as_view(),
                                name="feed-archive-success",
                            ),
                        ]
                    ),
                ),
                path(
                    "changelog/",
                    view=views.FaresChangelogView.as_view(),
                    name="feed-changelog",
                ),
            ]
        ),
    ),
    path("django_axe/", include("django_axe.urls")),
]
