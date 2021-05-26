from transit_odp.data_quality.constants import FastLinkObservation
from transit_odp.data_quality.models.warnings import FastLinkWarning
from transit_odp.data_quality.tables import (
    FastLinkWarningTimingTable,
    FastLinkWarningVehicleTable,
)
from transit_odp.data_quality.views.base import (
    TimingPatternsListBaseView,
    TwoTableDetailView,
)


class FastLinkListView(TimingPatternsListBaseView):
    data = FastLinkObservation
    model = FastLinkWarning

    def get_queryset(self):
        qs = super().get_queryset().add_message().add_line()
        # In theory, for FastLink there's only ever 1 service link,
        # so can implicitly traverse service_links, getting the from_stop and
        # to_stop of the first link But possibly safer to use subquery to get
        # service_link.first(), for example
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": (
                    "Following timing pattern(s) have been observed to have fast "
                    "timing links."
                ),
            }
        )
        return context


class FastLinkDetailView(TwoTableDetailView):
    data = FastLinkObservation
    model = FastLinkWarning
    tables = [FastLinkWarningTimingTable, FastLinkWarningVehicleTable]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        title = self.data.title
        line_name = self.warning.get_timing_pattern().service_pattern.service.name

        context["title"] = title
        context["subtitle"] = f"Line {line_name} has {title.lower()}"
        return context
