from .base import DQSWarningDetailsBaseTable
import django_tables2 as tables


class NoTimingPointMoreThan15MinsCodeTable(DQSWarningDetailsBaseTable):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.columns.remove(self.stop_name)
        self.details.verbose_name = "Timing point link"
        self.columns.append(self.details)
