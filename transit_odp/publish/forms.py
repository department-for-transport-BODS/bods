from crispy_forms.layout import HTML, ButtonHolder, Layout
from crispy_forms_govuk.forms import GOVUKForm, GOVUKModelForm
from crispy_forms_govuk.layout import (
    ButtonSubmit,
    LinkButton,
    RadioAccordion,
    RadioAccordionGroup,
)
from crispy_forms_govuk.layout.fields import CheckboxSingleField
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django_hosts.resolvers import reverse

import config.hosts
from transit_odp.common.contants import DEFAULT_ERROR_SUMMARY
from transit_odp.organisation.models import DatasetRevision
from transit_odp.publish.constants import (
    DUPLICATE_COMMENT_ERROR_MESSAGE,
    REQUIRED_COMMENT_ERROR_MESSAGE,
)

User = get_user_model()

NEXT_BUTTON = ButtonSubmit("submit", "submit", content=_("Next step"))
PUBLISH_DATA_BUTTON = ButtonSubmit("submit", "submit", content=_("Upload data"))
SUBMIT_BUTTON = ButtonSubmit("submit", "submit", content=_("Submit"))
SAVE_BUTTON = ButtonSubmit("submit", "submit", content=_("Save"))
PUBLISH_UPDATE_BUTTON = ButtonSubmit("submit", "submit", content=_("Publish changes"))
CONTINUE_BUTTON = ButtonSubmit("submit", "submit", content=_("Continue"))
CANCEL_UPDATE_BUTTON = LinkButton("/", content="Cancel")
CANCEL_PUBLISH_BUTTON = ButtonSubmit("cancel", "cancel", content=_("Cancel"))
CANCEL_PUBLISH_BUTTON.field_classes = "govuk-button govuk-button--secondary"

EDIT_DESCRIPTION_SUBMIT = ButtonSubmit(
    "submit", "submit", content=_("Save and continue")
)

DISABLE_SUBMIT_SCRIPT = (
    """document.querySelector('form button[type="submit"]').disabled = !this.checked"""
)


class FeedDescriptionForm(GOVUKModelForm):
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
            """This information will give context to data consumers. Please
        be descriptive, but do not use personally identifiable information."""
        )

        description.label = _("Data set description")
        description.label.id = "id-description"
        description.widget.attrs.update(
            {
                "placeholder": "",
                "class": "govuk-!-width-three-quarters",
                "maxlength": "300",
            }
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
                    "Enter a short description in the data set short description "
                    "box below "
                )
            }
        )

    def get_layout(self):
        return Layout(
            "description",
            "short_description",
            ButtonHolder(CONTINUE_BUTTON, CANCEL_PUBLISH_BUTTON),
        )


class FeedCommentForm(GOVUKModelForm):
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
            """Please add a comment to describe the updates you have
        made to this data set. Users will see this information in the change log."""
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


