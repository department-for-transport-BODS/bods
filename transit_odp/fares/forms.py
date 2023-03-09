from crispy_forms.layout import HTML, ButtonHolder, Layout
from crispy_forms_govuk.forms import GOVUKModelForm
from crispy_forms_govuk.layout.fields import RadioAccordion, RadioAccordionGroup
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django_hosts.resolvers import reverse

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


class FaresFeedDescriptionForm(GOVUKModelForm):
    form_tag = False
    form_error_title = DEFAULT_ERROR_SUMMARY
    form_title = _("Describe your data set")

    class Meta:
        model = DatasetRevision
        fields = ("description", "short_description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        description = self.fields["description"]
        description.widget = forms.Textarea(attrs={"rows": "3"})
        description.help_text = _(
            """This information will give context to data set users. Please be
            descriptive but do not include
            personally identifiable information. You may wish to include: The
            original file name, start date of data,
            description of the fares, products, OpCo, locations/region,
            routes/service numbers for which the data
            applies, or any other useful high level information. The description
            should reflect the data included at
            a high level. """
        )
        description.label = _("Data set description")
        description.label.id = "id-description"
        description.widget.attrs.update(
            {"placeholder": "", "class": "govuk-!-width-three-quarters"}
        )
        description.error_messages.update(
            {
                "required": _(
                    "Enter a description in the data set description box below "
                )
            }
        )

        short_description = self.fields["short_description"]
        short_description.help_text = _(
            """This info will be displayed on your published data set
                dashboard to identify this data set and will not be visible to data
                set users. The maximum number of characters (with spaces)
                is 30 characters."""
        )
        short_description.label = _("Data set short description")
        short_description.label.id = "id-short-description"
        short_description.widget.attrs.update(
            {"placeholder": "", "class": "govuk-!-width-three-quarters", "size": "30"}
        )
        short_description.error_messages.update(
            {
                "required": _(
                    (
                        "Enter a short description in the data set short "
                        "description box below "
                    )
                )
            }
        )

    def get_layout(self):
        return Layout(
            "description",
            "short_description",
            ButtonHolder(CONTINUE_BUTTON, CANCEL_PUBLISH_BUTTON),
        )


class FaresFeedCommentForm(GOVUKModelForm):
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
        comment.help_text = _(
            "This information will give context to data set users. Please "
            "be descriptive but do not include personally identifiable "
            "information. You may wish to include: The original file name, "
            "start date of data, "
            "description of the fares, products, OpCo, locations/region, "
            "routes/service numbers for "
            "which the data applies, or any other useful high level information. "
            "The description should reflect the data included at a high level."
        )
        comment.label = _("Comment on data set updates")
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


class FaresFeedUploadForm(GOVUKModelForm):
    form_tag = False
    form_error_title = DEFAULT_ERROR_SUMMARY

    is_upload = True

    URL_LINK_ITEM_ID = "url_link-conditional"
    UPLOAD_FILE_ITEM_ID = "upload_file-conditional"

    selected_item = forms.CharField(required=False)

    class Meta:
        model = DatasetRevision
        fields = ("upload_file", "url_link")

    def __init__(self, is_update=False, is_revision_modify=False, *args, **kwargs):
        # Remove form prefix so we can clean the selected radio button input. The
        # radio inputs are hardcoded in the
        # template with the name 'selected_item', see govuk/accordion-group.html
        kwargs.pop("prefix", None)
        super().__init__(*args, **kwargs)
        self.is_update = is_update
        self.is_revision_modify = is_revision_modify

        url_link = self.fields["url_link"]
        url_link.label = _("")
        url_link.help_text = _(
            "Please provide a URL link where your NeTEX files are hosted. "
            "Example address: 'mybuscompany.com/fares.xml'. "
        )
        url_link.error_messages.update(
            {
                "required": _("Please provide a URL link"),
                "invalid": _("Enter a valid URL to your data set"),
                "all": _("Please provide a file or url"),
            }
        )
        url_link.widget.attrs.update(
            {
                "placeholder": "",
                "class": "govuk-!-width-three-quarters",
                "aria-label": "url link",
            }
        )

        upload_file = self.fields["upload_file"]
        upload_file.label = _("")
        upload_file.widget = forms.FileInput()
        # Default widget is 'ClearableFileInput' which renders 'current file' in
        # the HTML
        upload_file.help_text = _(
            (
                "This must be either NeTEX (see description in guidance) or a "
                "zip consisting only of NeTEX files "
            )
        )
        upload_file.error_messages.update(
            {
                "required": _("Please provide a file"),
                "empty": _("Please provide a non-empty file"),
                "invalid": _("The file is not in a correct format"),
            }
        )
        upload_file.widget.attrs.update(
            {
                "placeholder": "",
                "class": "govuk-file-upload hidden-overflow",
                "aria-label": "Choose file",
            }
        )

    def get_layout(self):
        errors = self.errors
        non_field_errors = errors.get("__all__", None)
        # If there are field-related errors, don't show the non-field related ones
        # i.e. if URL is invalid don't show 'you must upload a file or url'
        if non_field_errors is not None and (len(errors.keys()) > 1):
            non_field_errors = None

        submit_button = CONTINUE_BUTTON
        cancel_button = CANCEL_PUBLISH_BUTTON

        legend_title = _("Choose how to provide your data set")

        if self.is_update:
            legend_title = _("Update your published data set")
            cancel_button = CANCEL_UPDATE_BUTTON
            if self.is_revision_modify:
                cancel_button.url = reverse(
                    "fares:revision-update-publish",
                    kwargs={
                        "pk": self.instance.dataset.id,
                        "pk1": self.instance.dataset.organisation_id,
                    },
                    host=config.hosts.PUBLISH_HOST,
                )
            else:
                cancel_button.url = reverse(
                    "fares:feed-detail",
                    kwargs={
                        "pk": self.instance.dataset.id,
                        "pk1": self.instance.dataset.organisation_id,
                    },
                    host=config.hosts.PUBLISH_HOST,
                )
            cancel_button = CANCEL_PUBLISH_BUTTON

        return Layout(
            RadioAccordion(
                RadioAccordionGroup(
                    "Provide a link to your data set",
                    "url_link",
                    css_id=self.URL_LINK_ITEM_ID,
                ),
                RadioAccordionGroup(
                    "Upload data set to Bus Open Data Service",
                    "upload_file",
                    css_id=self.UPLOAD_FILE_ITEM_ID,
                ),
                errors=non_field_errors,
                legend=legend_title,
                use_legend_as_heading=True,
            ),
            HTML(
                '<span id="file-select-success" class="govuk-hint" '
                'style="display: none">'
                "Your file has been selected</span>"
            ),
            ButtonHolder(submit_button, cancel_button),
        )

    def clean(self):
        cleaned_data = super().clean()
        upload_file = cleaned_data.pop("upload_file", None)
        url_link = cleaned_data.pop("url_link", "")

        if self.errors:
            # Don't raise errors if we already have field related errors, e.g. an
            # invalid URL also entails a missing URL
            # error
            return

        selected_item = cleaned_data.pop("selected_item", None)
        if selected_item == self.UPLOAD_FILE_ITEM_ID:
            # ensure a new file has been uploaded
            if not upload_file or ("upload_file" not in self.files):
                self.add_error(
                    "upload_file",
                    ValidationError(
                        self.fields["upload_file"].error_messages["required"],
                        code="required",
                    ),
                )
                return
            url_link = ""
        elif selected_item == self.URL_LINK_ITEM_ID:
            if not url_link or ("url_link" not in self.data):
                self.add_error(
                    "url_link",
                    ValidationError(
                        self.fields["url_link"].error_messages["required"],
                        code="required",
                    ),
                )
                return
            upload_file = None
        else:
            self.add_error(
                "url_link",
                ValidationError(
                    self.fields["url_link"].error_messages["all"],
                    code="all",
                ),
            )
            return

        # Do final validation to make sure only one or the other fields are set
        if not (bool(upload_file) ^ bool(url_link)):
            self.add_error(
                "url_link",
                ValidationError(
                    self.fields["url_link"].error_messages["all"],
                    code="all",
                ),
            )
            return

        cleaned_data["upload_file"] = upload_file
        cleaned_data["url_link"] = url_link

        return cleaned_data


class EditFeedDescriptionForm(GOVUKModelForm):
    form_title = _("Edit description")

    class Meta:
        model = DatasetRevision
        fields = ("description", "short_description")

    def __init__(self, instance=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        description = self.fields["description"]
        description.widget = forms.Textarea(attrs={"rows": "3"})
        description.help_text = _(
            (
                "This info will give context to data set users. Please be descriptive "
                "but do not use personally identifiable information. Information you "
                "may wish to include: The original file name, start date of data, "
                "description of timetables, OpCo, locations/region, routes/service "
                "numbers for which the data applies, or any other useful high-level "
                "information. "
            )
        )

        description.label = _("Data set description")
        description.label.id = "id-description"
        description.widget.attrs.update(
            {"placeholder": "", "class": "govuk-!-width-three-quarters"}
        )
        description.error_messages.update(
            {
                "required": _(
                    "Enter a description in the data set description box below "
                )
            }
        )
        description.initial = instance.description

        short_description = self.fields["short_description"]
        short_description.help_text = _(
            (
                "This information will be displayed on your published data set "
                "dashboard to identify this data set and will not be visible to data "
                "set users. The maximum number of characters (with spaces) is 30 "
                "characters. "
            )
        )
        short_description.label = _("Data set short description")
        short_description.label.id = "id-short-description"
        short_description.widget.attrs.update(
            {"placeholder": "", "class": "govuk-!-width-three-quarters", "size": "30"}
        )
        short_description.error_messages.update(
            {
                "required": _(
                    (
                        "Enter a short description in the data set short description "
                        "box below "
                    )
                )
            }
        )
        short_description.initial = instance.short_description

    def get_layout(self):
        return Layout(
            "description",
            "short_description",
            ButtonHolder(EDIT_DESCRIPTION_SUBMIT, CANCEL_PUBLISH_BUTTON),
        )
