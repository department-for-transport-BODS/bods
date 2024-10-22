from transit_odp.common.tables import GovUkTable
import django_tables2 as tables
from django.core.paginator import Paginator


class DQSWarningDetailsBaseTable(GovUkTable):
    def __init__(self, *args, **kwargs):

        self.template_name = "dqs/snippets/dqs_warning_detail.html"
        qs = args[0]
        curr_page = args[1]
        paginate_by = 10

        self.show_header = True
        self.show_footer = False
        self._prefix = self._page_field = None

        self.journey_start_time = tables.TimeColumn(
            verbose_name="Journey start time",
            orderable=False,
            empty_values=(),
            format="H:i",
            attrs={
                "a": {"class": "govuk-link"},
                "th": {"class": "govuk-table__header", "width": "40%"},
                "column_key": "journey_start_time",
            },
        )
        self.direction = tables.Column(
            verbose_name="Direction",
            orderable=False,
            empty_values=(),
            attrs={"column_key": "direction"},
        )
        self.stop_name = tables.Column(
            verbose_name="Stop name", attrs={"column_key": "stop_name"}
        )
        self.journey_code = tables.Column(
            verbose_name="Journey code", attrs={"column_key": "journey_code"}
        )
        self.details = tables.Column(
            verbose_name="Details", attrs={"column_key": "details"}
        )
        self.stop_type = tables.Column(
            verbose_name="Stop type", attrs={"column_key": "stop_type"}
        )
        self.serviced_organisation = tables.Column(
            verbose_name="Serviced organisation",
            attrs={"column_key": "serviced_organisation"},
        )
        self.serviced_organisation_code = tables.Column(
            verbose_name="Serviced organisation code",
            attrs={"column_key": "serviced_organisation_code"},
        )
        self.last_working_day = tables.Column(
            verbose_name="Last working day",
            attrs={"column_key": "last_working_day"},
        )
        self.columns = [
            self.journey_start_time,
            self.direction,
            self.stop_name,
        ]
        paginator = Paginator(qs, paginate_by)
        self.paginator = paginator
        self.page = self.paginator.page(curr_page)

    pagination_bottom = True
