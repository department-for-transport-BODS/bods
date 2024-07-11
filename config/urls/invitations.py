from django.urls import include, path, re_path

from transit_odp.users.views.invitations import AcceptInvite
from transit_odp.api.views.acc import write_acc

app_name = "invitations"

# django-invitations routes
urlpatterns = [
    # Override invitation routes
    re_path(
        r"^accept-invite/(?P<key>\w+)/?$", AcceptInvite.as_view(), name="accept-invite"
    ),
    path("", include("invitations.urls")),
    path("api/acc/", write_acc, name="write_acc"),
]
