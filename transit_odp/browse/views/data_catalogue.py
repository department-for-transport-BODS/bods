import csv

from django.db.models import F
from django.http import HttpResponse
from django.views import View

from transit_odp.browse.views.base_views import BaseListView
from transit_odp.common.csv import CSVBuilder, CSVColumn
from transit_odp.organisation.constants import AVLType, FeedStatus
from transit_odp.organisation.models import Dataset, Organisation


def get_feed_status(dataset):
    if (
        dataset.dataset_type == AVLType
        and dataset.live_revision.status == FeedStatus.error.value
    ):
        return "No vehicle activity"
    if dataset.live_revision.status == "live":
        return "published"

    return dataset.live_revision.status


class OperatorDataCatalogueCSV(CSVBuilder):
    columns = [
        CSVColumn(header="operator", accessor="organisation_name"),
        CSVColumn(header="operatorID", accessor="organisation_id"),
        CSVColumn(header="dataType", accessor="pretty_dataset_type"),
        CSVColumn(header="status", accessor=get_feed_status),
        CSVColumn(header="lastUpdated", accessor="modified"),
        CSVColumn(header="dataID", accessor="id"),
        CSVColumn(
            header="BODSCompliantData",
            accessor=lambda d: "yes" if d.is_pti_compliant else "no",
        ),
        CSVColumn(
            header="DQScore", accessor=lambda d: f"{d.score*100:.0f}" if d.score else ""
        ),
        CSVColumn(header="NationalOperatorCode", accessor="nocs"),
        CSVColumn(header="serviceCode", accessor="service_codes"),
    ]

    def get_queryset(self):
        return (
            Dataset.objects.get_active_org()
            .get_published()
            .select_related("organisation", "live_revision")
            .order_by("organisation__name", "dataset_type")
            .annotate(organisation_name=F("organisation__name"))
            .add_is_live_pti_compliant()
            .get_live_dq_score()
            .add_nocs(delimiter=";")
            .add_service_code(delimiter=";")
        )


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


class DownloadOperatorDatasetCatalogueView(View):
    def render_to_response(self, *args, **kwargs):
        filename = "operator_dataID_mapping.csv"
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        builder = OperatorDataCatalogueCSV()
        response.content = builder.to_string()
        return response

    def get(self, *args, **kwargs):
        return self.render_to_response()
