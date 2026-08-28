import pytest
from django.conf import settings
from django.urls import resolve


@pytest.mark.parametrize(
    "urlconf",
    [
        settings.ROOT_URLCONF,
        settings.DATA_URLCONF,
        settings.PUBLISH_URLCONF,
        settings.ADMIN_URLCONF,
    ],
)
@pytest.mark.parametrize(
    ("path", "view_name"),
    [
        ("/api/auth/login/", "api-auth-login"),
        ("/api/auth/logout/", "api-auth-logout"),
        ("/api/auth/signup/", "api-auth-signup"),
        ("/api/auth/confirm-email/", "api-auth-confirm-email"),
        ("/api/auth/user/", "api-auth-user"),
        ("/api/auth/csrf/", "api-auth-csrf"),
        ("/api/auth/password/change/", "api-auth-password-change"),
        ("/api/auth/password/reset/", "api-auth-password-reset"),
        ("/api/auth/password/reset/key/", "api-auth-password-reset-key"),
        ("/api/auth/settings/", "api-auth-settings"),
        ("/api/auth/settings/update/", "api-auth-settings-update"),
        ("/api/auth/account/", "api-auth-account"),
        ("/api/auth/subscriptions/", "api-auth-subscriptions"),
        ("/api/auth/subscriptions/mute/", "api-auth-subscriptions-mute"),
        ("/api/auth/agent/invite/1/", "api-auth-agent-invite"),
    ],
)
def test_session_auth_api_is_available_on_every_nextjs_host(urlconf, path, view_name):
    assert resolve(path, urlconf=urlconf).view_name == view_name


@pytest.mark.parametrize("urlconf", [settings.ROOT_URLCONF, settings.PUBLISH_URLCONF])
@pytest.mark.parametrize(
    ("path", "view_name"),
    [
        ("/api/organisations/", "api-user-organisations"),
        ("/api/avl/list/1/", "nextjs-avl-list"),
        ("/api/avl/update-context/1/2/", "nextjs-avl-update-context"),
        ("/api/avl/requires-attention/1/", "nextjs-avl-requires-attention"),
        ("/api/fares/list/1/", "nextjs-fares-list"),
        (
            "/api/timetables/review-status/1/2/",
            "nextjs-timetables-review-status",
        ),
    ],
)
def test_application_api_is_shared_by_www_and_publish(urlconf, path, view_name):
    assert resolve(path, urlconf=urlconf).view_name == view_name
