from .base import DQSWarningDetailsBaseTable


class MissingJourneyCodeTable(DQSWarningDetailsBaseTable):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.stop_name.verbose_name = "First stop"
