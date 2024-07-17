from django.urls import include, path

from transit_odp.fares_validator.views.export_excel import FaresXmlExporter
from transit_odp.fares_validator.views.views import FaresXmlValidator

urlpatterns = [
    path(
        "<int:pk2>/export/",
        FaresXmlExporter.as_view(),
        name="transit_odp.fares_exporter",
    ),
    path(
        "<int:pk2>/validate/",
        FaresXmlValidator.as_view(),
        name="transit_odp.fares_validator",
    ),
    path("django_axe/", include("django_axe.urls")),
]
