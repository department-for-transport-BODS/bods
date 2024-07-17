from django.conf import settings
from django.urls import include, path
from django_axe import urls

from transit_odp.avl import views

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
                        ]
                    ),
                ),
                path(
                    "download-matching-report/",
                    view=views.DownloadPPCWeeklyReportView.as_view(),
                    name="download-matching-report",
                ),
                path(
                    "dataset-edit/",
                    view=views.EditLiveRevisionDescriptionView.as_view(),
                    name="dataset-edit",
                ),
                path(
                    "revision-edit/",
                    view=views.EditDraftRevisionDescriptionView.as_view(),
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
                                            view=views.UpdateRevisionPublishView.as_view(),  # noqa E501
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
                    view=views.AVLChangeLogView.as_view(),
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

if "django_axe" in settings.INSTALLED_APPS and settings.DJANGO_AXE_ENABLED:
    urlpatterns = [
        path("django-axe/", include(urls, namespace="django_axe"))
    ] + urlpatterns
