from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView

from transit_odp.browse.views.base_views import (
    GlobalFeedbackThankYouView,
    GlobalFeedbackView,
)
from transit_odp.changelog.views import ChangelogView
from transit_odp.common.utils.custom_error_handlers import (
    page_not_found,
    permission_denied,
)
from transit_odp.common.views import (
    CookieDetailView,
    CookieView,
    PrivacyPolicyView,
    VersionView,
)
from transit_odp.fares.views.api import (
    create_fares_dataset_api,
    get_fares_review_status_api,
    publish_fares_dataset_api,
)
from transit_odp.timetables.views.api import ( 
    get_timetables_review_status_api 
)

from transit_odp.api.views.auth import (
    CSRFTokenAPIView,
    CurrentUserAPIView,
    LoginAPIView,
    LogoutAPIView
)

urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    # Session-based auth API for the Next.js frontend
    path("api/auth/login/", LoginAPIView.as_view(), name="api-auth-login"),
    path("api/auth/logout/", LogoutAPIView.as_view(), name="api-auth-logout"),
    path("api/auth/user/", CurrentUserAPIView.as_view(), name="api-auth-user"),
    path("api/auth/csrf/", CSRFTokenAPIView.as_view(), name="api-auth-csrf"),
    path(
        "api/fares/create/<int:pk1>/",
        create_fares_dataset_api,
        name="nextjs-fares-create",
    ),
    path(
        "api/fares/review-status/<int:pk1>/<int:pk>/",
        get_fares_review_status_api,
        name="nextjs-fares-review-status",
    ),
    path(
        "api/timetables/review-status/<int:pk1>/<int:pk>/",
        get_timetables_review_status_api,
        name="nextjs-timetables-review-status",
    ),
    path(
        "api/fares/publish/<int:pk1>/<int:pk>/",
        publish_fares_dataset_api,
        name="nextjs-fares-publish",
    ),
    path(
        "contact/",
        TemplateView.as_view(template_name="pages/contact.html"),
        name="contact",
    ),
    path(
        "global-feedback/",
        include(
            [
                path("", GlobalFeedbackView.as_view(), name="global-feedback"),
                path(
                    "thank-you/",
                    GlobalFeedbackThankYouView.as_view(),
                    name="global-feedback-success",
                ),
            ]
        ),
    ),
    path("version/", VersionView.as_view(), name="version"),
    path(
        "cookie/",
        include(
            [
                path("", view=CookieView.as_view(), name="cookie"),
                path("detail", view=CookieDetailView.as_view(), name="cookie-detail"),
            ]
        ),
    ),
    path(
        "accessibility/",
        TemplateView.as_view(template_name="pages/accessibility.html"),
        name="accessibility",
    ),
    path("privacy-policy/", PrivacyPolicyView.as_view(), name="privacy-policy"),
    path("account/", include("config.urls.allauth")),
    path("changelog/", ChangelogView.as_view(), name="changelog"),
    path("django_axe/", include("django_axe.urls")),
    path(
        "robots.txt",
        TemplateView.as_view(
            template_name="pages/robots.txt", content_type="text/plain"
        ),
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

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