class FeedUploadForm(GOVUKModelForm):
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
            "Please provide data set URL that contains either TransXChange "
            "(see description in guidance) or zip consisting only of TransXChange "
            "files. "
        )
        url_link.error_messages.update(
            {
                "required": _("Please provide a URL link"),
                "invalid": _("Enter a valid URL to your data set"),
                "all": _("Please provide a file or url"),
            }
        )
        url_link.widget.attrs.update(
            {"placeholder": "", "class": "govuk-!-width-three-quarters"}
        )

        upload_file = self.fields["upload_file"]
        upload_file.label = _("")
        upload_file.widget = forms.FileInput()
        # Default widget is 'ClearableFileInput' which renders 'current file' in
        # the HTML
        upload_file.help_text = _(
            "Please provide data set file that contains either TransXChange "
            "(see description in guidance) or zip consisting only of TransXChange "
            "files "
        )
        upload_file.error_messages.update(
            {
                "required": _("Please provide a file"),
                "empty": _("Please provide a non-empty file"),
                "invalid": _("The file is not in a correct format"),
            }
        )
        upload_file.widget.attrs.update(
            {"placeholder": "", "class": "govuk-file-upload hidden-overflow"}
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
                    "revision-update-publish",
                    kwargs={
                        "pk": self.instance.dataset.id,
                        "pk1": self.instance.dataset.organisation_id,
                    },
                    host=config.hosts.PUBLISH_HOST,
                )
            else:
                cancel_button.url = reverse(
                    "feed-detail",
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


class FeedPreviewForm(forms.ModelForm):
    class Meta:
        model = DatasetRevision
        fields = ("name", "description", "comment", "url_link")  # upload_file
        # fields = []

    # upload_file = forms.CharField()

    def __init__(self, submit=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hide all the fields in this form
        for name, field in self.fields.items():
            field.widget = forms.HiddenInput()


class FeedPublishCancelForm(forms.Form):
    def __init__(self, is_update=False, is_revision_modify=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_update = is_update
        self.is_revision_modify = is_revision_modify


class RevisionPublishForm(GOVUKModelForm):
    consent = forms.BooleanField(
        initial=False,
        required=True,
    )

    def __init__(
        self,
        consent_label="I have reviewed the submission and wish to publish my data",
        is_update=False,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        consent_field = self.fields["consent"]
        consent_field.label = _(consent_label)
        self.is_update = is_update

    class Meta:
        model = DatasetRevision
        fields = ("is_published",)

    def get_layout(self):
        return Layout(
            CheckboxSingleField(
                "consent",
                small_boxes=True,
                onchange=DISABLE_SUBMIT_SCRIPT,
            ),
            ButtonSubmit("submit", "submit", content=_("Publish data"), disabled=True),
        )

    def clean_consent(self):
        consent = self.cleaned_data["consent"]

        if not consent:
            raise forms.ValidationError("Select the box below to publish the data")

        return consent

    def clean(self):
        # There is no frontend route to this but protects against manually posting a
        # form
        if self.instance.is_pti_compliant():
            return super().clean()

        raise forms.ValidationError("Cannot publish PTI non compliant datasets")


class RevisionPublishFormViolations(RevisionPublishForm):
    def get_layout(self):
        modify_name = "update-modify" if self.is_update else "upload-modify"
        recommendation = (
            "Your data needs to be improved, "
            "and we do not recommend publishing non-compliant data."
        )
        reverse_kwargs = {
            "pk": self.instance.dataset.id,
            "pk1": self.instance.dataset.organisation_id,
        }
        update_button = LinkButton(
            reverse(
                modify_name,
                kwargs=reverse_kwargs,
                host=config.hosts.PUBLISH_HOST,
            ),
            "Update data",
        )
        update_button.field_classes = "govuk-button"
        submit_button = ButtonSubmit(
            "submit", "submit", content=_("Publish non-compliant data"), disabled=True
        )
        submit_button.field_classes = "govuk-button govuk-button--secondary"
        return Layout(
            HTML(
                '<h3 class="govuk-heading-m govuk-!-margin-top-6">'
                "Recommended actions"
                "</h3>"
            ),
            ButtonHolder(
                update_button,
                LinkButton(
                    reverse(
                        "revision-delete",
                        kwargs=reverse_kwargs,
                        host=config.hosts.PUBLISH_HOST,
                    ),
                    "Delete data",
                ),
            ),
            HTML(
                f'<p class="govuk-body-m govuk-!-font-weight-bold">{recommendation}</p>'
            ),
            CheckboxSingleField(
                "consent",
                small_boxes=True,
                onchange=DISABLE_SUBMIT_SCRIPT,
            ),
            submit_button,
        )


class SelectDataTypeForm(GOVUKForm):
    dataset_type = forms.ChoiceField(
        label=_("Choose data type"),
        choices=[
            (1, _("Timetables")),
            (2, _("Automatic Vehicle Locations (AVL)")),
            (3, _("Fares")),
        ],
        required=True,
        widget=forms.RadioSelect(attrs={"id": "dataset_type"}),
        error_messages={"required": "Please select a data type"},
    )
    page_heading_field = "dataset_type"

    def get_layout(self):
        return Layout("dataset_type", CONTINUE_BUTTON)


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
            "This info will give context to data set users. Please be descriptive "
            "but do not use personally identifiable information. Information you "
            "may wish to include: The original file name, start date of data, "
            "description of timetables, OpCo, locations/region, routes/service "
            "numbers for which the data applies, or any other useful high-level "
            "information. "
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
            "This information will be displayed on your published data set "
            "dashboard to identify this data set and will not be visible to data "
            "set users. The maximum number of characters (with spaces) is "
            "30 characters. "
        )
        short_description.label = _("Data set short description")
        short_description.label.id = "id-short-description"
        short_description.widget.attrs.update(
            {"placeholder": "", "class": "govuk-!-width-three-quarters", "size": "30"}
        )
        short_description.error_messages.update(
            {
                "required": _(
                    "Enter a short description in the data set short description "
                    "box below "
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
