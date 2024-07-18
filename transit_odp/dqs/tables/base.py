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
        # tables.TimeColumn(format="H:i", orderable=False)

        self.journey_start_time = tables.TimeColumn(
            verbose_name="Journey Start Time",
            orderable=False,
            empty_values=(),
            format="H:i",
            attrs={
                "a": {"class": "govuk-link"},
                "th": {"class": "govuk-table__header", "width": "40%"},
            },
        )
        self.direction = tables.Column(
            verbose_name="Direction",
            orderable=False,
            empty_values=(),
            attrs={"is_link": True},
        )
        self.stop_name = tables.Column(verbose_name="Stop Name")
        self.columns = [
            self.journey_start_time,
            self.direction,
            self.stop_name,
        ]
        print(f"curr_page: {curr_page}, {type(curr_page)}")
        paginator = Paginator(qs, paginate_by)
        self.paginator = paginator
        self.page = self.paginator.page(curr_page)

    pagination_bottom = True
