import pytest
from allauth.account.models import EmailAddress

from transit_odp.users.constants import AccountType

pytestmark = pytest.mark.django_db


class TestUserFactory:
    @pytest.mark.parametrize(
        "account_type,has_org",
        [
            (AccountType.developer, False),
            (AccountType.org_staff, True),
            (AccountType.org_admin, True),
            (AccountType.site_admin, False),
        ],
    )
    def test_organisation_generation(
        self, account_type: AccountType, has_org: bool, user_factory
    ):
        """Tests the UserFactory generates an Organisation when account_type
        is an org user type"""
        user = user_factory(account_type=account_type)
        assert user.account_type == account_type
        assert bool(user.organisation) == has_org

    @pytest.mark.parametrize("verified", [True, None])
    def test_verified(self, verified, user_factory):
        # Setup
        user = user_factory(verified=verified)
        # Assert
        assert EmailAddress.objects.get(
            user=user, email=user.email, primary=True, verified=True
        )


class TestInvitationFactory:
    @pytest.mark.parametrize(
        "account_type,has_org",
        [
            (AccountType.developer, False),
            (AccountType.org_staff, True),
            (AccountType.org_admin, True),
            (AccountType.site_admin, False),
        ],
    )
    def test_organisation_generation(
        self, account_type: AccountType, has_org: bool, invitation_factory
    ):
        """Tests the UserFactory generates an Organisation when account_type
        is an org user type"""
        user = invitation_factory(account_type=account_type)
        assert user.account_type == account_type
        assert bool(user.organisation) == has_org
