import csv

from django.http import HttpResponse
from django.views.generic import ListView, TemplateView
from django_filters.views import FilterView

from transit_odp.browse.serializers import DatasetCatalogueSerializer
from transit_odp.common.view_mixins import BODSBaseView
from transit_odp.organisation.models import Dataset, Organisation


class BaseFilterView(BODSBaseView, FilterView):
    pass


class BaseTemplateView(BODSBaseView, TemplateView):
    pass


class BaseListView(BODSBaseView, ListView):
    pass


class BrowseHomeView(BaseTemplateView):
    template_name = "browse/home.html"


class SearchSelectView(BaseTemplateView):
    template_name = "browse/search_select.html"


class DownloadsView(BaseTemplateView):
    template_name = "browse/downloads.html"


class ApiSelectView(BaseTemplateView):
    template_name = "browse/api_select.html"


class DownloadDataCatalogueView(BaseTemplateView):
    template_name = "browse/download_catalogue.html"


class DownloadOperatorNocCatalogueView(BaseListView):
    model = Organisation
    ordering = ("name", "nocs__noc")

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(is_active=True).prefetch_related("nocs")

    def render_to_response(self, context, **response_kwargs):
        self.object_list = self.get_queryset()
        response = HttpResponse(content_type="text/csv")
        response[
            "Content-Disposition"
        ] = 'attachment; filename="operator_noc_mapping.csv"'

        writer = csv.writer(response, quoting=csv.QUOTE_ALL)
        writer.writerow(["operator", "noc"])

        orgs = self.object_list.values_list("name", "nocs__noc")
        for org in orgs:
            writer.writerow(org)

        return response


class DownloadOperatorDatasetCatalogueView(BaseListView):
    serializer_class = DatasetCatalogueSerializer

    def get_serializer(self, queryset, many=True):
        return self.serializer_class(
            queryset,
            many=many,
        )

    def get_queryset(self):
        return (
            Dataset.objects.get_active_org()
            .get_published()
            .select_related("organisation")
            .select_related("live_revision")
            .add_organisation_name()
            .order_by("organisation_name", "dataset_type")
        )

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv")
        response[
            "Content-Disposition"
        ] = 'attachment; filename="operator_dataID_mapping.csv"'
        serializer = self.get_serializer(self.get_queryset(), many=True)

        writer = csv.DictWriter(response, fieldnames=self.serializer_class.Meta.fields)
        writer.writeheader()

        for data in serializer.data:
            writer.writerow(data)

        return response
