from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import IntegerField
from django.utils.translation import ugettext_lazy as _

from transit_odp.users.constants import AccountType


class UserRoleMixin(models.Model):
    class Meta:
        abstract = True

    ACCOUNT_TYPE_CHOICES = (
        (AccountType.site_admin.value, "Site Admin"),
        (AccountType.org_admin.value, "Organisation Admin"),
        (AccountType.org_staff.value, "Organisation Staff"),
        (AccountType.developer.value, "Developer"),
        (AccountType.agent_user.value, "Agent User"),
    )

    account_type = IntegerField(
        default=AccountType.developer.value, choices=ACCOUNT_TYPE_CHOICES
    )

    @property
    def pretty_account_name(self):
        name = dict(self.ACCOUNT_TYPE_CHOICES)[self.account_type]
        if self.is_org_admin:
            return "Admin"
        elif self.is_standard_user:
            return "Standard"
        elif self.is_agent_user:
            return "Agent"
        return name

    @property
    def is_developer(self):
        return self.account_type == AccountType.developer.value

    @property
    def is_site_admin(self):
        return self.account_type == AccountType.site_admin.value

    @property
    def is_org_admin(self):
        return self.account_type == AccountType.org_admin.value

    @property
    def is_agent_user(self):
        return self.account_type == AccountType.agent_user.value

    @property
    def is_standard_user(self):
        return self.account_type == AccountType.org_staff.value

    @property
    def is_single_org_user(self):
        return self.account_type in (
            AccountType.org_admin.value,
            AccountType.org_staff.value,
        )

    @property
    def is_org_user(self):
        return self.account_type in (
            AccountType.org_admin.value,
            AccountType.org_staff.value,
            AccountType.agent_user.value,
        )

    def validate(self):
        if self.is_org_user ^ bool(self.organisation):
            # Ensure only org_users have an organisation and that it is not null
            raise ValidationError(
                _("Invalid organisation for account_type. Please contact support.")
            )
