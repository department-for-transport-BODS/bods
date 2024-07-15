from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from django_axe import urls

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

urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
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
    path("axe/", include(urls, namespace="django_axe")),
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
