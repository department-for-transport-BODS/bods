from crispy_forms.layout import HTML, ButtonHolder, Layout
from transit_odp.frontend.forms import GOVUKModelForm
from transit_odp.frontend.layout import ButtonSubmit, LinkButton
from transit_odp.frontend.layout.fields import CheckboxSingleField
from django import forms
from django.utils.translation import gettext_lazy as _
from django_hosts import reverse
from waffle import flag_is_active

import config.hosts
from transit_odp.fares_validator.views.validate import FaresXmlValidator
from transit_odp.organisation.models import Dataset, DatasetRevision
from transit_odp.publish.forms.constants import DISABLE_SUBMIT_SCRIPT


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
        is_fares_validator_active = flag_is_active("", "is_fares_validator_active")
        if is_fares_validator_active:
            non_compliant_label = (
                "I acknowledge my data does not meet the required standard, as detailed "
                "in the validation report, and I am publishing non-compliant data to the "
                "Bus Open Data Service."
            )
            instance = kwargs.get("instance")

            org_id_list = Dataset.objects.filter(id=instance.dataset_id).values_list(
                "organisation_id", flat=True
            )

            validator_error = None
            if not self.get_validator_error(org_id_list[0], instance.id):
                validator_error = False
            else:
                validator_error = True

            if validator_error is True:
                consent_field.label = _(non_compliant_label)
            else:
                consent_field.label = _(consent_label)
        else:
            consent_field.label = _(consent_label)
        self.is_update = is_update

    class Meta:
        model = DatasetRevision
        fields = ("is_published",)

    def get_upload_file(self, revision_id):
        revision = DatasetRevision.objects.get(id=revision_id)
        upload_file = revision.upload_file
        return upload_file

    def get_validator_error(self, organisation_id, revision_id):
        upload_file = self.get_upload_file(revision_id)

        fares_validator_obj = FaresXmlValidator(
            upload_file, organisation_id, revision_id
        )
        fares_validator_errors = fares_validator_obj.get_errors()
        fares_validator_errors_list = fares_validator_errors.content.decode(
            "utf8"
        ).replace("'", '"')

        if fares_validator_errors_list == "[]":
            return False
        return True

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


class FaresRevisionPublishFormViolations(RevisionPublishForm):
    def get_layout(self):
        modify_name = "fares:update-modify"
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
                        "fares:revision-delete",
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
