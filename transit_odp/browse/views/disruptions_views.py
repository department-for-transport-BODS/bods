from transit_odp.browse.views.base_views import BaseTemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

class DownloadDisruptionsView(LoginRequiredMixin, BaseTemplateView):
    template_name = "browse/disruptions/download_disruptions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context