import pytest
from django_hosts import reverse

from config.hosts import ADMIN_HOST
from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import UserFactory
from transit_odp.users.models import User

pytestmark = pytest.mark.django_db


def change_form_data(user, **overrides):
    data = {
        "email": user.email,
        "username": user.username,
        "first_name": user.first_name or "First",
        "last_name": user.last_name or "Last",
        "account_type": user.account_type,
        "organisations": [org.id for org in user.organisations.all()],
        "dev_organisation": user.dev_organisation or "",
        "agent_organisation": user.agent_organisation or "",
        "description": user.description or "",
        "is_active": "on",
        "date_joined_0": user.date_joined.strftime("%Y-%m-%d"),
        "date_joined_1": user.date_joined.strftime("%H:%M:%S"),
    }
    data.update(overrides)
    return data


@pytest.fixture
def admin_client(client_factory):
    client = client_factory(host=ADMIN_HOST)
    superuser = UserFactory(
        account_type=AccountType.site_admin.value, is_staff=True, is_superuser=True
    )
    client.force_login(user=superuser)
    return client


@pytest.mark.parametrize(
    "account_type,org_count",
    [
        (AccountType.developer.value, 1),
        (AccountType.org_staff.value, 2),
        (AccountType.org_admin.value, 2),
    ],
)
def test_invalid_organisations_show_form_error_not_500(
    admin_client, account_type, org_count
):
    user = UserFactory(account_type=account_type)
    original_orgs = list(user.organisations.all())
    orgs = OrganisationFactory.create_batch(org_count)
    url = reverse("admin:users_user_change", args=[user.id], host=ADMIN_HOST)

    response = admin_client.post(
        url, change_form_data(user, organisations=[org.id for org in orgs])
    )

    assert response.status_code == 200
    assert "organisations" in response.context["adminform"].form.errors
    assert list(user.organisations.all()) == original_orgs


def test_moving_org_user_to_another_organisation_saves(admin_client):
    old_org, new_org = OrganisationFactory.create_batch(2)
    user = UserFactory(
        account_type=AccountType.org_staff.value, organisations=[old_org]
    )
    url = reverse("admin:users_user_change", args=[user.id], host=ADMIN_HOST)

    response = admin_client.post(
        url, change_form_data(user, organisations=[new_org.id])
    )

    assert response.status_code == 302
    assert list(user.organisations.all()) == [new_org]


@pytest.mark.parametrize(
    "account_type", [AccountType.site_admin.value, AccountType.developer.value]
)
def test_non_org_user_saves_without_organisation(admin_client, account_type):
    user = UserFactory(account_type=account_type)
    url = reverse("admin:users_user_change", args=[user.id], host=ADMIN_HOST)

    response = admin_client.post(url, change_form_data(user, organisations=[]))

    assert response.status_code == 302
    assert user.organisations.count() == 0


def test_org_user_still_requires_organisation(admin_client):
    user = UserFactory(account_type=AccountType.org_staff.value)
    url = reverse("admin:users_user_change", args=[user.id], host=ADMIN_HOST)

    response = admin_client.post(url, change_form_data(user, organisations=[]))

    assert response.status_code == 200
    assert "organisations" in response.context["adminform"].form.errors


def test_site_admin_with_stray_organisation_can_clear_it(admin_client):
    user = UserFactory(account_type=AccountType.site_admin.value)
    User.organisations.through.objects.create(
        user=user, organisation=OrganisationFactory()
    )
    url = reverse("admin:users_user_change", args=[user.id], host=ADMIN_HOST)

    response = admin_client.post(url, change_form_data(user, organisations=[]))

    assert response.status_code == 302
    assert user.organisations.count() == 0


@pytest.mark.parametrize("flag", ["is_staff", "is_superuser"])
def test_promoting_to_staff_without_organisation_saves_as_site_admin(
    admin_client, flag
):
    user = UserFactory(account_type=AccountType.developer.value)
    url = reverse("admin:users_user_change", args=[user.id], host=ADMIN_HOST)

    response = admin_client.post(
        url,
        change_form_data(
            user,
            account_type=AccountType.org_admin.value,
            organisations=[],
            **{flag: "on"},
        ),
    )

    assert response.status_code == 302
    user.refresh_from_db()
    assert user.account_type == AccountType.site_admin.value
    assert user.organisations.count() == 0


@pytest.mark.parametrize("flag", ["is_staff", "is_superuser"])
def test_promoting_to_staff_with_organisation_shows_form_error_not_500(
    admin_client, flag
):
    user = UserFactory(account_type=AccountType.developer.value)
    org = OrganisationFactory()
    url = reverse("admin:users_user_change", args=[user.id], host=ADMIN_HOST)

    response = admin_client.post(
        url,
        change_form_data(
            user,
            account_type=AccountType.org_staff.value,
            organisations=[org.id],
            **{flag: "on"},
        ),
    )

    assert response.status_code == 200
    assert "organisations" in response.context["adminform"].form.errors
    user.refresh_from_db()
    assert user.account_type == AccountType.developer.value
    assert user.organisations.count() == 0
