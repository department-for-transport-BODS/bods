from django.conf import settings
from django.urls import include, path
from django.views import defaults as default_views

from transit_odp.avl.views.archive import PPCArchiveView
from transit_odp.common.utils.custom_error_handlers import (
    page_not_found,
    permission_denied,
)
from transit_odp.common.views import ComingSoonView, VersionView
from transit_odp.publish.views.api import ProgressAPIView
from transit_odp.publish.views.base import DataActivityView
from transit_odp.publish.views.gatekeeper import PublishGateKeeperView
from transit_odp.publish.views.guide_me import (
    PublishGuideMeView,
    RedirectDashBoardView,
    RedirectDataActivityView,
    RedirectProfileView,
    RedirectPublishView,
)
from transit_odp.publish.views.home import PublishHomeView
from transit_odp.publish.views.navigation import (
    AgentDashboardView,
    PublishSelectDataTypeView,
    SelectOrgView,
)
from transit_odp.publish.views.reporting import (
    ConsumerFeedbackView,
    ConsumerInteractionsView,
)
from transit_odp.users.views.auth import InviteOnlySignupView

handler404 = "transit_odp.common.utils.custom_error_handlers.page_not_found"
handler403 = "transit_odp.common.utils.custom_error_handlers.permission_denied"

urlpatterns = [
    path("", view=PublishHomeView.as_view(), name="home"),
    path(
        "guide-me/",
        include(
            [
                path("", view=PublishGuideMeView.as_view(), name="guide-me"),
                path(
                    "publish/",
                    view=RedirectPublishView.as_view(),
                    name="redirect-publish",
                ),
                path(
                    "dashboard/",
                    view=RedirectDashBoardView.as_view(),
                    name="redirect-dashboard",
                ),
                path(
                    "activity/",
                    view=RedirectDataActivityView.as_view(),
                    name="redirect-activity",
                ),
                path(
                    "profile/",
                    view=RedirectProfileView.as_view(),
                    name="redirect-profile",
                ),
            ]
        ),
    ),
    path("org/", view=SelectOrgView.as_view(), name="select-org"),
    path("agent-dashboard/", view=AgentDashboardView.as_view(), name="agent-dashboard"),
    path("api/dq/", include("transit_odp.data_quality.api.urls")),
    path("gatekeeper", view=PublishGateKeeperView.as_view(), name="gatekeeper"),
    path(
        "dataset/<int:pk>/progress/",
        view=ProgressAPIView.as_view(),
        name="dataset-progress",
    ),
    path(
        "org/<int:pk1>/dataset/",
        include(
            [
                path(
                    "",
                    view=PublishSelectDataTypeView.as_view(),
                    name="select-data",
                ),
                path("timetable/", include("transit_odp.timetables.urls")),
                path("avl/", include("transit_odp.avl.urls", namespace="avl")),
                path("fares/", include("transit_odp.fares.urls", namespace="fares")),
                path(
                    "data-activity/",
                    include(
                        [
                            path(
                                "",
                                view=DataActivityView.as_view(),
                                name="data-activity",
                            ),
                            path(
                                "consumer-feedback/",
                                view=ConsumerFeedbackView.as_view(),
                                name="consumer-feedback",
                            ),
                            path(
                                "consumer-interactions/",
                                view=ConsumerInteractionsView.as_view(),
                                name="consumer-interactions",
                            ),
                        ]
                    ),
                ),
                path("fares-validator/", include("transit_odp.fares_validator.urls")),
                path(
                    "ppc-archive/",
                    view=PPCArchiveView.as_view(),
                    name="ppc-archive",
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
    path("django_axe/", include("django_axe.urls", namespace="django_axe")),
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
