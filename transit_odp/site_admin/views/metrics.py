from django.contrib.auth import get_user_model
from django.http.response import Http404
from django.views.generic import DetailView, ListView, TemplateView

from transit_odp.site_admin.constants import OperationalMetrics
from transit_odp.site_admin.models import DocumentArchive, MetricsArchive
from transit_odp.users.views.mixins import SiteAdminViewMixin

__all__ = [
    "MetricsDownloadDetailView",
    "MetricsDownloadListView",
    "MetricsDownloadListView",
    "MetricsIndexView",
    "MetricsOverviewView",
    "OperationalMetricsFileView",
]

User = get_user_model()


class MetricsIndexView(SiteAdminViewMixin, TemplateView):
    template_name = "site_admin/metrics/index.html"


class MetricsOverviewView(SiteAdminViewMixin, TemplateView):
    template_name = "site_admin/metrics/overview.html"


class MetricsDownloadListView(SiteAdminViewMixin, ListView):
    template_name = "site_admin/metrics/download.html"
    model = MetricsArchive
    queryset = MetricsArchive.objects.order_by("-start")[:12]


class MetricsDownloadDetailView(SiteAdminViewMixin, DetailView):
    model = MetricsArchive

    def get(self, *args, **kwargs):
        metric = self.get_object()
        return metric.to_http_response()


class OperationalMetricsFileView(SiteAdminViewMixin, DetailView):
    """A view for downloading BODS operational metrics zip file."""

    model = DocumentArchive

    def get_queryset(self):
        return super().get_queryset().filter(category=OperationalMetrics)

    def get_object(self, queryset=None):
        obj = self.get_queryset().last()
        if obj is None:
            raise Http404()
        return obj

    def get(self, *args, **kwargs):
        return self.get_object().to_http_response()
