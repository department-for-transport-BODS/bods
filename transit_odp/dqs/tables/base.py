from transit_odp.common.tables import GovUkTable
import django_tables2 as tables
from django.core.paginator import Paginator


class DQSWarningDetailsBaseTable(GovUkTable):

    journey_start_time = tables.Column(
        verbose_name="Journey Start Time",
        orderable=False,
        empty_values=(),
        attrs={
            "a": {"class": "govuk-link"},
            "th": {"class": "govuk-table__header", "width": "40%"},
        },
    )
    direction = tables.Column(
        verbose_name="Direction",
        orderable=False,
        empty_values=(),
        attrs={"is_link": True},
    )
    stop_name = tables.Column(verbose_name="Stop Name")
    stop_type = tables.Column(verbose_name="Stop Type", visible=False)

    class Meta:

        attrs = {
            "tbody": {"is_details_link": True},
            "th": {"class": "govuk-table__header"},
        }
        sequence = ("journey_start_time", "direction", "stop_name")
        template_name = "data_quality/snippets/dq_custom_table.html"
        pagination = True

    def __init__(self, *args, **kwargs):
        self.template_name = "data_quality/snippets/dq_custom_table.html"
        print(f"Calling DQSWarningDetailsBaseTable: {self} ")
        print(f"Calling DQSWarningDetailsBaseTable: Rows {args} ")
        qs = args[0]
        curr_page = args[1]
        paginate_by = 10
        print(f"Calling DQSWarningDetailsBaseTable: QuerySet : {qs} ")
        self.show_header = True
        self.show_footer = False
        self._prefix = self._page_field = ""
        self.rows = qs

        journey_start_time = tables.Column(
            verbose_name="Journey Start Time",
            orderable=False,
            empty_values=(),
            attrs={
                "a": {"class": "govuk-link"},
                "th": {"class": "govuk-table__header", "width": "40%"},
            },
        )
        direction = tables.Column(
            verbose_name="Direction",
            orderable=False,
            empty_values=(),
            attrs={"is_link": True},
        )
        stop_name = tables.Column(verbose_name="Stop Name")
        stop_type = tables.Column(verbose_name="Stop Type", visible=False)
        self.columns = [journey_start_time, direction, stop_name, stop_type]
        paginator = Paginator(qs, paginate_by)
        self.paginator = paginator
        self.page = self.paginator.page(curr_page)

        # page = self.request.GET.get("page", 1)

        print(f"Calling DQSWarningDetailsBaseTable: {self} ")

    pagination_bottom = True
