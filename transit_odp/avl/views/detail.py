from datetime import datetime
from typing import Optional, TypedDict

import pytz
from django.db.models import ObjectDoesNotExist
from django.http import FileResponse
from django.views.generic import DetailView

from transit_odp.avl.models import PostPublishingCheckReport, PPCReportType
from transit_odp.avl.proxies import AVLDataset
from transit_odp.common.views import BaseDetailView
from transit_odp.users.views.mixins import OrgUserViewMixin


class AvlFeedDetailView(OrgUserViewMixin, BaseDetailView):
    template_name = "avl/avl_feed_detail/index.html"
    model = AVLDataset

    class Properties(TypedDict):
        dataset_id: int
        name: str
        description: str
        short_description: str
        status: str
        organisation_name: str
        organisation_id: int
        siri_version: str
        url_link: str
        last_modified: str
        last_modified_user: Optional[str]
        last_server_update: str
        published_by: Optional[str]
        published_at: str
        avl_compliance_status_cached: str
        avl_timetables_matching: Optional[str]
        has_schema_violations: bool
        days_to_go: int
        first_error_date: datetime
        is_dummy: bool

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .filter(
                organisation_id=self.organisation.id,
            )
            .add_has_schema_violation_reports()
            .add_avl_report_count()
            .add_first_error_date()
            .get_published()
            .add_avl_compliance_status_cached()
            .select_related("live_revision")
        )
        return qs

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)

        dataset = self.object
        revision = dataset.live_revision

        last_modified_username = None
        if revision.last_modified_user is not None:
            last_modified_username = revision.last_modified_user.username

        published_by = None
        if revision.published_by is not None:
            published_by = revision.published_by.username

        kwargs["pk1"] = self.kwargs["pk1"]

        last_server_update = ""
        if dataset.avl_feed_last_checked is not None:
            last_server_update = dataset.avl_feed_last_checked.astimezone(
                pytz.timezone("Europe/London")
            ).strftime("%d %b %Y %H:%M")

        ppc_weekly_score = None
        try:
            ppc_avl_dataset = (
                PostPublishingCheckReport.objects.filter(granularity="weekly")
                .filter(dataset__id=self.object.id)
                .order_by("-created")
            ).first()
            ppc_weekly_score = (
                str(
                    ppc_avl_dataset.vehicle_activities_completely_matching
                    * 100
                    // ppc_avl_dataset.vehicle_activities_analysed,
                )
                + "%"
            )
        except (ObjectDoesNotExist, ZeroDivisionError, AttributeError):
            return str(0) + "%"

        if hasattr(revision, "metadata"):
            siri_version = revision.metadata.schema_version
        else:
            siri_version = "_"

        kwargs["properties"] = self.Properties(
            dataset_id=dataset.id,
            name=revision.name,
            description=revision.description,
            short_description=revision.short_description,
            status=revision.status,
            organisation_name=dataset.organisation.name,
            organisation_id=dataset.organisation_id,
            siri_version=siri_version,
            url_link=revision.url_link,
            last_modified=revision.modified,
            last_modified_user=last_modified_username,
            last_server_update=last_server_update,
            published_by=published_by,
            published_at=revision.published_at,
            avl_compliance_status_cached=dataset.avl_compliance_status_cached,
            avl_timetables_matching=ppc_weekly_score,
            has_schema_violations=dataset.has_schema_violations,
            days_to_go=7 - dataset.avl_report_count,
            first_error_date=dataset.first_error_date,
            is_dummy=dataset.is_dummy,
        )
        return kwargs


class ValidationFileDownloadView(BaseDetailView):
    model = AVLDataset

    def get(self, *args, **kwargs):
        return self.get_object().to_validation_reports_response()


class SchemaValidationFileDownloadView(OrgUserViewMixin, BaseDetailView):
    model = AVLDataset

    def get(self, *args, **kwargs):
        return self.get_object().to_schema_validation_response()


class DownloadPPCWeeklyReportView(DetailView):
    model = AVLDataset

    def get(self, *args, **kwargs):
        dataset_id = self.kwargs["pk"]
        self.ppc_avl_dataset = (
            PostPublishingCheckReport.objects.filter(
                dataset__id=dataset_id, granularity=PPCReportType.WEEKLY
            )
            .order_by("-created")
            .first()
        )
        return self.render_to_response()

    def render_to_response(self):
        response = FileResponse(self.ppc_avl_dataset.file)
        response[
            "Content-Disposition"
        ] = f"attachment; filename={self.ppc_avl_dataset.file.name}"
        return response
