import pytest
from django.contrib.auth import get_user_model
from django_hosts.resolvers import reverse

from config.hosts import ADMIN_HOST
from transit_odp.site_admin.forms import CHECKBOX_FIELD_KEY
from transit_odp.users.constants import (
    AccountType,
    DeveloperType,
    OrgStaffType,
    SiteAdminType,
)

pytestmark = pytest.mark.django_db
User = get_user_model()


class TestRevokeDeveloperView:
    host = ADMIN_HOST

    def test_standard_user_cant_access(self, client_factory, user_factory):
        client = client_factory(host=self.host)
        user = user_factory(account_type=OrgStaffType)
        developer = user_factory(account_type=DeveloperType)
        url = reverse(
            "users:revoke-consumer",
            kwargs={"pk": developer.id},
            host=self.host,
        )
        client.force_login(user=user)
        response = client.get(url)
        assert response.status_code == 403

    def test_site_admin_can_access(self, client_factory, user_factory):
        client = client_factory(host=self.host)
        user = user_factory(account_type=SiteAdminType)
        developer = user_factory(account_type=DeveloperType)
        url = reverse(
            "users:revoke-consumer",
            kwargs={"pk": developer.id},
            host=self.host,
        )
        client.force_login(user=user)
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["user"] == developer
        assert "site_admin/consumers/revoke.html" in response.template_name

    def test_site_admin_cant_access_staff(self, client_factory, user_factory):
        """Make sure a site admin can't revoke a non-developer account."""
        client = client_factory(host=self.host)
        user = user_factory(account_type=SiteAdminType)
        staff = user_factory(account_type=OrgStaffType)
        url = reverse(
            "users:revoke-consumer",
            kwargs={"pk": staff.id},
            host=self.host,
        )
        client.force_login(user=user)
        response = client.get(url)
        assert response.status_code == 404

    def test_site_admin_can_cancel_revoke(self, client_factory, user_factory):
        client = client_factory(host=self.host)
        user = user_factory(account_type=SiteAdminType)
        developer = user_factory(account_type=DeveloperType)
        url = reverse(
            "users:revoke-consumer",
            kwargs={"pk": developer.id},
            host=self.host,
        )
        client.force_login(user=user)
        response = client.post(url, follow=True, data={"submit": "cancel"})
        assert response.status_code == 200
        assert response.context["user"] == developer
        assert response.context["user"].is_active
        assert "site_admin/consumers/detail.html" in response.template_name

    def test_site_admin_can_confirm_revoke(self, client_factory, user_factory):
        client = client_factory(host=self.host)
        user = user_factory(account_type=SiteAdminType)
        developer = user_factory(account_type=DeveloperType)
        url = reverse(
            "users:revoke-consumer",
            kwargs={"pk": developer.id},
            host=self.host,
        )
        client.force_login(user=user)
        response = client.post(url, follow=True, data={"submit": "confirm"})

        assert response.status_code == 200
        assert response.context["user"] == developer
        assert not response.context["user"].is_active
        assert "site_admin/consumers/revoke_success.html" in response.template_name


class TestEditNotesView:
    host = ADMIN_HOST
    view_name = "users:edit-consumer-notes"

    def test_standard_user_cant_access(self, client_factory, user_factory):
        client = client_factory(host=self.host)
        user = user_factory(account_type=OrgStaffType)
        developer = user_factory(account_type=DeveloperType)
        url = reverse(self.view_name, kwargs={"pk": developer.id}, host=self.host)
        client.force_login(user=user)
        response = client.get(url)
        assert response.status_code == 403

    def test_site_admin_can_access(self, client_factory, user_factory):
        client = client_factory(host=self.host)
        user = user_factory(account_type=SiteAdminType)
        developer = user_factory(account_type=DeveloperType)
        url = reverse(self.view_name, kwargs={"pk": developer.id}, host=self.host)
        client.force_login(user=user)
        response = client.get(url)
        assert response.status_code == 200
        assert response.context["user"] == developer
        assert "site_admin/consumers/edit_notes.html" in response.template_name

    def test_can_edit_developer_notes(self, client_factory, user_factory):
        client = client_factory(host=self.host)
        user = user_factory(account_type=SiteAdminType)
        developer = user_factory(account_type=DeveloperType, notes="original notes")
        url = reverse(self.view_name, kwargs={"pk": developer.id}, host=self.host)
        client.force_login(user=user)
        response = client.post(url, follow=True, data={"notes": "updated notes"})
        assert response.status_code == 200
        assert response.context["user"] == developer
        assert response.context["user"].notes == "updated notes"
        assert "site_admin/consumers/detail.html" in response.template_name


class TestConsumerListView:
    host = ADMIN_HOST
    url = reverse("users:consumer-list", host=host)

    def test_standard_user_cant_access(self, client_factory, user_factory):
        client = client_factory(host=self.host)
        user = user_factory(account_type=AccountType.org_staff.value)
        client.force_login(user=user)
        response = client.get(self.url)
        assert response.status_code == 403

    def test_site_admin_get_list(self, client_factory, user_factory):
        client = client_factory(host=self.host)
        user = user_factory(account_type=AccountType.site_admin.value)
        num_developers = 4
        for _ in range(num_developers):
            user_factory(account_type=AccountType.developer.value)

        user_factory(account_type=AccountType.org_staff.value)
        user_factory(account_type=AccountType.org_admin.value)

        client.force_login(user=user)
        response = client.get(self.url)
        assert response.status_code == 200
        table = response.context["table"]
        assert len(table.rows) == num_developers

    def test_email_filter(self, client_factory, user_factory):
        client = client_factory(host=self.host)
        user = user_factory(account_type=AccountType.site_admin.value)
        for letter in "abc" + "xyz" + "123" + "ABC":
            user_factory(
                email=f"{letter}@email.zz", account_type=AccountType.developer.value
            )

        user_factory(account_type=AccountType.org_staff.value)
        user_factory(account_type=AccountType.org_admin.value)
        client.force_login(user=user)

        for letter in "ABC":
            response = client.get(
                f"{self.url}?letters={letter}&letters=P&submitform=submit"
            )
            assert response.status_code == 200
            table = response.context["table"]
            assert len(table.rows) == 2

        for letter in "XYZ":
            response = client.get(
                f"{self.url}?letters={letter}&letters=P&submitform=submit"
            )
            assert response.status_code == 200
            table = response.context["table"]
            assert len(table.rows) == 1

        response = client.get(self.url, {"letters": "0-9"})
        assert response.status_code == 200
        table = response.context["table"]
        assert len(table.rows) == 3

    def test_bucket_counts(self, client_factory, user_factory):
        emails = [
            "0digit@site.com",
            "5digit@site.com",
            "aletter@site.com",
            "Aletter@site.com",
            "eletter@site.com",
            "zletter@site.com",
        ]
        _ = [user_factory(email=e, account_type=DeveloperType) for e in emails]

        client = client_factory(host=self.host)
        user = user_factory(account_type=SiteAdminType)
        client.force_login(user=user)
        response = client.get(self.url)
        assert response.status_code == 200

        first_letter_count = (
            response.context["filter"]
            .form.fields[CHECKBOX_FIELD_KEY]
            .first_letter_count
        )
        assert first_letter_count["0 - 9"] == 2
        assert first_letter_count["A"] == 2
        assert first_letter_count["E"] == 1
        assert first_letter_count["Z"] == 1
        for ch in "BCDFGHIJKLMNOPQRSTUVWXY":
            assert first_letter_count[ch] == 0
