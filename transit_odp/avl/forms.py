from crispy_forms.layout import HTML, ButtonHolder, Layout
from transit_odp.crispy_forms_govuk.forms import GOVUKModelForm
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django_hosts.resolvers import reverse
from django.conf import settings

import config.hosts
from transit_odp.common.constants import DEFAULT_ERROR_SUMMARY
from transit_odp.organisation.models import DatasetRevision
from transit_odp.publish.constants import (
    DUPLICATE_COMMENT_ERROR_MESSAGE,
    REQUIRED_COMMENT_ERROR_MESSAGE,
)
from transit_odp.publish.forms.constants import (
    CANCEL_PUBLISH_BUTTON,
    CANCEL_UPDATE_BUTTON,
    CONTINUE_BUTTON,
    EDIT_DESCRIPTION_SUBMIT,
)

User = get_user_model()


ALLOW_LIST_IP_ADDRESSES = settings.CAVL_IP_ADDRESS_LIST
COMMENT_HELP = _(
    "Please add a comment to describe the data feed. Providers may want to "
    "include the following information:\ntime & date of feed connection, reason "
    "for updating feed, OpCo/Region/Zone of feed, any internal\nreferences or "
    "services included in the feed."
)
DESCRIPTION_HELP = _(
    "The info will give context to data feed users. Please be descriptive "
    "but do not use personally identifiable information. Information you may "
    "wish to include: time & date of feed connection, reason for updating feed, "
    "OpCo/region/zone of feed, services included in feed."
)
DESCRIPTION_HELP_SHORT = _(
    "This info will be displayed on your published data feed dashboard to "
    "identify this feed and will not be visible to data feed users. The "
    "maximum number of characters (with spaces) is 30 characters."
)
DESCRIPTION_ERROR = _("Enter a description in the data feed description box below ")
DESCRIPTION_ERROR_SHORT = _(
    "Enter a short description in the data feed short description box below "
)


