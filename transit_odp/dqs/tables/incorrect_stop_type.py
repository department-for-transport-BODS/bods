from .base import DQSWarningDetailsBaseTable
import django_tables2 as tables


class IncorrectStopTypeTable(DQSWarningDetailsBaseTable):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.stop_type = tables.Column(verbose_name="Stop type")
        self.columns.append(self.stop_type)
