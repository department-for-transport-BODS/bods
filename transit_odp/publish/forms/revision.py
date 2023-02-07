from crispy_forms.layout import HTML, ButtonHolder, Layout
from crispy_forms_govuk.forms import GOVUKModelForm
from crispy_forms_govuk.layout import ButtonSubmit, LinkButton
from crispy_forms_govuk.layout.fields import CheckboxSingleField
from django import forms
from django.utils.translation import gettext_lazy as _
from django_hosts import reverse

import config.hosts
from transit_odp.organisation.models import DatasetRevision
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