class AvlFeedDescriptionForm(GOVUKModelForm):
    form_tag = False
    form_error_title = DEFAULT_ERROR_SUMMARY
    form_title = _("Describe your data feed")

    class Meta:
        model = DatasetRevision
        fields = ("description", "short_description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        description = self.fields["description"]
        description.widget = forms.Textarea(attrs={"rows": "3"})
        description.help_text = DESCRIPTION_HELP
        description.label = _("Data feed description")
        description.label.id = "id-description"
        description.widget.attrs.update(
            {"placeholder": "", "class": "govuk-!-width-three-quarters"}
        )
        description.error_messages.update({"required": DESCRIPTION_ERROR})

        short_description = self.fields["short_description"]
        short_description.help_text = DESCRIPTION_HELP_SHORT
        short_description.label = _("Data feed short description")
        short_description.label.id = "id-short-description"
        short_description.widget.attrs.update(
            {"placeholder": "", "class": "govuk-!-width-three-quarters", "size": "30"}
        )
        short_description.error_messages.update({"required": DESCRIPTION_ERROR_SHORT})

    def get_layout(self):
        return Layout(
            "description",
            "short_description",
            ButtonHolder(CONTINUE_BUTTON, CANCEL_PUBLISH_BUTTON),
        )


class AVLFeedCommentForm(GOVUKModelForm):
    form_tag = False
    form_error_title = DEFAULT_ERROR_SUMMARY
    form_title = "Provide a comment on what has been updated"

    class Meta:
        model = DatasetRevision
        fields = ("comment",)

    def __init__(self, is_update=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_update = is_update

        comment = self.fields["comment"]
        comment.required = True
        comment.widget = forms.Textarea(attrs={"rows": "3"})
        comment.help_text = COMMENT_HELP
        comment.label = _("Comment on data feed updates")
        comment.widget.attrs.update(
            {"placeholder": "", "class": "govuk-!-width-three-quarters"}
        )
        comment.error_messages.update(
            {
                "required": _(REQUIRED_COMMENT_ERROR_MESSAGE),
                "duplicate": _(DUPLICATE_COMMENT_ERROR_MESSAGE),
            }
        )

    def get_layout(self):
        return Layout("comment", ButtonHolder(CONTINUE_BUTTON, CANCEL_PUBLISH_BUTTON))

    def clean(self):
        cleaned_data = super().clean()
        comment = cleaned_data.get("comment", None)

        if comment and comment == self.instance.tracker.previous("comment"):
            self.add_error(
                "comment",
                ValidationError(
                    self.fields["comment"].error_messages["duplicate"], code="required"
                ),
            )
        return cleaned_data


class AvlFeedUploadForm(GOVUKModelForm):
    form_title = _("Provide your data using the link below")

    class Meta:
        model = DatasetRevision
        fields = (
            "url_link",
            "username",
            "password",
            "requestor_ref",
        )

    def __init__(self, is_update=False, is_revision_modify=False, *args, **kwargs):
        kwargs.pop("prefix", None)
        super().__init__(*args, **kwargs)
        self.is_update = is_update
        self.is_revision_modify = is_revision_modify

        if is_update:
            self.form_title = _("Update your published data feed")

        url_link = self.fields["url_link"]
        url_link.label = _("Provide a URL link")
        self.fields["url_link"].required = True
        url = (
            reverse("guidance:support-bus_operators", host=config.hosts.PUBLISH_HOST)
            + "?section=buslocation"
        )
        url_link.help_text = (
            f'We have <a class="govuk-link" target="_blank" '
            f"href={url}>guidance</a> on the SIRI-VM standard and how to provide data"
        )

        url_link.error_messages.update(
            {
                "required": _("Please provide a URL link"),
                "invalid": _("Enter a valid URL to your data feed"),
            }
        )
        url_link.widget.attrs.update(
            {"placeholder": "", "class": "govuk-!-width-three-quarters"}
        )

        username = self.fields["username"]
        username.label = _("Username")
        self.fields["username"].required = True
        username.error_messages.update(
            {
                "required": _("Please provide a username"),
                "invalid": _("Enter a valid username to your data feed"),
            }
        )
        username.widget.attrs.update(
            {"placeholder": "", "class": "govuk-!-width-three-quarters"}
        )

        password = self.fields["password"]
        password.label = _("Password")
        self.fields["password"].required = True
        password.error_messages.update(
            {
                "required": _("Please provide a password"),
                "invalid": _("Enter a valid password to your data feed"),
            }
        )
        password.widget.attrs.update(
            {"placeholder": "", "class": "govuk-!-width-three-quarters"}
        )

        requestor_ref = self.fields["requestor_ref"]
        requestor_ref.label = _("RequestorRef (Optional)")
        requestor_ref.error_messages.update(
            {"invalid": _("Enter a valid RequestorRef to your data feed")}
        )
        requestor_ref.widget.attrs.update(
            {"placeholder": "", "class": "govuk-!-width-three-quarters"}
        )

    def get_layout(self):
        submit_button = CONTINUE_BUTTON
        cancel_button = CANCEL_PUBLISH_BUTTON

        if self.is_update:
            cancel_button = CANCEL_UPDATE_BUTTON
            if self.is_revision_modify:
                cancel_button.url = reverse(
                    "avl:revision-update-publish",
                    kwargs={
                        "pk": self.instance.dataset.id,
                        "pk1": self.instance.dataset.organisation_id,
                    },
                    host=config.hosts.PUBLISH_HOST,
                )
            else:
                cancel_button.url = reverse(
                    "avl:feed-detail",
                    kwargs={
                        "pk": self.instance.dataset.id,
                        "pk1": self.instance.dataset.organisation_id,
                    },
                    host=config.hosts.PUBLISH_HOST,
                )
            cancel_button = CANCEL_PUBLISH_BUTTON

        ip_text = (
            HTML(
                '<span class="govuk-hint">If you require your SIRI-VM feed to be '
                "restricted to particular IP addresses, "
                "please allow-list these IP addresses: "
                f"{ALLOW_LIST_IP_ADDRESSES}"
                "</span>"
            )
            if ALLOW_LIST_IP_ADDRESSES
            else ""
        )

        return Layout(
            "url_link",
            "username",
            "password",
            "requestor_ref",
            ip_text,
            ButtonHolder(submit_button, cancel_button),
        )


class EditFeedDescriptionForm(GOVUKModelForm):
    form_title = _("Edit description")

    class Meta:
        model = DatasetRevision
        fields = ("description", "short_description")

    def __init__(self, instance=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        description = self.fields["description"]
        description.widget = forms.Textarea(attrs={"rows": "3"})
        description.help_text = DESCRIPTION_HELP
        description.label = _("Data feed description")
        description.label.id = "id-description"
        description.widget.attrs.update(
            {"placeholder": "", "class": "govuk-!-width-three-quarters"}
        )
        description.error_messages.update({"required": DESCRIPTION_ERROR})
        description.initial = instance.description

        short_description = self.fields["short_description"]
        short_description.help_text = DESCRIPTION_HELP_SHORT
        short_description.label = _("Data feed short description")
        short_description.label.id = "id-short-description"
        short_description.widget.attrs.update(
            {"placeholder": "", "class": "govuk-!-width-three-quarters", "size": "30"}
        )
        short_description.error_messages.update({"required": DESCRIPTION_ERROR_SHORT})
        short_description.initial = instance.short_description

    def get_layout(self):
        return Layout(
            "description",
            "short_description",
            ButtonHolder(EDIT_DESCRIPTION_SUBMIT, CANCEL_PUBLISH_BUTTON),
        )
