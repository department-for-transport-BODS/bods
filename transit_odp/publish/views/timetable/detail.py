from django.conf import settings
from django_hosts import reverse

import config.hosts
from transit_odp.common.enums import FeedErrorSeverity
from transit_odp.common.views import BaseDetailView
from transit_odp.data_quality.scoring import get_data_quality_rag
from transit_odp.organisation.constants import DatasetType, FeedStatus
from transit_odp.organisation.models import Dataset, TXCFileAttributes
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

    def get_distinct_dataset_txc_attributes(self, revision_id):
        
        distinct_attributes = {}
        distinct_licence_numbers = (
            TXCFileAttributes.objects.filter(revision_id=revision_id)
            .values_list("licence_number", flat=True)
            .distinct()
        )
        for licence_number in distinct_licence_numbers:
            distinct_nocs = (
                TXCFileAttributes.objects.filter(
                    revision_id=revision_id, licence_number=licence_number
                )
                .values_list("national_operator_code", flat=True)
                .distinct()
            )
            license_number_nocs = {}
            
            for noc in distinct_nocs:
                distinct_line_names = (
                    TXCFileAttributes.objects.filter(
                        revision_id=revision_id,
                        licence_number=licence_number,
                        national_operator_code=noc,
                    )
                    .values_list("line_names", flat=True)
                    .distinct()
                )
                noc_line_service_codes = {}

                for line_name in distinct_line_names:
                    distinct_service_codes = (
                        TXCFileAttributes.objects.filter(
                            revision_id=revision_id,
                            licence_number=licence_number,
                            national_operator_code=noc,
                            line_names=line_name
                        )
                        .values_list("service_code", flat=True)
                        .distinct()
                    )
                    noc_line_service_codes[line_name[0]] = ', '.join(map(str, distinct_service_codes))
                license_number_nocs[noc] = noc_line_service_codes
        
            distinct_attributes[licence_number] = license_number_nocs

        return distinct_attributes


    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)

        dataset = self.object
        live_revision = dataset.live_revision
        report = live_revision.report.order_by("-created").first()
        summary = getattr(report, "summary", None)

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

        kwargs["report_id"] = report.id if summary else None
        kwargs["dq_score"] = get_data_quality_rag(report) if summary else None

        distinct_attributes = self.get_distinct_dataset_txc_attributes(live_revision.id)
        kwargs["distinct_attributes"] = distinct_attributes

        return kwargs
