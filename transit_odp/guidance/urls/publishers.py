from django.conf import settings
from django.urls import include, path
from django_axe import urls

from transit_odp.data_quality.views.glossary import (
    DataQualityGlossaryView,
    DataQualityScoreGuidanceView,
)

from ..views import BusOperatorReqView, LocalAuthorityReqView, SupportOperatorHomeView

app_name = "guidance"
urlpatterns = [
    path("", view=SupportOperatorHomeView.as_view(), name="operators-home"),
    path(
        "local-authority-requirements/",
        view=LocalAuthorityReqView.as_view(),
        name="support-local_authorities",
    ),
    path(
        "operator-requirements/",
        view=BusOperatorReqView.as_view(),
        name="support-bus_operators",
    ),
    path(
        "data-quality-definitions/",
        view=DataQualityGlossaryView.as_view(),
        name="dq-definitions",
    ),
    path(
        "score-description/",
        view=DataQualityScoreGuidanceView.as_view(),
        name="dq-score-description",
    ),
]

if "django_axe" in settings.INSTALLED_APPS and settings.DJANGO_AXE_ENABLED:
    urlpatterns = [path("axe/", include(urls, namespace="django_axe"))] + urlpatterns
