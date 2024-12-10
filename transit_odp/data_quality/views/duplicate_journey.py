from transit_odp.data_quality.constants import DuplicateJourneyObservation
from transit_odp.data_quality.models.warnings import JourneyDuplicateWarning
from transit_odp.data_quality.tables import DuplicateJourneyWarningTimingTable
from transit_odp.data_quality.tables.duplicate_journey import DuplicateJourneyListTable
from transit_odp.data_quality.views.base import JourneyListBaseView, OneTableDetailView


class DuplicateJourneyListView(JourneyListBaseView):
    data = DuplicateJourneyObservation
    model = JourneyDuplicateWarning
    table_class = DuplicateJourneyListTable

    def get_queryset(self):
        return super().get_queryset().add_message().add_line().apply_deduplication()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": "The following duplicate journeys have been observed.",
            }
        )
        return context


class DuplicateJourneyDetailView(OneTableDetailView):
    data = DuplicateJourneyObservation
    model = JourneyDuplicateWarning
    # awkward to have a MultiTableView with only one table,
    # but maintains similarity with other detail views
    tables = [DuplicateJourneyWarningTimingTable]

    def get_context_data(self, **kwargs):
        kwargs.update({"subtitle_end": "is duplicated"})
        context = super().get_context_data(**kwargs)
        return context
