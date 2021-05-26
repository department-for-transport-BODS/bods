from django.urls import path

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
