from django.conf import settings
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic.base import TemplateView
from rest_framework.authtoken import views

from transit_odp.browse.views.base_views import (
    ApiSelectView,
    BrowseHomeView,
    DownloadsView,
    SearchSelectView,
)
from transit_odp.browse.views.contact_operator import (
    ContactOperatorFeedbackSuccessView,
    ContactOperatorView,
)
from transit_odp.browse.views.data_catalogue import DownloadDataCatalogueView
from transit_odp.browse.views.guide_me import BrowseGuideMeView
from transit_odp.browse.views.local_authority import (
    LocalAuthorityDetailView,
    LocalAuthorityExportView,
    LocalAuthorityView,
)
from transit_odp.browse.views.operators import OperatorDetailView, OperatorsView
from transit_odp.common.views import ComingSoonView, VersionView
from transit_odp.users.urls import AGENT_PATHS
from transit_odp.users.views.account import (
    DatasetManageView,
    MyAccountView,
    SettingsView,
    UserRedirectView,
)

urlpatterns = [
    path("", view=BrowseHomeView.as_view(), name="home"),
    path("search/", view=SearchSelectView.as_view(), name="select-data"),
    path("downloads/", view=DownloadsView.as_view(), name="downloads"),
    path("api/", view=ApiSelectView.as_view(), name="api-select"),
    path(
        "guide-me/",
        view=BrowseGuideMeView.as_view(),
        name="guide-me",
    ),
    path(
        "catalogue/",
        view=DownloadDataCatalogueView.as_view(),
        name="download-catalogue",
    ),
    path(
        "operators/",
        include(
            [
                path("", view=OperatorsView.as_view(), name="operators"),
                path(
                    "<int:pk>/",
                    include(
                        [
                            path(
                                "",
                                view=OperatorDetailView.as_view(),
                                name="operator-detail",
                            ),
                            path(
                                "contact/",
                                view=ContactOperatorView.as_view(),
                                name="contact-operator",
                            ),
                            path(
                                "contact/success/",
                                view=ContactOperatorFeedbackSuccessView.as_view(),
                                name="feedback-operator-success",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    path(
        "local-authority/",
        include(
            [
                path("", view=LocalAuthorityView.as_view(), name="local-authority"),
                path(
                    "<int:pk>/",
                    include(
                        [
                            path(
                                "detail/",
                                view=LocalAuthorityDetailView.as_view(),
                                name="local-authority-detail",
                            ),
                            path(
                                "export/",
                                view=LocalAuthorityExportView.as_view(),
                                name="local-authority-export",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    path(
        "contact/",
        TemplateView.as_view(template_name="pages/contact.html"),
        name="contact",
    ),
    path(
        "api/",
        include(
            [
                path(
                    "api-auth/",
                    include("rest_framework.urls", namespace="rest_framework"),
                ),
                path("api-token-auth/", views.obtain_auth_token),
                path("", include("transit_odp.api.urls", namespace="api")),
            ]
        ),
    ),
    path("timetable/", include("transit_odp.browse.urls.timetables")),
    path("avl/", include("transit_odp.browse.urls.avl")),
    path("fares/", include("transit_odp.browse.urls.fares")),
    path("account/", include("config.urls.allauth")),
    path(
        "account/",
        include(
            (  # 2-tuple of urls and 'app_name', this is required for namespace to work
                [
                    path("", view=MyAccountView.as_view(), name="home"),
                    path("settings/", view=SettingsView.as_view(), name="settings"),
                    path(
                        "manage/", view=DatasetManageView.as_view(), name="feeds-manage"
                    ),
                    # Used to redirect back to user's account page
                    path(
                        "~redirect/", view=UserRedirectView.as_view(), name="redirect"
                    ),
                    path("agent/", include(AGENT_PATHS)),
                ],
                "users",
            ),
            namespace="users",
        ),
    ),
    # Invitation routes
    path("invitations/", include("config.urls.invitations", namespace="invitations")),
    # Guidance routes
    path(
        "guidance/",
        include("transit_odp.guidance.urls.developers", namespace="guidance"),
    ),
    path("coming_soon/", ComingSoonView.as_view(), name="placeholder"),
    path("version/", VersionView.as_view(), name="version"),
]

if settings.DEBUG:
    from django.conf.urls.static import static

    # Its awkward to display urls to media files, e.g. bulk data archive, since in dev
    # only the relative location is
    # available while in prod the urls will be absolute to S3. Therefore, for the
    # relative urls to resolve we must
    # serve media file from the data subdomain not just root.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

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
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
