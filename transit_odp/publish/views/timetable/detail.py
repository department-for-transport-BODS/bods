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
    get_service_type,
    get_valid_files,
)
from transit_odp.users.views.mixins import OrgUserViewMixin
import urllib.parse
from datetime import datetime


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
        """
        Get the context data for the view.

        This method retrieves various contextual data based on the request parameters
        and the object's attributes.
        """
        line = self.request.GET.get("line")
        noc = self.request.GET.get("noc")
        licence_no = self.request.GET.get("l")
        show_all_outbound_param = self.request.GET.get("showAllOutbound", "false")
        show_all_inbound_param = self.request.GET.get("showAllInbound", "false")
        date = self.request.GET.get("date", datetime.now().strftime("%Y-%m-%d"))

        show_all_outbound = show_all_outbound_param.lower() == "true"
        show_all_inbound = show_all_inbound_param.lower() == "true"
        outbound_curr_page_param = int(self.request.GET.get("outboundPage", "1"))
        inbound_curr_page_param = int(self.request.GET.get("inboundPage", "1"))

        service_code = self.request.GET.get("service_code")

        kwargs = super().get_context_data(**kwargs)

        dataset = self.object
        live_revision = dataset.live_revision
        # datetime.now().strftime("%Y-%M-%d")"2013-01-08"
        kwargs["curr_date"] = date
        kwargs["pk"] = dataset.id
        kwargs["pk1"] = self.kwargs["pk1"]
        kwargs["line_name"] = line
        kwargs["service_code"] = service_code
        kwargs["start_date"] = "2022-03-22"
        kwargs["end_date"] = "2025-03-22"
        outbound_total_page = 3
        inbound_total_page = 3
        kwargs["service_type"] = get_service_type(
            live_revision.id, kwargs["service_code"], kwargs["line_name"]
        )
        kwargs["current_valid_files"] = get_current_files(
            live_revision.id, kwargs["service_code"], kwargs["line_name"]
        )
        kwargs["api_root"] = reverse("api:app:api-root", host=config.hosts.DATA_HOST)

        kwargs["outbound_journey_name"] = "Outbound - Norwich to Watton"
        stop_timings = list(range(1000, 1010, 1))
        kwargs["outbound_journey_stops"] = stop_timings

        journey_bus_stops = [
            {"Oxford Circus Station": stop_timings},
            {"King's Cross St. Pancras Station": stop_timings},
            {"Victoria Station": stop_timings},
            {"Waterloo Station": stop_timings},
            {"Marble Arch": stop_timings},
            {"Trafalgar Square": stop_timings},
            {"Piccadilly Circus": stop_timings},
            {"Euston Station": stop_timings},
            {"Paddington Station": stop_timings},
            {"Liverpool Street Station": stop_timings},
            {"Whitechapel Station": stop_timings},
            {"London Bridge": stop_timings},
            {"Aldgate East Station": stop_timings},
            {"Stratford Station": stop_timings},
            {"Elephant & Castle Station": stop_timings},
            {"Brixton Station": stop_timings},
            {"Clapham Junction Station": stop_timings},
            {"Hammersmith Bus Station": stop_timings},
            {
                "Notting Hill Gate": stop_timings,
            },
            {"Camden Town Station": stop_timings},
        ]

        kwargs["outbound_journey_bus_stops"] = journey_bus_stops
        kwargs["inbound_journey_bus_stops"] = journey_bus_stops

        if not show_all_outbound:
            kwargs["outbound_journey_bus_stops"] = journey_bus_stops[:10]

        if not show_all_inbound:
            kwargs["inbound_journey_bus_stops"] = journey_bus_stops[:10]

        kwargs["inbound_journey_name"] = "Inbound - Watton to Norwich"
        kwargs["inbound_journey_stops"] = stop_timings

        kwargs["show_all_outbound"] = show_all_outbound
        kwargs["show_all_inbound"] = show_all_inbound
        kwargs["outbound_ttl_page"] = outbound_total_page
        kwargs["outbound_curr_page"] = outbound_curr_page_param
        kwargs["inbound_ttl_page"] = inbound_total_page
        kwargs["inbound_curr_page"] = inbound_curr_page_param

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

        return kwargs
