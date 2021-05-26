from django.conf import settings
from django.urls import include, path
from django.views import defaults as default_views

from transit_odp.common.utils.custom_error_handlers import (
    page_not_found,
    permission_denied,
)
from transit_odp.common.views import ComingSoonView, VersionView
from transit_odp.data_quality.views.report import DraftReportOverviewView
from transit_odp.publish.views.api import ProgressAPIView
from transit_odp.publish.views.gatekeeper import PublishGateKeeperView
from transit_odp.publish.views.home import PublishHomeView
from transit_odp.publish.views.navigation import (
    PublishSelectDataTypeView,
    SelectOrgView,
)
from transit_odp.publish.views.timetable.archive import (
    TimetableFeedArchiveSuccessView,
    TimetableFeedArchiveView,
)
from transit_odp.publish.views.timetable.changelog import FeedChangeLogView
from transit_odp.publish.views.timetable.create import FeedUploadWizard
from transit_odp.publish.views.timetable.delete import (
    RevisionDeleteSuccessView,
    RevisionDeleteTimetableView,
)
from transit_odp.publish.views.timetable.detail import FeedDetailView
from transit_odp.publish.views.timetable.download import DatasetDownloadView
from transit_odp.publish.views.timetable.edit_description import (
    EditDraftRevisionDescriptionView,
    EditLiveRevisionDescriptionView,
)
from transit_odp.publish.views.timetable.list import PublishView
from transit_odp.publish.views.timetable.progess import PublishProgressView
from transit_odp.publish.views.timetable.update import (
    DatasetUpdateModify,
    DraftExistsView,
    FeedUpdateWizard,
    RevisionUpdateSuccessView,
)
from transit_odp.timetables.views import (
    PublishRevisionView,
    ReviewViolationsCSVFileView,
    RevisionPublishSuccessView,
    TimetableUploadModify,
    UpdateRevisionPublishView,
)
from transit_odp.timetables.views.pti import PublishedViolationsCSVFileView
from transit_odp.users.views.auth import InviteOnlySignupView

handler404 = "transit_odp.common.utils.custom_error_handlers.page_not_found"
handler403 = "transit_odp.common.utils.custom_error_handlers.permission_denied"

timetable_path = "org/<int:pk1>/dataset/"
urlpatterns = []
flagged_urls = []

if settings.IS_AVL_FEATURE_FLAG_ENABLED:
    flagged_urls.append(path("avl/", include("transit_odp.avl.urls", namespace="avl")))

if settings.IS_FARES_FEATURE_FLAG_ENABLED:
    flagged_urls.append(
        path("fares/", include("transit_odp.fares.urls", namespace="fares"))
    )

if flagged_urls:
    # At least one feature flag has been enabled so include select data type view
    flagged_urls = [
        path("", view=PublishSelectDataTypeView.as_view(), name="select-data")
    ] + flagged_urls

    urlpatterns += [
        path(
            timetable_path,
            include(flagged_urls),
        ),
        path(
            "dataset/<int:pk>/progress/",
            view=ProgressAPIView.as_view(),
            name="dataset-progress",
        ),
    ]
    timetable_path += "timetable/"

urlpatterns += [
    # Publish data routes
    path("", view=PublishHomeView.as_view(), name="home"),
    path("org/", view=SelectOrgView.as_view(), name="select-org"),
    path("api/dq/", include("transit_odp.data_quality.api.urls")),
    path("gatekeeper", view=PublishGateKeeperView.as_view(), name="gatekeeper"),
    path(
        timetable_path,
        include(
            [
                path("", view=PublishView.as_view(), name="feed-list"),
                path("new", view=FeedUploadWizard.as_view(), name="feed-new"),
                # All these routes must restrict access to organisation who owns
                # the feed
                path(
                    "<int:pk>/",
                    include(
                        [
                            path("", view=FeedDetailView.as_view(), name="feed-detail"),
                            path(
                                "violations-csv",
                                view=PublishedViolationsCSVFileView.as_view(),
                                name="revision-pti-csv",
                            ),
                            path(
                                "review/",
                                include(
                                    [
                                        path(
                                            "",
                                            view=PublishRevisionView.as_view(),
                                            name="revision-publish",
                                        ),
                                        path(
                                            "update",
                                            view=TimetableUploadModify.as_view(),
                                            name="upload-modify",
                                        ),
                                        path(
                                            "pti-csv",
                                            view=ReviewViolationsCSVFileView.as_view(),
                                            name="review-pti-csv",
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
                                "delete/",
                                view=RevisionDeleteTimetableView.as_view(),
                                name="revision-delete",
                            ),
                            path(
                                "progress/",
                                view=PublishProgressView.get_progress,
                                name="progress",
                            ),
                            path(
                                "success/",
                                view=RevisionPublishSuccessView.as_view(),
                                name="revision-publish-success",
                            ),
                            path(
                                "update/",
                                include(
                                    [
                                        path(
                                            "",
                                            view=FeedUpdateWizard.as_view(),
                                            name="feed-update",
                                        ),
                                        path(
                                            "review/",
                                            include(
                                                [
                                                    path(
                                                        "",
                                                        view=UpdateRevisionPublishView.as_view(),  # noqa E501
                                                        name="revision-update-publish",
                                                    ),
                                                    path(
                                                        "update",
                                                        view=DatasetUpdateModify.as_view(),  # noqa E501
                                                        name="update-modify",
                                                    ),
                                                ]
                                            ),
                                        ),
                                        path(
                                            "success/",
                                            view=RevisionUpdateSuccessView.as_view(),
                                            name="revision-update-success",
                                        ),
                                    ]
                                ),
                            ),
                            path(
                                "download/",
                                view=DatasetDownloadView.as_view(),
                                name="feed-download",
                            ),
                            path(
                                "deactivate/",
                                include(
                                    [
                                        path(
                                            "",
                                            view=TimetableFeedArchiveView.as_view(),
                                            name="feed-archive",
                                        ),
                                        path(
                                            "success",
                                            view=TimetableFeedArchiveSuccessView.as_view(),  # noqa E501
                                            name="feed-archive-success",
                                        ),
                                    ]
                                ),
                            ),
                            path(
                                "changelog/",
                                view=FeedChangeLogView.as_view(),
                                name="feed-changelog",
                            ),
                            path(
                                "draft-exists/",
                                view=DraftExistsView.as_view(),
                                name="feed-draft-exists",
                            ),
                            path(
                                "report/<int:report_id>/",
                                # TODO: use namespace?
                                include("config.urls.data_quality"),
                            ),
                            path(
                                "report/draft/",
                                view=DraftReportOverviewView.as_view(),
                                name="dq-draft-report",
                            ),
                        ]
                    ),
                ),
                path(
                    "delete-success",
                    view=RevisionDeleteSuccessView.as_view(),
                    name="revision-delete-success",
                ),
            ]
        ),
    ),
    # Account routes
    path(
        "account/",
        include(
            [
                # override signup view with invited only signup page
                path(
                    "signup/",
                    view=InviteOnlySignupView.as_view(),
                    name="account_signup",
                ),
                path("", include("config.urls.allauth")),
            ]
        ),
    ),
    path("account/", include("transit_odp.users.urls", namespace="users")),
    path("invitations/", include("config.urls.invitations", namespace="invitations")),
    path(
        "guidance/",
        include("transit_odp.guidance.urls.publishers", namespace="guidance"),
    ),
    path("coming_soon/", ComingSoonView.as_view(), name="placeholder"),
    path("version/", VersionView.as_view(), name="version"),
]

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
