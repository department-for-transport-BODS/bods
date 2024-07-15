from django.urls import include, path
from django_axe import urls

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
    path("axe/", include(urls, namespace="django_axe")),
]
