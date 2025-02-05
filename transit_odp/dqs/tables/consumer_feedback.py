from .base import DQSWarningDetailsBaseTable
import django_tables2 as tables


class ConsumerFeedbackCodeTable(DQSWarningDetailsBaseTable):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.columns = [
            self.journey_start_time,
            self.direction,
            self.stop_name,
            self.message,
            self.feedback,
        ]
