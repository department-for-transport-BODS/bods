import pytest

from transit_odp.users.constants import AccountType
from transit_odp.users.factories import UserFactory
from transit_odp.users.forms.admin import UserCreationForm

pytestmark = pytest.mark.django_db


class TestUserCreationForm:
    def test_clean_username(self):
        # A user with proto_user params does not exist yet.
        proto_user = UserFactory.build(
            verified=False, account_type=AccountType.developer.value
        )
        # organisation = OrganisationFactory.create()
        organisation = None

        form = UserCreationForm(
            {
                "username": proto_user.username,
                "first_name": proto_user.first_name,
                "last_name": proto_user.last_name,
                "account_type": proto_user.account_type,
                "organisation": organisation,
                "email": proto_user.email,
                "password1": proto_user._password,
                "password2": proto_user._password,
            }
        )

        assert form.is_valid()
        assert form.clean_username() == proto_user.username

        # Creating a user.
        form.save()

        # The user with proto_user params already exists,
        # hence cannot be created.
        form = UserCreationForm(
            {
                "username": proto_user.username,
                "first_name": proto_user.first_name,
                "last_name": proto_user.last_name,
                "account_type": proto_user.account_type,
                "organisation": organisation,
                "email": proto_user.email,
                "password1": proto_user._password,
                "password2": proto_user._password,
            }
        )

        assert not form.is_valid()
        assert len(form.errors) == 1
        assert "username" in form.errors
