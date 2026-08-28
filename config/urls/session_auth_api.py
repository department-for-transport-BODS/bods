from django.urls import path

from transit_odp.api.views.auth import (
    ConfirmEmailAPIView,
    CSRFTokenAPIView,
    CurrentUserAPIView,
    InviteAcceptAPIView,
    LoginAPIView,
    LogoutAPIView,
    PasswordChangeAPIView,
    PasswordResetAPIView,
    PasswordResetFromKeyAPIView,
    SignupAPIView,
)
from transit_odp.users.views.api import (
    get_account_api,
    get_account_settings_api,
    get_agent_invite_api,
    get_subscriptions_api,
    leave_agent_organisation_api,
    remove_agent_from_organisation_api,
    resend_agent_invite_api,
    respond_agent_invite_api,
    update_account_settings_api,
    update_subscriptions_mute_api,
)

# Mounted at api/auth/ on every service host (www, data, publish, admin) so the
# session cookie and CSRF origin check stay on the host the user signed in from.
urlpatterns = [
    path("login/", LoginAPIView.as_view(), name="api-auth-login"),
    path("logout/", LogoutAPIView.as_view(), name="api-auth-logout"),
    path("signup/", SignupAPIView.as_view(), name="api-auth-signup"),
    path(
        "invite/accept/",
        InviteAcceptAPIView.as_view(),
        name="api-auth-invite-accept",
    ),
    path(
        "confirm-email/",
        ConfirmEmailAPIView.as_view(),
        name="api-auth-confirm-email",
    ),
    path("user/", CurrentUserAPIView.as_view(), name="api-auth-user"),
    path("csrf/", CSRFTokenAPIView.as_view(), name="api-auth-csrf"),
    path(
        "password/change/",
        PasswordChangeAPIView.as_view(),
        name="api-auth-password-change",
    ),
    path(
        "password/reset/",
        PasswordResetAPIView.as_view(),
        name="api-auth-password-reset",
    ),
    path(
        "password/reset/key/",
        PasswordResetFromKeyAPIView.as_view(),
        name="api-auth-password-reset-key",
    ),
    path("settings/", get_account_settings_api, name="api-auth-settings"),
    path(
        "settings/update/",
        update_account_settings_api,
        name="api-auth-settings-update",
    ),
    path("account/", get_account_api, name="api-auth-account"),
    path("subscriptions/", get_subscriptions_api, name="api-auth-subscriptions"),
    path(
        "subscriptions/mute/",
        update_subscriptions_mute_api,
        name="api-auth-subscriptions-mute",
    ),
    path("agent/invite/<int:pk>/", get_agent_invite_api, name="api-auth-agent-invite"),
    path(
        "agent/invite/<int:pk>/respond/",
        respond_agent_invite_api,
        name="api-auth-agent-invite-respond",
    ),
    path(
        "agent/invite/<int:pk>/leave/",
        leave_agent_organisation_api,
        name="api-auth-agent-invite-leave",
    ),
    path(
        "agent/invite/<int:pk>/remove/",
        remove_agent_from_organisation_api,
        name="api-auth-agent-invite-remove",
    ),
    path(
        "agent/invite/<int:pk>/resend/",
        resend_agent_invite_api,
        name="api-auth-agent-invite-resend",
    ),
]
