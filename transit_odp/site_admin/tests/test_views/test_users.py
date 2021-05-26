import pytest
from django.contrib.auth import get_user_model
from django_hosts.resolvers import reverse

from config.hosts import ADMIN_HOST
from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.site_admin.views import UserDetailView, UserEditView
from transit_odp.users.constants import (
    AgentUserType,
    OrgAdminType,
    OrgStaffType,
    SiteAdminType,
)
from transit_odp.users.factories import AgentUserInviteFactory, UserFactory
from transit_odp.users.views.mixins import SiteAdminViewMixin

pytestmark = pytest.mark.django_db
User = get_user_model()


class TestUserDetailView:
    host = ADMIN_HOST

    def test_view_permission_mixin(self):
        """Tests the view subclasses SiteAdminViewMixin.

        The mixin has been tested in users/tests/test_view_mixins.py so we don't
        need to test the permissions again"""
        assert issubclass(UserDetailView, SiteAdminViewMixin)

    def test_correct_template_used(self, client_factory):
        user = UserFactory(account_type=SiteAdminType)
        organisation = OrganisationFactory()

        org_user = UserFactory(
            email="abc@abc.com",
            organisations=(organisation,),
            account_type=OrgAdminType,
        )

        url = reverse(
            "users:manage-user-detail",
            kwargs={"pk": organisation.id, "pk1": org_user.id},
            host=self.host,
        )

        client = client_factory(host=self.host)
        client.force_login(user=user)
        response = client.get(url)
        assert response.status_code == 200
        assert "site_admin/users_manage_detail.html" in [
            t.name for t in response.templates
        ]
        assert response.context["user"].email == org_user.email

    def test_agent_user_detail_with_invite(self, client_factory):
        site_admin = UserFactory(account_type=SiteAdminType)
        organisation = OrganisationFactory()
        agent = UserFactory(account_type=AgentUserType, organisations=(organisation,))
        invite = AgentUserInviteFactory(agent=agent, organisation=organisation)

        url = reverse(
            "users:manage-user-detail",
            kwargs={"pk": organisation.id, "pk1": agent.id},
            host=self.host,
        )

        client = client_factory(host=self.host)
        client.force_login(user=site_admin)

        response = client.get(url)

        assert response.status_code == 200
        assert "site_admin/users_manage_detail.html" in [
            t.name for t in response.templates
        ]
        assert response.context["user"].email == invite.agent.email
        assert response.context["invite"] == invite

    def test_user_does_not_exist(self, client_factory):
        user = UserFactory(account_type=SiteAdminType)
        organisation = OrganisationFactory.create()

        UserFactory(
            id=5,
            email="abc@abc.com",
            organisations=(organisation,),
            account_type=OrgAdminType,
        )

        url = reverse(
            "users:manage-user-detail",
            kwargs={"pk": organisation.id, "pk1": 10},
            host=self.host,
        )
        client = client_factory(host=self.host)
        client.force_login(user=user)
        response = client.get(url)
        assert response.status_code == 404


class TestUserEditView:
    host = ADMIN_HOST

    def test_view_permission_mixin(self):
        """Tests the view subclasses SiteAdminViewMixin.

        The mixin has been tested in users/tests/test_view_mixins.py so we don't
        need to test the permissions again"""
        assert issubclass(UserEditView, SiteAdminViewMixin)

    def test_correct_template_used(self, client_factory, user_factory):
        user = user_factory(account_type=SiteAdminType)
        organisation = OrganisationFactory.create()

        org_user = UserFactory.create(
            email="abc@abc.com",
            username="abc",
            organisations=(organisation,),
            account_type=OrgAdminType,
        )

        url = reverse(
            "users:manage-user-edit",
            kwargs={"pk": organisation.id, "pk1": org_user.id},
            host=self.host,
        )

        client = client_factory(host=self.host)
        client.force_login(user=user)
        data = {"email": "test@test.com", "username": "test", "account_type": 3}
        response = client.post(url, data=data)
        modified_user = User.objects.get(id=org_user.id)

        assert response.status_code == 302
        assert modified_user.email == data["email"]
        assert modified_user.username == data["username"]
        assert modified_user.account_type == data["account_type"]


class TestUserArchiveSuccessView:
    host = ADMIN_HOST

    def test_correct_template_used(self, client_factory):
        site_admin = UserFactory(account_type=SiteAdminType)
        organisation = OrganisationFactory()
        org_user = UserFactory(
            organisations=(organisation,), account_type=OrgStaffType, is_active=False
        )
        url = reverse(
            "users:org-user-archive-success",
            kwargs={"pk": organisation.id, "pk1": org_user.id},
            host=self.host,
        )

        client = client_factory(host=self.host)
        client.force_login(user=site_admin)
        response = client.get(url)

        expected_template = "site_admin/user_archive_success.html"
        assert response.status_code == 200
        assert expected_template in response.template_name
        assert response.context["object"] == org_user


class TestUserEditSuccessView:
    host = ADMIN_HOST

    def test_correct_template_used(self, client_factory):
        site_admin = UserFactory(account_type=SiteAdminType)
        organisation = OrganisationFactory()
        org_user = UserFactory(organisations=(organisation,), account_type=OrgStaffType)
        url = reverse(
            "users:manage-user-edit-success",
            kwargs={"pk": organisation.id, "pk1": org_user.id},
            host=self.host,
        )

        client = client_factory(host=self.host)
        client.force_login(user=site_admin)
        response = client.get(url)

        expected_template = "site_admin/users_manage_edit_success.html"
        assert response.status_code == 200
        assert expected_template in response.template_name
        assert response.context["user"] == org_user
