from django.conf import settings
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from rest_framework.authtoken import views

from transit_odp.browse.views.base_views import (
    ApiSelectView,
    BrowseHomeView,
    DownloadDataCatalogueView,
    DownloadOperatorDatasetCatalogueView,
    DownloadOperatorNocCatalogueView,
    DownloadsView,
    SearchSelectView,
)
from transit_odp.common.views import ComingSoonView, VersionView
from transit_odp.users.urls import AGENT_PATHS
from transit_odp.users.views.account import (
    DatasetManageView,
    MyAccountView,
    SettingsView,
    UserRedirectView,
)

urlpatterns = []
timetable_path = "search/"

if settings.IS_AVL_FEATURE_FLAG_ENABLED:
    # AVL routes
    urlpatterns.append(path("avl/", include("transit_odp.browse.urls.avl")))

if settings.IS_FARES_FEATURE_FLAG_ENABLED:
    # Fares routes
    urlpatterns.append(path("fares/", include("transit_odp.browse.urls.fares")))

if urlpatterns:
    timetable_path = "timetable/"
    urlpatterns = [
        path("search/", view=SearchSelectView.as_view(), name="select-data"),
        path("downloads/", view=DownloadsView.as_view(), name="downloads"),
        path("api/", view=ApiSelectView.as_view(), name="api-select"),
        path(
            "catalogue/",
            include(
                [
                    path(
                        "",
                        view=DownloadDataCatalogueView.as_view(),
                        name="download-catalogue",
                    ),
                    path(
                        "operator-noc/",
                        view=DownloadOperatorNocCatalogueView.as_view(),
                        name="operator-noc-catalogue",
                    ),
                    path(
                        "operator-dataset/",
                        view=DownloadOperatorDatasetCatalogueView.as_view(),
                        name="operator-dataset-catalogue",
                    ),
                ]
            ),
        ),
    ] + urlpatterns

urlpatterns += [
    # Find data routes
    path("", view=BrowseHomeView.as_view(), name="home"),
    path(
        "contact/",
        TemplateView.as_view(template_name="pages/contact.html"),
        name="contact",
    ),
    # API routes
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
    # Timetable routes
    path(timetable_path, include("transit_odp.browse.urls.timetables")),
    # path("", include("transit_odp.browse.urls.timetables")),
    # Account routes
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
