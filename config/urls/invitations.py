from django.conf.urls import url
from django.urls import include, path

from transit_odp.users.views.invitations import AcceptInvite

app_name = "invitations"

# django-invitations routes
urlpatterns = [
    # Override invitation routes
    url(
        r"^accept-invite/(?P<key>\w+)/?$", AcceptInvite.as_view(), name="accept-invite"
    ),
    path("", include("invitations.urls")),
]
