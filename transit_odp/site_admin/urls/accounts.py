from django.urls import path

from transit_odp.users.views.account import (
    MyAccountView,
    SettingsView,
    UserRedirectView,
)

paths = [
    path("", view=MyAccountView.as_view(), name="home"),
    path(
        "settings/",
        view=SettingsView.as_view(),
        name="settings",
    ),
    # Used to redirect back to user's account page
    path(
        "~redirect/",
        view=UserRedirectView.as_view(),
        name="redirect",
    ),
]
