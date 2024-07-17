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
    path("django_axe/", include("django_axe.urls")),
]
