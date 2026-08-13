from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import DetailView

from transit_odp.browse.cfn import generate_signed_url
from transit_odp.site_admin.constants import DataCatalogue
from transit_odp.site_admin.models import DocumentArchive


class DownloadDataCatalogueView(DetailView):
    model = DocumentArchive

    def get_queryset(self):
        return super().get_queryset().filter(category=DataCatalogue)

    def get_object(self, queryset=None):
        obj = self.get_queryset().last()
        if obj is None:
            raise Http404()
        return obj

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        return redirect(
            generate_signed_url(f"data-catalogue/{self.object.archive.name}")
        )
