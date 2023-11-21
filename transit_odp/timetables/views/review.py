from django.conf import settings
from django.utils import timezone
from django.views.generic.detail import DetailView
from django_hosts import reverse

import config.hosts
from transit_odp.data_quality.report_summary import Summary
from transit_odp.data_quality.scoring import get_data_quality_rag
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models import Dataset, TXCFileAttributes
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.publish.forms import RevisionPublishFormViolations
from transit_odp.publish.views.base import BaseDatasetUploadModify, ReviewBaseView
from transit_odp.timetables.views.constants import (
    DATA_QUALITY_LABEL,
    DATA_QUALITY_WITH_VIOLATIONS_LABEL,
    ERROR_CODE_LOOKUP,
)
from transit_odp.users.views.mixins import OrgUserViewMixin


class BaseTimetableReviewView(ReviewBaseView):
    def get_form_class(self):
        if not self.object.is_pti_compliant():
            return RevisionPublishFormViolations
        return super().get_form_class()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if not self.object.is_pti_compliant():
            label = DATA_QUALITY_WITH_VIOLATIONS_LABEL
        else:
            label = DATA_QUALITY_LABEL
        kwargs.update({"consent_label": label, "is_update": False})
        return kwargs

    def get_dataset_queryset(self):
        """Returns a DatasetQuerySet for Timetable datasets owned by
        the user's organisation"""
        queryset = super().get_dataset_queryset()
        return queryset.filter(dataset_type=DatasetType.TIMETABLE)

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .add_admin_area_names()
            .add_error_code()
            .prefetch_related("data_quality_tasks")
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        api_root = reverse("api:app:api-root", host=config.hosts.DATA_HOST)
        revision = self.get_object()
        tasks = revision.data_quality_tasks
        loading = self.is_loading()
        dq_pending_or_failed = tasks.get_latest_status() in ["FAILURE", "PENDING"]
        show_update = (
            self.object.is_pti_compliant() and tasks.get_latest_status() == "SUCCESS"
        )
        pti_deadline_passed = settings.PTI_ENFORCED_DATE.date() <= timezone.localdate()
        context.update(
            {
                "loading": loading,
                "current_step": "upload" if loading else "review",
                "admin_areas": revision.admin_area_names,
                "api_root": api_root,
                "has_pti_observations": not revision.is_pti_compliant(),
                "dq_status": tasks.get_latest_status(),
                "dqs_timeout": settings.DQS_WAIT_TIMEOUT,
                "pti_enforced_date": settings.PTI_ENFORCED_DATE,
                "pti_deadline_passed": pti_deadline_passed,
                "dq_pending_or_failed": dq_pending_or_failed,
                "show_update": show_update,
            }
        )
        if context["dq_status"] == DatasetETLTaskResult.SUCCESS:
            report = tasks.latest().report
            rag = get_data_quality_rag(report)

            context.update(
                {
                    "summary": Summary.from_report_summary(report.summary),
                    "dq_score": rag,
                }
            )

        has_error = bool(revision.error_code)
        if has_error:
            system_error = ERROR_CODE_LOOKUP.get(DatasetETLTaskResult.SYSTEM_ERROR)
            error_context = ERROR_CODE_LOOKUP.get(revision.error_code, system_error)
            context.update({"severe_error": error_context})
        context.update({"error": has_error})

        return context


class PublishRevisionView(BaseTimetableReviewView):
    template_name = "publish/revision_review/index.html"

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
        context = super().get_context_data(**kwargs)
        revision = self.object
        dataset_txc_attributes = self.get_distinct_dataset_txc_attributes(revision.id)
        context.update(
            {"is_update": False, "dataset_txc_attributes": dataset_txc_attributes}
        )
        return context

    def get_success_url(self):
        dataset_id = self.object.dataset_id
        return reverse(
            "revision-publish-success",
            kwargs={"pk": dataset_id, "pk1": self.kwargs["pk1"]},
            host=config.hosts.PUBLISH_HOST,
        )


class UpdateRevisionPublishView(BaseTimetableReviewView):
    template_name = "publish/revision_review/index.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"is_update": True})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"is_update": True})
        return context

    def get_success_url(self):
        dataset_id = self.object.dataset_id
        return reverse(
            "revision-update-success",
            kwargs={"pk": dataset_id, "pk1": self.kwargs["pk1"]},
            host=config.hosts.PUBLISH_HOST,
        )


class RevisionPublishSuccessView(OrgUserViewMixin, DetailView):
    template_name = "publish/revision_publish_success.html"
    model = Dataset

    def get_queryset(self):
        return super().get_queryset().add_is_live_pti_compliant()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "update": False,
                "pti_enforced_date": settings.PTI_ENFORCED_DATE,
                "is_pti_compliant": self.get_object().is_pti_compliant,
            }
        )
        return context


class TimetableUploadModify(BaseDatasetUploadModify):
    pass
