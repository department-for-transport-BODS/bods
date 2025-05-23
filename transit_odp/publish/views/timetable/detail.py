import math
import re
from datetime import datetime
from typing import Dict

import pandas as pd
from django.conf import settings
from django_hosts import reverse
from waffle import flag_is_active

import config.hosts
from transit_odp.browse.timetable_visualiser import TimetableVisualiser
from transit_odp.common.constants import FeatureFlags
from transit_odp.common.enums import FeedErrorSeverity
from transit_odp.common.views import BaseDetailView
from transit_odp.data_quality.models import SchemaViolation
from transit_odp.data_quality.models.report import PostSchemaViolation, PTIObservation
from transit_odp.data_quality.report_summary import Summary
from transit_odp.data_quality.scoring import get_data_quality_rag
from transit_odp.dqs.constants import ReportStatus
from transit_odp.dqs.models import Report
from transit_odp.organisation.constants import DatasetType, FeedStatus
from transit_odp.organisation.models import Dataset
from transit_odp.publish.views.utils import (
    get_current_files,
    get_distinct_dataset_txc_attributes,
    get_service_type,
    get_valid_files,
)
from transit_odp.users.views.mixins import OrgUserViewMixin


class FeedDetailView(OrgUserViewMixin, BaseDetailView):
    template_name = "publish/dataset_detail/index.html"
    model = Dataset

    def get_queryset(self):
        query = (
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
        return query

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        is_new_data_quality_service_active = flag_is_active(
            "", "is_new_data_quality_service_active"
        )

        dataset = self.object
        live_revision = dataset.live_revision
        report = live_revision.report.order_by("-created").first()
        dqs_report = live_revision.dqs_report.order_by("-created").first()

        if dqs_report:
            report_id = dqs_report.id if dqs_report else None
            warning_data = Summary.get_report(report_id, live_revision.id)
            kwargs["warning_data"] = warning_data
            kwargs["new_dqs_report"] = True
            kwargs["is_new_data_quality_service_active"] = True
        else:
            report_id = report.id if report else None
            summary = getattr(report, "summary", None)
            kwargs["dq_score"] = get_data_quality_rag(report) if summary else None
            kwargs["new_dqs_report"] = False
            kwargs["is_new_data_quality_service_active"] = False

        kwargs["report_id"] = report_id
        kwargs["api_root"] = reverse("api:app:api-root", host=config.hosts.DATA_HOST)
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
        kwargs["distinct_attributes"] = get_distinct_dataset_txc_attributes(
            live_revision.id
        )

        kwargs["is_schema_violation"] = (
            SchemaViolation.objects.filter(revision=live_revision.id).count() > 0
        )
        kwargs["is_post_schema_violation"] = (
            PostSchemaViolation.objects.filter(revision=live_revision.id).count() > 0
        )
        kwargs["is_pti_violation"] = (
            PTIObservation.objects.filter(revision=live_revision.id).count() > 0
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
            .select_related("live_revision")
        )

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
        service_code = self.request.GET.get("service")
        kwargs = super().get_context_data(**kwargs)

        dataset = self.object
        live_revision = dataset.live_revision
        kwargs["pk"] = dataset.id
        kwargs["pk1"] = self.kwargs["pk1"]
        kwargs["line_name"] = line
        kwargs["service_code"] = service_code
        kwargs["service_type"] = get_service_type(
            live_revision.id, kwargs["service_code"], kwargs["line_name"]
        )
        kwargs["current_valid_files"] = get_current_files(
            live_revision.id, kwargs["service_code"], kwargs["line_name"]
        )
        kwargs["api_root"] = reverse("api:app:api-root", host=config.hosts.DATA_HOST)

        if (
            kwargs["service_type"] == "Flexible"
            or kwargs["service_type"] == "Flexible/Standard"
        ):
            booking_arrangements_info = get_valid_files(
                live_revision.id,
                kwargs["current_valid_files"],
                kwargs["service_code"],
                kwargs["line_name"],
            )
            if booking_arrangements_info:
                kwargs["booking_arrangements"] = booking_arrangements_info[0][0]
                kwargs["booking_methods"] = booking_arrangements_info[0][1:]

        # Get the flag is_timetable_visualiser_active state
        is_timetable_visualiser_active = flag_is_active(
            "", "is_timetable_visualiser_active"
        )
        kwargs["is_complete_service_pages_active"] = flag_is_active(
            "", FeatureFlags.COMPLETE_SERVICE_PAGES.value
        )
        kwargs["is_timetable_visualiser_active"] = is_timetable_visualiser_active

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
                live_revision.id, service_code, line, target_date
            ).get_timetable_visualiser()
            timetable = {}
            is_timetable_info_available = False
            # Set the context for the timetable visualiser and the line details
            kwargs["curr_date"] = date
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
                    "observations": direction_details.get("observations", {}),
                    "page_param": direction + "Page",
                    "show_all_param": "showAll" + direction.capitalize(),
                }
            kwargs["timetable"] = timetable
            kwargs["is_timetable_info_available"] = is_timetable_info_available

        return kwargs
