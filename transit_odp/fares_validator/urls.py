from django.contrib import admin
from django.urls import path
from transit_odp.fares_validator.views.views import FaresXmlValidator
from transit_odp.fares_validator.views.export_excel import FaresXmlExporter


urlpatterns = [
    path('<int:pk2>/export/', FaresXmlExporter.as_view(), name='transit_odp.fares_exporter'),
    path('<int:pk2>/validate/', FaresXmlValidator.as_view(), name = 'transit_odp.fares_validator'),
]