from django.conf import settings
from django.urls import include, path, re_path

from transit_odp.users.views.invitations import AcceptInvite

app_name = "invitations"

# django-invitations routes
urlpatterns = [
    # Override invitation routes
    re_path(
        r"^accept-invite/(?P<key>\w+)/?$", AcceptInvite.as_view(), name="accept-invite"
    ),
    path("", include("invitations.urls")),
]

if "django_axe" in settings.INSTALLED_APPS and settings.DJANGO_AXE_ENABLED:
    urlpatterns = [path("django_axe/", include("django_axe.urls"))] + urlpatterns
