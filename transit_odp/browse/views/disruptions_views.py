from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin

from transit_odp.browse.views.base_views import BaseTemplateView
from transit_odp.common.view_mixins import DownloadView, ResourceCounterMixin
from transit_odp.disruptions.models import DisruptionsDataArchive


class DownloadDisruptionsView(LoginRequiredMixin, BaseTemplateView):
    template_name = "browse/disruptions/download_disruptions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["show_bulk_archive_url"] = DisruptionsDataArchive.objects.exists()
        return context


class DownloadDisruptionsDataArchiveView(ResourceCounterMixin, DownloadView):
    def get_object(self, queryset=None):
        archive = DisruptionsDataArchive.objects.last()

        if archive is None:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": DisruptionsDataArchive._meta.verbose_name}
            )
        return archive

    def get_download_file(self):
        return self.object.data
