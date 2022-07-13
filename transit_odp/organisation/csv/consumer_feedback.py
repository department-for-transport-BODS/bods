from transit_odp.common.csv import CSVBuilder, CSVColumn
from transit_odp.organisation.models import ConsumerFeedback


class ConsumerFeedbackBaseCSV(CSVBuilder):
    @property
    def columns(self):
        return [
            CSVColumn(header="Date", accessor=lambda n: f"{n.date:%d.%m.%y}"),
            CSVColumn(header="Feedback type", accessor="feedback_type"),
            CSVColumn(header="Dataset ID", accessor="dataset_id"),
            CSVColumn(header="DataType", accessor="dataset_type"),
            CSVColumn(header="Description", accessor="feedback"),
            CSVColumn(header="Raised by: Name", accessor="username"),
            CSVColumn(header="Raised by: Email", accessor="email"),
            CSVColumn(
                header="Total number of issues raised on this dataset/feed",
                accessor=lambda n: "-" if n.count is None else str(n.count),
            ),
        ]

    def get_queryset(self):
        return (
            ConsumerFeedback.objects.add_date()
            .add_total_issues_per_dataset()
            .add_consumer_details()
            .add_feedback_type()
            .add_dataset_type()
            .order_by("-date")
        )


class ConsumerFeedbackCSV(ConsumerFeedbackBaseCSV):
    def __init__(self, organisation_id: int):
        self._organisation_id = organisation_id

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organisation_id=self._organisation_id)


class ConsumerFeedbackAdminCSV(ConsumerFeedbackBaseCSV):
    @property
    def columns(self):
        columns = super().columns
        columns.insert(
            1, CSVColumn(header="Organisation", accessor="organisation_name")
        )
        return columns

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.add_organisation_name()
