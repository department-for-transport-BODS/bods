from crispy_forms.layout import HTML, ButtonHolder, Div, Layout
from crispy_forms_govuk.forms import GOVUKForm, GOVUKModelForm
from crispy_forms_govuk.layout import (
    ButtonSubmit,
    LinkButton,
    RadioAccordion,
    RadioAccordionGroup,
)
from crispy_forms_govuk.layout.fields import CheckboxSingleField, Field
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.forms import NumberInput
from django.template.loader import render_to_string
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_hosts.resolvers import reverse

import config.hosts
from transit_odp.common.constants import DEFAULT_ERROR_SUMMARY
from transit_odp.organisation.models import DatasetRevision, Licence, SeasonalService
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
SEPARATOR = HTML(
    '<hr class="govuk-section-break '
    "           govuk-section-break--xs "
    '           govuk-section-break--visible"'
    ">"
)


def cancel_seasonal_service(org_id):
    return LinkButton(
        reverse(
            "seasonal-service", kwargs={"pk1": org_id}, host=config.hosts.PUBLISH_HOST
        ),
        content="Cancel",
    )


EDIT_DESCRIPTION_SUBMIT = ButtonSubmit(
    "submit", "submit", content=_("Save and continue")
)

DISABLE_SUBMIT_SCRIPT = (
    """document.querySelector('form button[type="submit"]').disabled = !this.checked"""
)


class FieldNoErrors(Field):
    """
    Override Field class but supress the group error so each
    date does not have an individual error bar
    """

    def render(self, form, form_style, context, **kwargs):
        context["suppress_form_group_error"] = True
        return super().render(form, form_style, context, **kwargs)


class DateDiv(Div):
    """
    Override Div class so error bar is added to container if
    errors are detected in its fields
    """

    def render(self, form, form_style, context, **kwargs):
        show_error = False
        for field in self.fields:
            bound_field = form[field.fields[0]]
            if bound_field.errors:
                show_error = True
                break

        self.css_class = (
            self.css_class + " govuk-form-group--error"
            if show_error
            else self.css_class
        )

        return super().render(form, form_style, context, **kwargs)


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
    form_title = _("Choose data type")
    dataset_type = forms.ChoiceField(
        label="",
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
    description = _("Please choose the type of data you would like to publish.")

    def get_layout(self):
        return Layout(
            HTML(
                f'<p class="govuk-body-m '
                f'govuk-!-margin-bottom-7">{self.description}</p>'
            ),
            "dataset_type",
            CONTINUE_BUTTON,
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


class SeasonalServiceLicenceNumberForm(GOVUKModelForm):
    form_tag = False
    form_error_title = DEFAULT_ERROR_SUMMARY

    class Meta:
        model = SeasonalService
        fields = ("licence",)

    def __init__(self, *args, **kwargs):
        self.org_id = kwargs.pop("org_id", None)
        super().__init__(*args, **kwargs)
        self.fields.update(
            {
                "licence": forms.ModelChoiceField(
                    queryset=Licence.objects.filter(organisation_id=self.org_id),
                    required=True,
                    label="PSV licence number",
                    empty_label=_("Select PSV licence number"),
                )
            }
        )
        number_field = self.fields["licence"]
        number_field.label_from_instance = lambda obj: obj.number
        number_field.widget.attrs.update({"class": "govuk-!-width-full"})

    def get_layout(self):
        return Layout(
            Div("licence", css_class="licence"),
            SEPARATOR,
            ButtonHolder(
                CONTINUE_BUTTON,
                cancel_seasonal_service(self.org_id),
                css_class="buttons",
            ),
        )


class SeasonalServiceEditDateForm(GOVUKModelForm):
    form_tag = False
    form_error_title = DEFAULT_ERROR_SUMMARY

    registration_code = forms.IntegerField(
        required=True,
        label=_("Service code"),
        error_messages={"required": _("Enter a service code in the box below")},
    )
    start = forms.DateTimeField(
        required=True,
        label=_("Service begins on"),
        error_messages={"invalid": _("Error first date")},
        widget=NumberInput(attrs={"type": "date"}),
    )
    end = forms.DateTimeField(
        required=True,
        label=_("Service ends on"),
        error_messages={"invalid": _("Error last date")},
        widget=NumberInput(attrs={"type": "date"}),
    )

    class Meta:
        model = SeasonalService
        fields = ("registration_code", "start", "end")

    def __init__(self, *args, **kwargs):
        self.licence = kwargs.pop("licence", None)
        self.org_id = kwargs.pop("org_id")
        super().__init__(*args, **kwargs)

    def get_layout(self):
        help_modal = render_to_string(
            "publish/snippets/help_modals/seasonal_services.html"
        )
        return Layout(
            Field(
                "registration_code",
                template="publish/seasonal_services/service_code_widget.html",
            ),
            HTML(
                format_html(
                    '<h2 class="govuk-heading-s">Service operating dates {}</h2>',
                    help_modal,
                )
            ),
            DateDiv(
                FieldNoErrors("start", wrapper_class="date"),
                FieldNoErrors("end", wrapper_class="date"),
                css_class="date-container",
            ),
            SEPARATOR,
            ButtonHolder(
                CONTINUE_BUTTON,
                cancel_seasonal_service(self.org_id),
                css_class="buttons",
            ),
        )

    def clean_registration_code(self):
        registration_code = self.cleaned_data["registration_code"]
        exists = SeasonalService.objects.filter(
            licence=self.licence, registration_code=registration_code
        ).exists()
        if exists:
            raise ValidationError(
                "This service code has already been set up with a date range"
            )
        return registration_code

    def clean(self):
        cleaned_data = self.cleaned_data
        start = cleaned_data.get("start")
        end = cleaned_data.get("end")
        if start is None or end is None:
            return cleaned_data

        if start >= end:
            raise ValidationError("Start date must be earlier than end date")
        return cleaned_data
