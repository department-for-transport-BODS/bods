from django.urls import include, path, re_path

from config.settings.base import register_django_axe_url
from transit_odp.users.views.invitations import AcceptInvite

app_name = "invitations"

# django-invitations routes
urlpatterns = (
    [
        # Override invitation routes
        re_path(
            r"^accept-invite/(?P<key>\w+)/?$",
            AcceptInvite.as_view(),
            name="accept-invite",
        ),
        path("", include("invitations.urls")),
        register_django_axe_url(),
    ],
)
