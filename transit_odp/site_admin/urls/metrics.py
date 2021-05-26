from django.urls import path

from transit_odp.site_admin.views import (
    APIMetricsFileView,
    MetricsDownloadView,
    OperationalMetricsFileView,
)

paths = [
    path("", MetricsDownloadView.as_view(), name="bods-metrics"),
    path(
        "operations/",
        OperationalMetricsFileView.as_view(),
        name="operational-metrics",
    ),
    path(
        "apis/",
        APIMetricsFileView.as_view(),
        name="api-metrics",
    ),
]
