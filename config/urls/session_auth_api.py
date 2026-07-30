from django.urls import path

from transit_odp.api.views.auth import (
    CSRFTokenAPIView,
    CurrentUserAPIView,
    LoginAPIView,
    LogoutAPIView,
)

urlpatterns = [
    path("login/", LoginAPIView.as_view(), name="api-auth-login"),
    path("logout/", LogoutAPIView.as_view(), name="api-auth-logout"),
    path("user/", CurrentUserAPIView.as_view(), name="api-auth-user"),
    path("csrf/", CSRFTokenAPIView.as_view(), name="api-auth-csrf"),
]
