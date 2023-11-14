from django.urls import include, path, re_path

from transit_odp.users.views.account import (
    EmailView,
    PasswordChangeDoneView,
    PasswordChangeView,
)
from transit_odp.users.views.auth import (
    ConfirmEmailView,
    EmailVerificationSentView,
    LoginView,
    LogoutSuccessView,
    PasswordResetDoneView,
    PasswordResetFromKeyView,
    PasswordResetView,
    SignupView,
)

urlpatterns = [
    # Custom views
    path(
        "logout-success/",
        view=LogoutSuccessView.as_view(),
        name="account_logout_success",
    ),
    # Override specific AllAuth views
    path("login/", view=LoginView.as_view(), name="account_login"),
    path("signup/", view=SignupView.as_view(), name="account_signup"),
    path(
        "password/change/",
        view=PasswordChangeView.as_view(),
        name="account_change_password",
    ),
    path(
        "password/change/done/",
        view=PasswordChangeDoneView.as_view(),
        name="account_change_password_done",
    ),
    # email
    path("email/", view=EmailView.as_view(), name="account_email"),
    path(
        "confirm-email/",
        EmailVerificationSentView.as_view(),
        name="account_email_verification_sent",
    ),
    path(
        "confirm-email/<str:key>/",
        ConfirmEmailView.as_view(),
        name="account_confirm_email",
    ),
    # password reset
    path("password/reset/", PasswordResetView.as_view(), name="account_reset_password"),
    path(
        "password/reset/done/",
        PasswordResetDoneView.as_view(),
        name="account_reset_password_done",
    ),
    re_path(
        r"^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$",
        PasswordResetFromKeyView.as_view(),
        name="account_reset_password_from_key",
    ),
    # Include AllAuth views
    path("", include("allauth.urls")),
]
