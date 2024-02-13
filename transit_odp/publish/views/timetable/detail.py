from django.conf import settings
from django_hosts import reverse

import config.hosts
from transit_odp.common.enums import FeedErrorSeverity
from transit_odp.common.views import BaseDetailView
from transit_odp.data_quality.scoring import get_data_quality_rag
from transit_odp.organisation.constants import DatasetType, FeedStatus
from transit_odp.organisation.models import Dataset
from transit_odp.publish.views.utils import (
    get_current_files,
    get_distinct_dataset_txc_attributes,
    get_service_codes_dict,
    get_service_type,
    get_valid_files,
)
from transit_odp.users.views.mixins import OrgUserViewMixin


class FeedDetailView(OrgUserViewMixin, BaseDetailView):
    template_name = "publish/dataset_detail/index.html"
    model = Dataset

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                organisation_id=self.organisation.id,
                dataset_type=DatasetType.TIMETABLE.value,
            )
            .get_published()
            .add_admin_area_names()
            .add_live_data()
            .add_is_live_pti_compliant()
            .select_related("live_revision")
        )

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)

        dataset = self.object
        live_revision = dataset.live_revision
        report = live_revision.report.order_by("-created").first()
        summary = getattr(report, "summary", None)

        kwargs["api_root"] = reverse("api:app:api-root", host=config.hosts.DATA_HOST)
        kwargs["admin_areas"] = self.object.admin_area_names
        kwargs["pk"] = dataset.id
        kwargs["pk1"] = self.kwargs["pk1"]

        severe_errors = live_revision.errors.filter(
            severity=FeedErrorSeverity.severe.value
        )

        status = "success"

        # There shouldn't be severe errors without status == error, but just in case
        # there display error banner
        if severe_errors or (live_revision.status == FeedStatus.error.value):
            status = "error"

        kwargs["status"] = status
        kwargs["severe_errors"] = severe_errors
        kwargs["show_pti"] = (
            live_revision.created.date() >= settings.PTI_START_DATE.date()
        )
        kwargs["pti_enforced_date"] = settings.PTI_ENFORCED_DATE

        kwargs["report_id"] = report.id if summary else None
        kwargs["dq_score"] = get_data_quality_rag(report) if summary else None
        kwargs["distinct_attributes"] = get_distinct_dataset_txc_attributes(
            live_revision.id
        )

        return kwargs


class LineMetadataDetailView(OrgUserViewMixin, BaseDetailView):
    template_name = "publish/dataset_detail/review_line_metadata.html"
    model = Dataset

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                organisation_id=self.organisation.id,
                dataset_type=DatasetType.TIMETABLE.value,
            )
            .get_published()
            .add_admin_area_names()
            .add_live_data()
            .add_is_live_pti_compliant()
            .select_related("live_revision")
        )

    def get_context_data(self, **kwargs):
        line = self.request.GET.get("line")
        kwargs = super().get_context_data(**kwargs)

        dataset = self.object
        live_revision = dataset.live_revision
        kwargs["pk"] = dataset.id
        kwargs["pk1"] = self.kwargs["pk1"]
        kwargs["line_name"] = line
        kwargs["service_codes"] = get_service_codes_dict(live_revision.id, line)
        kwargs["service_type"] = get_service_type(
            live_revision.id, kwargs["service_codes"], kwargs["line_name"]
        )
        kwargs["current_valid_files"] = get_current_files(
            live_revision.id, kwargs["service_codes"], kwargs["line_name"]
        )
        kwargs["api_root"] = reverse("api:app:api-root", host=config.hosts.DATA_HOST)

        if (
            kwargs["service_type"] == "Flexible"
            or kwargs["service_type"] == "Flexible/Standard"
        ):
            booking_arrangements_info = get_valid_files(
                live_revision.id,
                kwargs["current_valid_files"],
                kwargs["service_codes"],
                kwargs["line_name"],
            )
            if booking_arrangements_info:
                kwargs["booking_arrangements"] = booking_arrangements_info[0][0]
                kwargs["booking_methods"] = booking_arrangements_info[0][1:]

        return kwargs
