from django.conf import settings
from django.utils import timezone
from django.views.generic.detail import DetailView
from django_hosts import reverse

import config.hosts
from transit_odp.data_quality.report_summary import Summary
from transit_odp.data_quality.scoring import get_data_quality_rag
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models import Dataset
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.dqs.models import Report
from transit_odp.dqs.constants import ReportStatus
from transit_odp.publish.forms import RevisionPublishFormViolations
from transit_odp.publish.views.base import BaseDatasetUploadModify, ReviewBaseView
from transit_odp.publish.views.utils import (
    get_current_files,
    get_distinct_dataset_txc_attributes,
    get_revision_details,
    get_service_type,
    get_valid_files,
)
from transit_odp.timetables.views.constants import (
    DATA_QUALITY_LABEL,
    DATA_QUALITY_WITH_VIOLATIONS_LABEL,
    ERROR_CODE_LOOKUP,
)
from transit_odp.users.views.mixins import OrgUserViewMixin
from datetime import datetime
import pandas as pd
from transit_odp.browse.timetable_visualiser import TimetableVisualiser
from typing import Dict
import math
import re
from waffle import flag_is_active


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
        is_new_data_quality_service_active = flag_is_active(
            "", "is_new_data_quality_service_active"
        )
        kwargs[
            "is_new_data_quality_service_active"
        ] = is_new_data_quality_service_active

        context = super().get_context_data(**kwargs)
        api_root = reverse("api:app:api-root", host=config.hosts.DATA_HOST)
        revision = self.get_object()
        tasks = revision.data_quality_tasks
        loading = self.is_loading()

        show_update = (
            self.object.is_pti_compliant() and tasks.get_latest_status() == "SUCCESS"
        )
        pti_deadline_passed = settings.PTI_ENFORCED_DATE.date() <= timezone.localdate()
        if is_new_data_quality_service_active:
            report = (
                Report.objects.filter(revision_id=revision.id)
                .order_by("-created")
                .filter(
                    status__in=[
                        ReportStatus.REPORT_GENERATED.value,
                        ReportStatus.REPORT_GENERATION_FAILED.value,
                    ]
                )
                .first()
            )
            dq_pending_or_failed = True
            report_id = report.id if report else None
            dq_status = "PENDING"
            if report_id:
                dq_status = "SUCCESS"
                dq_pending_or_failed = False
            context.update(
                {
                    "loading": loading,
                    "current_step": "upload" if loading else "review",
                    "admin_areas": revision.admin_area_names,
                    "api_root": api_root,
                    "has_pti_observations": not revision.is_pti_compliant(),
                    "dq_status": dq_status,
                    "dqs_timeout": settings.DQS_WAIT_TIMEOUT,
                    "pti_enforced_date": settings.PTI_ENFORCED_DATE,
                    "pti_deadline_passed": pti_deadline_passed,
                    "dq_pending_or_failed": dq_pending_or_failed,
                    "show_update": True,
                    "is_new_data_quality_service_active": is_new_data_quality_service_active,
                }
            )
        else:
            dq_pending_or_failed = tasks.get_latest_status() in ["FAILURE", "PENDING"]
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
                    "is_new_data_quality_service_active": is_new_data_quality_service_active,
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        revision = self.object

        is_new_data_quality_service_active = flag_is_active(
            "", "is_new_data_quality_service_active"
        )
        kwargs[
            "is_new_data_quality_service_active"
        ] = is_new_data_quality_service_active

        if is_new_data_quality_service_active:
            report = (
                Report.objects.filter(revision_id=revision.id)
                .order_by("-created")
                .filter(
                    status__in=[
                        ReportStatus.REPORT_GENERATED.value,
                        ReportStatus.REPORT_GENERATION_FAILED.value,
                    ]
                )
                .first()
            )
            report_id = report.id if report else None
            summary = None
            if report_id:
                summary = Summary.get_report(report_id, revision.id)

            context.update(
                {
                    "pk": revision.dataset_id,
                    "is_update": False,
                    "distinct_attributes": get_distinct_dataset_txc_attributes(
                        revision.id
                    ),
                    "report_id": report_id,
                    "is_new_data_quality_service_active": is_new_data_quality_service_active,
                    "summary": summary,
                }
            )
        else:
            context.update(
                {
                    "pk": revision.dataset_id,
                    "is_update": False,
                    "distinct_attributes": get_distinct_dataset_txc_attributes(
                        revision.id
                    ),
                }
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


class LineMetadataRevisionView(OrgUserViewMixin, DetailView):
    template_name = "publish/revision_review/review_line_metadata.html"
    model = Dataset

    def get_queryset(self):
        return super().get_queryset()

    def get_direction_timetable(
        self, df_timetable: pd.DataFrame, direction: str = "outbound"
    ) -> Dict:

        """
        Get the timetable details like the total, current page and the dataframe
        based on the timetable dataframe and the direction.

        :param df_timetable pd.DataFrame
        Timetable visualiser dataframe
        :param direction string
        Possible values can be 'outbound' or 'inbound'

        :return Dict
        {
            'total_page': "Total pages of the dataframe",
            'curr_page': "Current page",
            'show_all': "Flag to show all rows in dataframe",
            'df_timetable': "Dataframe sliced with rows and columns"
        }
        """

        if df_timetable.empty:
            return {
                "total_page": 0,
                "curr_page": 1,
                "show_all": False,
                "df_timetable": pd.DataFrame(),
                "total_row_count": 0,
            }

        if direction == "outbound":
            show_all_param = self.request.GET.get("showAllOutbound", "false")
            curr_page_param = int(self.request.GET.get("outboundPage", "1"))
        else:
            show_all_param = self.request.GET.get("showAllInbound", "false")
            curr_page_param = int(self.request.GET.get("inboundPage", "1"))
            pass

        show_all = show_all_param.lower() == "true"
        total_row_count, total_columns_count = df_timetable.shape
        total_page = math.ceil((total_columns_count - 1) / 10)
        curr_page_param = 1 if curr_page_param > total_page else curr_page_param
        page_size = 10
        # Adding 1 to always show the first column of stops
        col_start = ((curr_page_param - 1) * page_size) + 1
        col_end = min(total_columns_count, (curr_page_param * page_size) + 1)
        col_indexes_display = []
        for i in range(col_start, col_end):
            col_indexes_display.append(i)
        if len(col_indexes_display) > 0:
            col_indexes_display.insert(0, 0)
        row_count = min(total_row_count, 10)
        # Slice the dataframe by the 10 rows if show all is false
        df_timetable = (
            df_timetable.iloc[:, col_indexes_display]
            if show_all
            else df_timetable.iloc[:row_count, col_indexes_display]
        )

        return {
            "total_page": total_page,
            "curr_page": curr_page_param,
            "show_all": show_all,
            "df_timetable": df_timetable,
            "total_row_count": total_row_count,
        }

    def get_context_data(self, **kwargs):

        """
        Get the context data for the view.

        This method retrieves various contextual data based on the request parameters
        and the object's attributes.
        """
        line = self.request.GET.get("line")
        revision_id = self.request.GET.get("revision_id")
        service_code = self.request.GET.get("service")
        context = super().get_context_data(**kwargs)
        dataset = self.object
        revision = get_revision_details(dataset.id)
        context.update(
            {
                "line_name": line,
                "pk1": dataset.organisation_id,
                "pk": dataset.id,
                "feed_name": revision[1],
            }
        )
        context["service_code"] = service_code
        context["service_type"] = get_service_type(
            revision[0], context["service_code"], context["line_name"]
        )
        context["current_valid_files"] = get_current_files(
            revision[0], context["service_code"], context["line_name"]
        )

        context["api_root"] = reverse("api:app:api-root", host=config.hosts.DATA_HOST)
        context["revision_id"] = revision_id

        if (
            context["service_type"] == "Flexible"
            or context["service_type"] == "Flexible/Standard"
        ):
            booking_arrangements_info = get_valid_files(
                revision[0],
                context["current_valid_files"],
                context["service_code"],
                context["line_name"],
            )
            if booking_arrangements_info:
                context["booking_arrangements"] = booking_arrangements_info[0][0]
                context["booking_methods"] = booking_arrangements_info[0][1:]

        # Get the flag is_timetable_visualiser_active state
        is_timetable_visualiser_active = flag_is_active(
            "", "is_timetable_visualiser_active"
        )
        context["is_timetable_visualiser_active"] = is_timetable_visualiser_active
        # If flag is enabled, show the timetable visualiser
        if is_timetable_visualiser_active:
            date = self.request.GET.get("date", datetime.now().strftime("%Y-%m-%d"))
            # Regular expression pattern to match dates in yyyy-mm-dd format
            date_pattern = r"^\d{4}-\d{2}-\d{2}$"
            is_valid_date = re.match(date_pattern, date) is not None
            if not is_valid_date:
                date = datetime.now().strftime("%Y-%m-%d")
            target_date = datetime.strptime(date, "%Y-%m-%d").date()
            timetable_inbound_outbound = TimetableVisualiser(
                revision_id, service_code, line, target_date
            ).get_timetable_visualiser()

            # Set the context for the timetable visualiser and the line details
            context["curr_date"] = date
            timetable = {}
            is_timetable_info_available = False
            for direction in ["outbound", "inbound"]:
                direction_details = timetable_inbound_outbound[direction]
                journey = direction_details["description"]
                journey = direction.capitalize() + " - " + journey if journey else ""
                bound_details = self.get_direction_timetable(
                    direction_details["df_timetable"], direction
                )
                if (
                    not is_timetable_info_available
                    and not bound_details["df_timetable"].empty
                ):
                    is_timetable_info_available = True
                timetable[direction] = {
                    "df": bound_details["df_timetable"],
                    "total_page": bound_details["total_page"],
                    "total_row_count": bound_details["total_row_count"],
                    "curr_page": bound_details["curr_page"],
                    "show_all": bound_details["show_all"],
                    "journey_name": journey,
                    "stops": direction_details["stops"],
                    "page_param": direction + "Page",
                    "show_all_param": "showAll" + direction.capitalize(),
                }

            context["timetable"] = timetable
            context["is_timetable_info_available"] = is_timetable_info_available
        return context


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
