from transit_odp.data_quality.constants import SlowLinkObservation
from transit_odp.data_quality.models.warnings import SlowLinkWarning
from transit_odp.data_quality.tables import (
    SlowLinkWarningTimingTable,
    SlowLinkWarningVehicleTable,
)
from transit_odp.data_quality.views.base import (
    TimingPatternsListBaseView,
    TwoTableDetailView,
)


class SlowLinkListView(TimingPatternsListBaseView):
    data = SlowLinkObservation
    model = SlowLinkWarning

    def get_queryset(self):
        qs = super().get_queryset().add_line().add_message()
        # In theory, for SlowLink there's only ever 1 service link,
        # so can implicitly traverse service_links, getting the from_stop and to_stop
        # of the first link But possibly safer to use subquery to get
        # service_link.first(), for example
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": (
                    "Following timing pattern(s) have been observed to have slow "
                    "links."
                ),
            }
        )
        return context


class SlowLinkDetailView(TwoTableDetailView):
    data = SlowLinkObservation
    model = SlowLinkWarning
    tables = [SlowLinkWarningTimingTable, SlowLinkWarningVehicleTable]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = self.data.title
        line_name = self.warning.get_timing_pattern().service_pattern.service.name

        context["title"] = title
        context["subtitle"] = f"Line {line_name} has {title.lower()}"
        return context
