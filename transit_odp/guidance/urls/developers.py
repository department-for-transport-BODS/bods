from django.conf import settings
from django.urls import include, path

from ..views import DeveloperGuidanceHomeView, DeveloperReqView

app_name = "guidance"
urlpatterns = [
    path(
        "",
        view=DeveloperGuidanceHomeView.as_view(),
        name="developers-home",
    ),
    path(
        "requirements/",
        view=DeveloperReqView.as_view(),
        name="support-developer",
    ),
]
if "django_axe" in settings.INSTALLED_APPS and settings.DJANGO_AXE_ENABLED:
    urlpatterns = [path("django_axe/", include("django_axe.urls"))] + urlpatterns
