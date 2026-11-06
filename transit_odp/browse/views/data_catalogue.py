import logging

from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import DetailView
from waffle import flag_is_active
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from transit_odp.browse.cfn import generate_signed_url
from transit_odp.site_admin.constants import DataCatalogue
from transit_odp.site_admin.models import DocumentArchive

logger = logging.getLogger(__name__)


class DataCatalogueDownloadURLAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        catalogue = DocumentArchive.objects.filter(category=DataCatalogue).last()
        if catalogue is None:
            return Response(status=404)

        try:
            download_url = generate_signed_url(
                f"data-catalogue/{catalogue.archive.name}"
            )
        except Exception:
            logger.exception("Unable to generate the data catalogue download URL.")
            return Response(
                {"detail": "Unable to generate the data catalogue download URL."},
                status=500,
            )

        return Response({"url": download_url})


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
