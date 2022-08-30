from django.utils.safestring import mark_safe

from transit_odp.data_quality.constants import MissingStopsObservation
from transit_odp.data_quality.helpers import create_comma_separated_string
from transit_odp.data_quality.models.warnings import ServiceLinkMissingStopWarning
from transit_odp.data_quality.tables.base import TimingPatternListTable
from transit_odp.data_quality.tables.service_link_missing_stop import (
    ServiceLinkMissingStopWarningTimingTable,
    ServiceLinkMissingStopWarningVehicleTable,
)
from transit_odp.data_quality.views.base import (
    TimingPatternsListBaseView,
    TwoTableDetailView,
)


class ServiceLinkMissingStopListView(TimingPatternsListBaseView):
    data = MissingStopsObservation
    model = ServiceLinkMissingStopWarning
    table_class = TimingPatternListTable

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .add_line(self.kwargs["report_id"])
            .add_message()
            .distinct("id")
        )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": (
                    "Following timing pattern(s) have been observed to have missing "
                    "stops."
                ),
            }
        )
        return context


class ServiceLinkMissingStopDetailView(TwoTableDetailView):
    data = MissingStopsObservation
    model = ServiceLinkMissingStopWarning
    tables = [
        ServiceLinkMissingStopWarningTimingTable,
        ServiceLinkMissingStopWarningVehicleTable,
    ]

    # Warning primarily about service link, so we don't show "effected stops" on the map
    # pass empty string instead
    def get_effected_stop_ids(self):
        return ""

    def get_table1_kwargs(self):
        warning = self.warning
        service_name = warning.get_service_pattern().service.name
        missing_stop_names = warning.stops.values_list("name", flat=True)
        missing_stop_names_html = self.convert_stop_names_to_html(missing_stop_names)
        pluralize = "stops" if missing_stop_names.count() > 1 else "stop"
        from_stop_name = warning.service_link.from_stop.name
        to_stop_name = warning.service_link.to_stop.name

        return {
            "warning_message": mark_safe(
                f"We've found a possibility where the route {service_name} might be "
                f"missing {pluralize} {missing_stop_names_html} between "
                f"{from_stop_name} and {to_stop_name}."
            )
        }

    # doesn't easily fit into the usual pattern because the "effected stops" are those
    # that are missing
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        warning = self.warning
        line_name = warning.get_service_pattern().service.name
        from_stop = warning.service_link.from_stop
        to_stop = warning.service_link.to_stop
        stop_ids_for_map = (
            from_stop.id,
            to_stop.id,
        )
        service_link_ids_for_map = (warning.service_link.id,)

        context.update(
            {
                "title": self.data.title,
                "subtitle": (
                    f"Line {line_name} might be missing a stop between "
                    f"{from_stop.name} and {to_stop.name}"
                ),
                # for map
                "stop_ids": create_comma_separated_string(stop_ids_for_map),
                # not ideal -- super() calls mean we change value of service_pattern_id
                # several times
                "service_pattern_id": "",
                "service_link_ids": create_comma_separated_string(
                    service_link_ids_for_map
                ),
            }
        )
        return context

    def convert_stop_names_to_html(self, stop_name_qs):
        comma_separated_string = ",".join(stop_name_qs)
        html = f'<span class="govuk-!-font-weight-bold">{comma_separated_string}</span>'
        return html
