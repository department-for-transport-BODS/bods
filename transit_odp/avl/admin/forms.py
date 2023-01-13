from datetime import date

from django import forms
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django.utils.translation import gettext as _

from transit_odp.avl.enums import AVL_FEED_UP
from transit_odp.avl.proxies import AVLDataset
from transit_odp.organisation.constants import LIVE, AVLType
from transit_odp.organisation.models import DatasetRevision, Organisation


class DummyDatafeedForm(forms.ModelForm):
    class Meta:
        model = AVLDataset
        fields = ("organisation",)

    username = forms.CharField(label="Username", required=True)
    password = forms.CharField(
        label="Password", required=True, widget=forms.PasswordInput
    )
    organisation = forms.ModelChoiceField(
        label="Organisation",
        required=True,
        queryset=Organisation.objects.filter(key_contact__isnull=False).all(),
        help_text="Cant see your organisation? make sure the key contact is defined.",
    )
    url = forms.URLField(label="URL", required=True)
    description = forms.CharField(label="Description", required=True)
    short_description = forms.CharField(label="Short Description", required=True)

    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, instance=instance, **kwargs)
        username = self.fields["username"]
        username.initial = instance.live_revision.username if instance else None

        url = self.fields["url"]
        url.initial = instance.live_revision.url_link if instance else None

        password = self.fields["password"]
        password.initial = instance.live_revision.password if instance else None

        organisation = self.fields["organisation"]
        organisation.label_from_instance = lambda obj: f"{obj.id} | {obj.name}"

        description = self.fields["description"]
        description.initial = instance.live_revision.description if instance else None

        short_description = self.fields["short_description"]
        short_description.initial = (
            instance.live_revision.short_description if instance else None
        )

    def save(self, commit=True):
        dataset_instance = super().save(commit=commit)
        return create_dummy_avl_datafeed(dataset_instance, **self.cleaned_data)


def create_dummy_avl_datafeed(
    datafeed: AVLDataset,
    url: str,
    username: str,
    password: str,
    organisation: Organisation,
    description: str,
    short_description: str,
) -> AVLDataset:
    """
    Creates/updates and returns a dummy datafeed with minimal fields required
    Args:
        datafeed: instance of AVLDataset returned by form
        url: url text box from django admin form
        password: password text box from django admin form
        username: username text box from django admin form
        organisation: organisation from dropdown on django admin form
        description: description text box from django admin form
        short_description: short_description text box from django admin form

    """
    datafeed.organisation = organisation
    datafeed.contact = organisation.key_contact
    datafeed.avl_feed_status = AVL_FEED_UP
    datafeed.dataset_type = AVLType
    datafeed.is_dummy = True

    datafeed.save()

    if datafeed.live_revision:
        # update if revision exists
        revision = datafeed.live_revision
        revision.url_link = url
        revision.password = password
        revision.username = username
        revision.short_description = short_description
        revision.description = description
        revision.save()
    else:
        revision = DatasetRevision.objects.create(
            is_published=True,
            published_at=now(),
            published_by=organisation.key_contact,
            url_link=url,
            status=LIVE,
            name=None,  # This will ensure a proper name gets generated
            dataset=datafeed,
            username=username,
            password=password,
            description=description,
            short_description=short_description,
            comment="First publication",
        )
        datafeed.live_revision = revision
        datafeed.save()

    return datafeed


class PostPublishingCheckReportAdminForm(forms.ModelForm):
    def clean_created(self):
        if self.cleaned_data["created"] > date.today():
            raise ValidationError(
                _("Creation date cannot be in the future"),
                code="created_future",
            )
        return self.cleaned_data["created"]

    def clean(self):
        cleaned_data = super().clean()
        if (
            not self.has_error("vehicle_activities_completely_matching")
            and not self.has_error("vehicle_activities_analysed")
            and cleaned_data["vehicle_activities_completely_matching"]
            > cleaned_data["vehicle_activities_analysed"]
        ):
            raise ValidationError(
                _("Matching vehicles must be less than or equal to vehicles analysed"),
                code="matching_gt_total",
            )
        return cleaned_data
