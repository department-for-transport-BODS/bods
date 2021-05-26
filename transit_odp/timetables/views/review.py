from django.conf import settings
from django.views.generic import TemplateView
from django_hosts import reverse

import config.hosts
from transit_odp.data_quality.constants import OBSERVATIONS
from transit_odp.data_quality.report_summary import Summary
from transit_odp.data_quality.scoring import (
    DataQualityCalculator,
    DataQualityRAG,
    DQScoreException,
)
from transit_odp.organisation.constants import DatasetType
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
        if self.object.pti_observations.count() > 0:
            return RevisionPublishFormViolations
        return super().get_form_class()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.object.pti_observations.count() > 0:
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
        context.update(
            {
                "loading": loading,
                "current_step": "upload" if loading else "review",
                "admin_areas": revision.admin_area_names,
                "api_root": api_root,
                "has_pti_observations": self.object.pti_observations.count() > 0,
                "dq_status": tasks.get_latest_status(),
                "dqs_timeout": settings.DQS_WAIT_TIMEOUT,
            }
        )
        if context["dq_status"] == DatasetETLTaskResult.SUCCESS:
            report = tasks.latest().report
            score_observations = [o for o in OBSERVATIONS if o.model and o.weighting]
            calculator = DataQualityCalculator(score_observations)

            try:
                score = calculator.calculate(report_id=report.id)
            except DQScoreException:
                rag = None
            else:
                rag = DataQualityRAG.from_score(score)

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"is_update": False})
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


class RevisionPublishSuccessView(OrgUserViewMixin, TemplateView):
    template_name = "publish/revision_publish_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"update": False})
        return context


class TimetableUploadModify(BaseDatasetUploadModify):
    pass
