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
    server_error,
)
from transit_odp.common.views import (
    CookieDetailView,
    CookieView,
    PrivacyPolicyView,
    VersionView,
)
from transit_odp.fares.views.api import (
    create_fares_dataset_api,
    deactivate_fares_dataset_api,
    delete_fares_dataset_api,
    get_fares_list_api,
    get_fares_review_status_api,
    publish_fares_dataset_api,
    update_fares_dataset_api,
)
from transit_odp.avl.views.api import (
    create_avl_dataset_api,
    delete_avl_dataset_api,
    edit_avl_dataset_description_api,
    get_avl_requires_attention_api,
    get_avl_changelog_api,
    get_avl_dataset_edit_api,
    get_avl_feed_detail_api,
    get_avl_review_status_api,
    get_avl_update_context_api,
    list_avl_datasets_api,
    publish_avl_dataset_api,
    update_avl_dataset_api,
)
from transit_odp.timetables.views.api import (
    create_timetables_dataset_api,
    get_timetables_review_status_api,
    publish_timetables_dataset_api,
)

handler500 = "transit_odp.common.utils.custom_error_handlers.server_error"

urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path("api/", include("config.urls.nextjs_api")),
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
        path("500/", server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
