from django.urls import include, path

import transit_odp.avl.views.dataset_review
from transit_odp.avl import views
from transit_odp.avl.views.edit_description import (
    EditDraftRevisionDescriptionView,
    EditLiveRevisionDescriptionView,
)

app_name = "avl"
urlpatterns = [
    path("", views.ListView.as_view(), name="feed-list"),
    path(
        "new/",
        views.AVLUploadWizard.as_view(),
        name="new-feed",
    ),
    path(
        "<int:pk>/",
        include(
            [
                path(
                    "",
                    views.AvlFeedDetailView.as_view(),
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
                            # path(
                            #     "update",
                            #     view=DatasetUploadModify.as_view(),
                            #     name="upload-modify",
                            # ),
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
                    "delete/",
                    view=views.RevisionDeleteAVLView.as_view(),
                    name="revision-delete",
                ),
                path(
                    "success/",
                    view=views.RevisionPublishSuccessView.as_view(),
                    name="revision-publish-success",
                ),
                path(
                    "error/",
                    view=views.PublishErrorView.as_view(),
                    name="revision-publish-error",
                ),
                path(
                    "update/",
                    include(
                        [
                            path(
                                "",
                                view=views.AVLUpdateWizard.as_view(),
                                name="feed-update",
                            ),
                            path(
                                "review/",
                                include(
                                    [
                                        path(
                                            "",
                                            view=transit_odp.avl.views.dataset_review.UpdateRevisionPublishView.as_view(),  # noqa E501
                                            name="revision-update-publish",
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
                    "deactivate/",
                    include(
                        [
                            path(
                                "",
                                views.AVLFeedArchiveView.as_view(),
                                name="feed-archive",
                            ),
                            path(
                                "success",
                                views.AVLFeedArchiveSuccessView.as_view(),
                                name="feed-archive-success",
                            ),
                        ]
                    ),
                ),
                path(
                    "changelog/",
                    view=views.ChangeLogView.as_view(),
                    name="feed-changelog",
                ),
                path(
                    "validation-report/",
                    view=views.ValidationFileDownloadView.as_view(),
                    name="validation-report-download",
                ),
                path(
                    "schema-report/",
                    view=views.SchemaValidationFileDownloadView.as_view(),
                    name="schema-report-download",
                ),
            ]
        ),
    ),
    path(
        "delete-success",
        view=views.RevisionDeleteSuccessView.as_view(),
        name="revision-delete-success",
    ),
]
