from django.urls import path

from transit_odp.site_admin.views import (
    MetricsDownloadDetailView,
    MetricsDownloadListView,
    MetricsIndexView,
    MetricsOverviewView,
    OperationalMetricsFileView,
)

paths = [
    path("", MetricsIndexView.as_view(), name="bods-metrics"),
    path("overview/", MetricsOverviewView.as_view(), name="overview-metrics"),
    path(
        "download/",
        MetricsDownloadListView.as_view(),
        name="download-metrics",
    ),
    path(
        "download/<int:pk>",
        MetricsDownloadDetailView.as_view(),
        name="download-metrics-detail",
    ),
    path(
        "operations/",
        OperationalMetricsFileView.as_view(),
        name="operational-metrics",
    ),
]
