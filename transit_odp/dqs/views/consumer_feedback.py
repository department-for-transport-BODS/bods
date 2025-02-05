from transit_odp.dqs.constants import (
    Checks,
    ConsumerFeedbackObservation,
)
from transit_odp.dqs.tables.consumer_feedback import (
    ConsumerFeedbackCodeTable,
)
from transit_odp.dqs.views.base import FeedbackListBaseView, FeedbackDetailBaseView


class ConsumerFeedbackListView(FeedbackListBaseView):
    data = ConsumerFeedbackObservation

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_dqs_new_report = None

    check = None
    dqs_details = "There is at least one consumer feedback received"

    def get_queryset(self):

        return super().get_queryset()

    def get_table_kwargs(self):
        return {}


class ConsumerFeedbackDetailView(FeedbackDetailBaseView):
    data = ConsumerFeedbackObservation
    paginate_by = 10

    def get_context_data(self, **kwargs):

        self._table_name = ConsumerFeedbackCodeTable
        self.check = Checks.ServicedOrganisationOutOfDate
        line = self.request.GET.get("line")

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "subtitle": f"Service {line} has at least one feedback message to address.",
                "subtitle_description": "How many feedbacks have been raised by consumers?",
                "total_journey_description": "Consumer feedback observations",
                "list_text": "consumer feedback",
            }
        )

        return context
