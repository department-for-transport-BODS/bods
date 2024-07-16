from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from django_axe import urls

from transit_odp.common.utils.custom_error_handlers import (
    page_not_found,
    permission_denied,
)
from transit_odp.common.views import ComingSoonView
from transit_odp.site_admin.urls import (
    account_paths,
    agent_paths,
    consumer_paths,
    metrics_paths,
    organisation_paths,
)
from transit_odp.site_admin.views import AdminHomeView
from transit_odp.users.views.auth import InviteOnlySignupView

urlpatterns = [
    path("", AdminHomeView.as_view(), name="home"),
    path(
        "metrics/",
        include(metrics_paths),
    ),
    path("coming_soon/", ComingSoonView.as_view(), name="placeholder"),
    path(
        "",
        include(
            (
                [
                    path("consumers/", include(consumer_paths)),
                    path("organisations/", include(organisation_paths)),
                    path("agents/", include(agent_paths)),
                    # Put account routes here so they share the users namespace
                    path("account/", include(account_paths)),
                ],
                "users",
            ),
            # Note need to add users namespace to be compatible  with other service
            namespace="users",
        ),
    ),
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
    path("invitations/", include("config.urls.invitations", namespace="invitations")),
    # Django Admin, use {% url 'admin:index' %}
    # TODO - host route on Admin service
    path(settings.ADMIN_URL, admin.site.urls),
]

if "django_axe" in settings.INSTALLED_APPS and settings.DJANGO_AXE_ENABLED:
    urlpatterns = [
        path("django-axe/", include(urls, namespace="django_axe"))
    ] + urlpatterns

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
        path("docs/", include("django.contrib.admindocs.urls")),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
