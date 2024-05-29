from datetime import datetime
from typing import Optional

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel

from transit_odp.organisation.constants import (
    ORG_ACTIVE,
    ORG_INACTIVE,
    ORG_NOT_YET_INVITED,
    ORG_PENDING_INVITE,
)
from transit_odp.organisation.managers import (
    BODSLicenceManager,
    ConsumerFeedbackManager,
    OrganisationManager,
)
from transit_odp.organisation.models import Dataset
from transit_odp.users.models import User


class Organisation(TimeStampedModel):
    class Meta(TimeStampedModel.Meta):
        ordering = ("name",)
        indexes = [models.Index(fields=["name"], name="organisation_name_idx")]

    name = models.CharField(_("Name of Organisation"), max_length=255, unique=True)
    short_name = models.CharField(_("Organisation Short Name"), max_length=255)
    key_contact = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="key_organisation",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(
        default=False, help_text="Whether the organisation is active or not"
    )
    is_abods_global_viewer = models.BooleanField(
        default=False,
        help_text="Whether organisation will be used solely for managing ABODS global viewer users",
    )
    licence_required = models.BooleanField(
        _("Whether an organisation requires a PSV licence"), null=True, default=None
    )

    objects = OrganisationManager()

    def __str__(self):
        return f"name='{self.name}'"

    @property
    def licence_not_required(self):
        """
        Inverts the behaviour of licence_required if a boolean otherwise returns
        False if licence_required is None.
        """
        if self.licence_required is None:
            return False
        elif self.licence_required:
            return False
        else:
            return True

    def get_latest_login_date(self) -> Optional[datetime]:
        """
        Returns the most recent login date.
        """
        dates = [user.last_login for user in self.users.all() if user.last_login]
        return max(dates) if dates else None

    def get_status(self) -> str:
        """
        Returns the status of the Organisation.
        """
        user_count = self.users.count()
        invitations = self.invitation_set.count()
        if self.is_active:
            return ORG_ACTIVE
        elif not self.is_active and invitations == 0 and user_count == 0:
            return ORG_NOT_YET_INVITED
        elif not self.is_active and user_count > 0:
            return ORG_INACTIVE
        elif not self.is_active and user_count == 0 and invitations > 0:
            return ORG_PENDING_INVITE
        else:
            return ""

    def get_invite_sent_date(self) -> Optional[datetime]:
        """
        Gets the earliest date that an invite was sent.
        """
        dates = [invite.sent for invite in self.invitation_set.all() if invite.sent]
        return min(dates) if dates else None

    def get_invite_accepted_date(self) -> Optional[datetime]:
        """
        Gets the earliest date that an invite was sent.
        """
        dates = [user.date_joined for user in self.users.all() if user.date_joined]
        return min(dates) if dates else None

    def get_absolute_url(self):
        return reverse("users:organisation-profile", kwargs={"pk": self.id})


class OperatorCode(models.Model):
    noc = models.CharField(_("National Operator Code"), max_length=20, unique=True)
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="nocs"
    )

    def __str__(self):
        return f"<OperatorCode noc='{self.noc}'>"


class Licence(models.Model):
    number = models.CharField(_("PSV Licence Number"), max_length=9, unique=True)
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="licences"
    )

    objects = BODSLicenceManager()

    def __str__(self):
        return f"id={self.id}, number={self.number!r}"


class ConsumerFeedback(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    dataset = models.ForeignKey(
        Dataset, null=True, on_delete=models.SET_NULL, related_name="feedback"
    )
    consumer = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL, related_name="feedback"
    )
    feedback = models.TextField(blank=False, null=False)
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="feedback"
    )

    objects = ConsumerFeedbackManager()

    def __str__(self):
        return f"id={self.id}, feedback={self.feedback}"
