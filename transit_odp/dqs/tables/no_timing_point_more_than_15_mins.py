from .base import DQSWarningDetailsBaseTable
import django_tables2 as tables


class NoTimingPointMoreThan15MinsCodeTable(DQSWarningDetailsBaseTable):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.stop_name.verbose_name = "Timing point"
