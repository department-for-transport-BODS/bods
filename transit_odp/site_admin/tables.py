import django_tables2 as tables
from django.contrib.auth import get_user_model
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django_hosts.resolvers import reverse

import config.hosts
from transit_odp.common.tables import GovUkTable
from transit_odp.organisation.models import DatasetSubscription, Organisation

User = get_user_model()

RESEND_CLASS = "resend-checkbox"
CLICKER_SCRIPT = (
    f"[...document"
    f'.getElementsByClassName("{RESEND_CLASS}")'
    f"].forEach("
    f"function(elem){{elem.checked = this.checked}}.bind(this)"
    f")"
)


class GovUKCheckBoxColumn(tables.CheckBoxColumn):
    in_error = False

    @property
    def header(self):
        label_css_classes = "govuk-checkboxes__label"
        if self.in_error:
            label_css_classes += " invite-error"
        return mark_safe(
            '<div class="govuk-checkboxes__item">'
            f"{super().header}"
            f'<label class="govuk-label {label_css_classes}" '
            'for="select-all">'
            '<span class="govuk-visually-hidden">'
            "Resend all organisation invites"
            "</span>"
            "</label>"
            "</div>",
        )


class OrganisationTable(GovUkTable):
    name = tables.Column(
        verbose_name="Name", attrs={"td": {"class": "organisation_name_cell"}}
    )
    status = tables.Column(verbose_name="Status")
    invite_sent = tables.Column(
        verbose_name="Date invited", order_by=("registration_complete", "invite_sent")
    )
    last_active = tables.Column(verbose_name="Last active")
    resend_invites = GovUKCheckBoxColumn(
        empty_values=(),
        attrs={
            "th__input": {
                "form": "ignore",
                "onChange": CLICKER_SCRIPT,
                "class": "govuk-checkboxes__input",
                "id": "select-all",
            },
            "td": {"class": "govuk-checkboxes--small"},
            "th": {"class": "govuk-table__header govuk-checkboxes--small"},
        },
    )

    class Meta(GovUkTable.Meta):
        model = Organisation
        exclude = (
            "id",
            "created",
            "modified",
            "short_name",
            "key_contact",
            "is_active",
            "licence_required",
        )
        sequence = (
            "resend_invites",
            "name",
            "status",
            "invite_sent",
            "last_active",
        )

    def __init__(self, *args, in_error=False, checked_ids=None, **kwargs):
        self._checked_ids = checked_ids or []
        self._in_error = in_error
        self.base_columns["resend_invites"].in_error = in_error
        super().__init__(*args, **kwargs)

    def render_resend_invites(self, record=None):
        if record is not None:
            # We need the label so we can get the clever govuk-frontend checkbox css
            label_css_classes = "govuk-checkboxes__label"
            if self._in_error:
                label_css_classes += " invite-error"

            return format_html(
                '<div class="govuk-checkboxes__item">'
                '<input type="checkbox" '
                'id="resend-invite-org-{name}"'
                'class="{css_class} govuk-checkboxes__input" '
                'name="invites" '
                'value="{name}" '
                "{checked}>"
                "</input>"
                '<label class="govuk-label {label_css_classes}" '
                'for="resend-invite-org-{name}">'
                '<span class="govuk-visually-hidden">'
                "Resend invite for {org_name}"
                "</span>"
                "</label>"
                "</div>",
                css_class=RESEND_CLASS,
                label_css_classes=label_css_classes,
                checked="checked" if record.id in self._checked_ids else "",
                name=record.id,
                org_name=record.name,
            )
        return ""

    def render_invite_sent(self, record=None):
        if not record.registration_complete:
            return f"Invite sent - {record.invite_sent: %d/%m/%Y}"
        return ""

    def render_last_active(self, record=None):
        if record is not None:
            return f"{record.last_active: %d %B %Y %-I:%M%p}"

    def render_name(self, **kwargs):
        value = kwargs["value"]
        record = kwargs["record"]
        link = reverse(
            "users:organisation-detail",
            kwargs={"pk": record.id},
            host=config.hosts.ADMIN_HOST,
        )
        return format_html(
            """
            <a class='govuk-link' href='{link}'>{value}</a>
            """,
            link=link,
            value=value,
        )

    def render_actions(self, **kwargs):
        record = kwargs["record"]
        assert isinstance(record, Organisation)

        items = []

        if record.registration_complete is False:
            url = reverse(
                "users:re-invite",
                kwargs={"pk": record.id},  # organisation_id
                host=config.hosts.ADMIN_HOST,
            )

            items.append(
                format_html(
                    "<a class='govuk-link' href='{link}'>{text}</a>",
                    link=url,
                    text=_("Re-send invitation"),
                )
            )

        if items:
            items_html = format_html_join("\n", "<li>{}</li>", (items,))

            return format_html(
                """
                <ul class="organisation-table__actions">
                    {items}
                </ul>
                """,
                items=items_html,
            )
        else:
            return ""


class FeedNotificationTable(GovUkTable):
    name = tables.Column(verbose_name="Data set")

    class Meta(GovUkTable.Meta):
        model = DatasetSubscription


class ConsumerTable(GovUkTable):
    email = tables.Column(verbose_name="Email")
    is_active = tables.Column(verbose_name="Status")
    last_login = tables.Column(verbose_name="Last active")

    def render_is_active(self, value=None, **kwargs):
        if value:
            return "Active"
        return "Inactive"

    def render_last_login(self, value=None):
        if value is not None:
            return f"{value: %d %B %Y %-I:%M%p}"
        return ""

    def render_email(self, record=None, value=None):
        link = reverse(
            "users:consumer-detail",
            kwargs={"pk": record.id},
            host=config.hosts.ADMIN_HOST,
        )
        anchor = "<a class='govuk-link' href='{link}'>{text}</a>"
        return format_html(anchor, link=link, text=value)

    class Meta(GovUkTable.Meta):
        model = User
        fields = ("email",)


class AgentsTable(GovUkTable):
    class Meta(GovUkTable.Meta):
        model = User
        fields = ("agent_organisation", "email")

    agent_organisation = tables.Column(
        orderable=True, verbose_name="Agent organisation"
    )
    email = tables.Column(orderable=True, verbose_name="Email")
    details = tables.Column(
        orderable=False,
        linkify=lambda record: reverse(
            "users:agent-detail", kwargs={"pk": record.id}, host=config.hosts.ADMIN_HOST
        ),
    )


class AgentOrganisationsTable(GovUkTable):
    class Meta(GovUkTable.Meta):
        model = Organisation
        fields = ("name",)

    name = tables.Column(
        orderable=False,
        verbose_name="Organisation",
        linkify=lambda record: reverse(
            "users:organisation-detail",
            kwargs={"pk": record.id},
            host=config.hosts.ADMIN_HOST,
        ),
    )
    key_contact = tables.Column(
        orderable=False, verbose_name="Key contact", accessor="key_contact__email"
    )
