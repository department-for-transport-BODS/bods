from datetime import timedelta

import django_tables2 as tables
from django.conf import settings
from django.template.loader import get_template, render_to_string
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django_hosts.resolvers import reverse

from config.hosts import PUBLISH_HOST
from transit_odp.common.tables import GovUkTable
from transit_odp.data_quality.scoring import get_data_quality_rag
from transit_odp.pipelines.models import DataQualityTask
from transit_odp.publish.tables import DatasetRevisionTable


def get_table_page(page: str) -> str:
    return f"?page={page}&" if page and page > "1" else "?page=&"


class TimetableChangelogTable(DatasetRevisionTable):
    class Meta(DatasetRevisionTable.Meta):
        pass

    data_quality = tables.Column(
        verbose_name="Data quality",
        empty_values=(),
        orderable=False,
    )

    def render_data_quality(self, *args, **kwargs):
        snippet = "snippets/data_quality_row.html"
        revision = kwargs.get("record")
        report = revision.report.order_by("-id").first()

        if report is None:
            # there are no reports associated with this revision, why?
            task = revision.data_quality_tasks.order_by("-id").first()
            if task is None or task.status == DataQualityTask.FAILURE:
                # task didnt run or failed
                return format_html("Not available")

            if now() - task.created < timedelta(minutes=settings.DQS_WAIT_TIMEOUT):
                # task is still young, probably hasnt finished yet
                return format_html("Generating...")
            # task is probably stuck in pending state
            return format_html("Not available")

        rag = get_data_quality_rag(report)
        if rag:
            template = get_template(snippet)
            return template.render({"rag": rag})

        return format_html("")


class LineColumn(tables.Column):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.verbose_name = "Line"
        self.attrs["annotation"] = mark_safe(
            render_to_string("publish/snippets/help_modals/line_service_number.html")
        )


class RequiresAttentionTable(GovUkTable):
    class Meta(GovUkTable.Meta):
        pass

    licence_number = tables.Column(
        verbose_name="Licence number", accessor="licence__number"
    )
    service_code = tables.Column(
        verbose_name="Service code", accessor="registration_number"
    )
    line = LineColumn(accessor="service_number")


class SeasonalServiceTable(GovUkTable):
    class Meta(GovUkTable.Meta):
        pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.empty_text = format_html(
            """
                <div class="seasonal_service_empty_body_table">
                <p>No seasonal services added.</p>
                <br/>
                <p>Click 'Add new date range' to add a service.</p>
                </div>
            """
        )

    licence_number = tables.Column(
        verbose_name="Licence number", accessor="licence__number"
    )
    service_code = tables.Column(
        verbose_name="Service code", accessor="registration_number"
    )
    service_begins = tables.DateTimeColumn(
        verbose_name="Service begins", accessor="start", format="d/m/Y"
    )
    service_ends = tables.DateTimeColumn(
        verbose_name="Service ends", accessor="end", format="d/m/Y"
    )
    actions = tables.Column(empty_values=())

    def render_actions(self, record):
        return format_html(
            '<a class="govuk-link" href={href_edit}?page={page}&>'
            "Edit dates"
            "</a>"
            '<button type="submit" name="id" value="{value}" '
            'class="button-table-link govuk-!-margin-left-1">'
            "Delete"
            "</button>",
            href_edit=reverse(
                "edit-seasonal-service-date",
                kwargs={
                    "pk1": record.licence.organisation.id,
                    "pk": record.id,
                },
                host=PUBLISH_HOST,
            ),
            page=self.page.number,
            value=record.id,
        )
