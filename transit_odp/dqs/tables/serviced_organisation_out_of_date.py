from .base import DQSWarningDetailsBaseTable
import django_tables2 as tables


class ServicedOrganisationOutOfDateCodeTable(DQSWarningDetailsBaseTable):
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.columns = [
            self.serviced_organisation,
            self.serviced_organisation_code,
            self.last_working_day,
        ]
