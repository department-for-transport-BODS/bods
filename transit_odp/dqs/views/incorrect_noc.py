from transit_odp.dqs.constants import (
    Checks,
    IncorrectNocObservation as DQSIncorrectNocObservation,
)
from transit_odp.dqs.views.base import DQSWarningListBaseView
from waffle import flag_is_active


class IncorrectNOCListView(DQSWarningListBaseView):
    data = DQSIncorrectNocObservation

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._is_dqs_new_report = None

    @property
    def is_new_data_quality_service_active(self):
        return flag_is_active("", "is_new_data_quality_service_active")

    check = Checks.IncorrectNoc

    def get_queryset(self):

        self.col_name = "noc"
        self.is_details_link = False
        return DQSWarningListBaseView.get_queryset(self)

    def get_table_kwargs(self):

        kwargs = {}
        if not self.is_dqs_new_report:
            kwargs = super().get_table_kwargs()
            kwargs.update({"message_col_verbose_name": "Summary"})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "resolve": self.data.resolve,
                "preamble": self.data.preamble,
                "is_new_data_quality_service_active": self.is_new_data_quality_service_active,
            }
        )
        return context
