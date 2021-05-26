import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction

from transit_odp.common.adapters import Invitation
from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.users.constants import AccountType
from transit_odp.users.managers import InvitationManager

pytestmark = pytest.mark.django_db


class TestUserModel:
    def test_user_get_absolute_url(self, user: settings.AUTH_USER_MODEL):
        # assert user.get_absolute_url() == f"/users/{user.username}/"
        assert user.get_absolute_url() is None

    def test_user_api_token(self, user: settings.AUTH_USER_MODEL):
        """Tests that an API Token is created for the user. This is used for DRF
        authentication"""
        assert user.auth_token is not None

    def test_staff_superuser_are_site_admins(self, user_factory):
        """Tests that users with staff or superuser privileges have site_admin
        account types"""
        staff = user_factory(is_staff=True, account_type=AccountType.developer.value)
        superuser = user_factory(
            is_superuser=True, account_type=AccountType.developer.value
        )
        assert staff.account_type == AccountType.site_admin.value
        assert superuser.account_type == AccountType.site_admin.value

    @pytest.mark.skip(reason="Can't test this since we move to m2m orgs")
    @pytest.mark.parametrize(
        "account_type", [AccountType.org_staff, AccountType.org_admin]
    )
    def test_org_user_must_have_org(self, account_type, user_factory):
        user = user_factory.build(organisations=())
        user.account_type = account_type.value
        with pytest.raises(ValidationError):
            user.save()

    @pytest.mark.parametrize(
        "account_type", [AccountType.org_staff, AccountType.org_admin]
    )
    def test_org_user_can_only_have_one_org(self, account_type, user_factory):
        user = user_factory(account_type=account_type)
        another_org = OrganisationFactory()
        with transaction.atomic():
            with pytest.raises(ValidationError):
                user.organisations.add(another_org)

        assert user.organisations.count() == 1

    @pytest.mark.parametrize(
        "account_type", [AccountType.site_admin, AccountType.developer]
    )
    def test_non_org_user_must_not_have_org(self, account_type, user_factory):
        user = user_factory(account_type=account_type.value, organisations=())
        org = OrganisationFactory()
        with transaction.atomic():
            with pytest.raises(ValidationError):
                user.organisations.add(org)
        assert user.organisations.count() == 0

    def test_user_settings(self, user: settings.AUTH_USER_MODEL):
        """Tests that user settings are created for a user"""
        assert user.settings.mute_all_dataset_notifications is False
        assert user.settings.notify_invitation_accepted is False


class TestInvitationModel:
    @pytest.mark.parametrize(
        "account_type", [AccountType.org_staff, AccountType.org_admin]
    )
    def test_org_user_must_have_org(self, account_type, invitation_factory):
        invitation = invitation_factory.build(organisation=None)
        invitation.account_type = account_type.value
        invitation.inviter.save()
        with pytest.raises(ValidationError):
            invitation.save()

    @pytest.mark.parametrize(
        "account_type", [AccountType.site_admin, AccountType.developer]
    )
    def test_non_org_user_must_not_have_org(self, account_type, invitation_factory):
        invitation = invitation_factory.build(account_type=account_type.value)
        invitation.organisation = OrganisationFactory()
        invitation.inviter.save()
        with pytest.raises(ValidationError):
            invitation.save()

    def test_invitation_manager_is_used(self):
        assert Invitation.objects == InvitationManager()

    def test_key_set_on_first_instantiation(self, invitation_factory):
        # Set up
        invitation = invitation_factory.build()
        # Assert
        assert invitation.key is not None
