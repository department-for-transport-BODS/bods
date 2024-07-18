from .base import DQSWarningDetailsBaseTable


class StopNotFoundInNaptanOnlyTable(DQSWarningDetailsBaseTable):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
