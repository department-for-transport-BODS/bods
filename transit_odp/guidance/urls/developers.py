from django.urls import path

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
