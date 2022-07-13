from django.conf import settings
from django_hosts import reverse

import config.hosts
from transit_odp.common.enums import FeedErrorSeverity
from transit_odp.common.views import BaseDetailView
from transit_odp.data_quality.models.report import DataQualityReport
from transit_odp.data_quality.scoring import get_data_quality_rag
from transit_odp.organisation.constants import DatasetType, FeedStatus
from transit_odp.organisation.models import Dataset
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

        kwargs["api_root"] = reverse("api:app:api-root", host=config.hosts.DATA_HOST)
        kwargs["admin_areas"] = self.object.admin_area_names
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

        try:
            report = live_revision.report.latest()
        except DataQualityReport.DoesNotExist:
            return kwargs

        kwargs["report_id"] = report.id
        kwargs["dq_score"] = get_data_quality_rag(report)

        return kwargs
