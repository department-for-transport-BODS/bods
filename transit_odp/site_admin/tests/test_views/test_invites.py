import pytest
from allauth.account.adapter import get_adapter
from django.contrib.auth import get_user_model
from django_hosts.resolvers import get_host, reverse

from config.hosts import ADMIN_HOST
from transit_odp.common.test_utils import add_session_middleware
from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.site_admin.views import (
    InviteView,
    OrganisationListView,
    ResendOrgUserInviteView,
)
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import InvitationFactory, UserFactory
from transit_odp.users.models import Invitation
from transit_odp.users.views.mixins import SiteAdminViewMixin

pytestmark = pytest.mark.django_db
User = get_user_model()


class TestBulkResendInvitesFeature:
    """
    Its important to note that when using the bulk resend feature
    we make a GET request to organisation-manage with queryparams
    success returns a 302 where we can POST to bulk-resend-invite
    note a 200 status code denotes an error that we are rendering
    to the user
    """

    host = ADMIN_HOST
    manage_url = reverse("users:organisation-manage", host=host)
    bulk_url = reverse("users:bulk-resend-invite", host=host)

    def setup_organisations(self):
        """
        Sets up users, invites and organisations. We have:
        2 organisations (one active one not) with 1 admin user each
        2 organisations without users (both inactive)
        :return:
        """
        orgs_with_users = []
        orgs_without_users = []
        for active in (True, False):
            old_invite = InvitationFactory.create(
                account_type=AccountType.org_admin, is_key_contact=True, accepted=True
            )
            user = UserFactory.create(
                account_type=old_invite.account_type,
                organisations=(old_invite.organisation,),
                email=old_invite.email,
            )
            old_invite.organisation.key_contact = user
            old_invite.organisation.is_active = active
            old_invite.organisation.save()

            orgs_with_users.append(old_invite.organisation)

            invite = InvitationFactory.create(
                account_type=AccountType.org_admin, is_key_contact=True, accepted=False
            )
            invite.organisation.is_active = False
            invite.organisation.save()
            orgs_without_users.append(invite.organisation)

        return orgs_with_users, orgs_without_users

    def test_view_permission_mixin(self):
        """Tests the view subclasses SiteAdminViewMixin.

        The mixin has been tested in users/tests/test_view_mixins.py so we don't
        need to test the permissions again"""
        assert issubclass(OrganisationListView, SiteAdminViewMixin)

    def test_standard_user_cant_access(self, client_factory, user_factory):
        client = client_factory(host=self.host)
        user = user_factory(account_type=AccountType.org_staff.value)
        client.force_login(user=user)
        response = client.get(self.bulk_url)
        assert response.status_code == 403

    def test_sending_multiple_invites(self, client_factory, user_factory, mailoutbox):
        client = client_factory(host=self.host)
        admin = user_factory(account_type=AccountType.site_admin.value)
        _, orgs = self.setup_organisations()

        client.force_login(user=admin)
        queryparams = "?bulk_invite=true"
        for org in orgs:
            queryparams += f"&invites={org.id}"

        response = client.get(self.manage_url + queryparams)
        assert response.status_code == 302

        response = client.post(self.bulk_url, data={"submit": "submit"})
        expected_results = (
            Invitation.objects.filter(organisation_id__in=[org.id for org in orgs])
            .order_by("email")
            .values_list("email", flat=True)
        )
        assert response.status_code == 302
        assert sorted([mail.to[0] for mail in mailoutbox]) == list(expected_results)

    def test_returns_error_when_no_org_is_selected(self, client_factory, user_factory):
        self.setup_organisations()
        client = client_factory(host=self.host)
        admin = user_factory(account_type=AccountType.site_admin.value)
        client.force_login(user=admin)
        response = client.get(self.manage_url + "?bulk_invite=true")
        assert response.status_code == 200
        assert (
            response.context_data["form"].errors["__all__"].data[0].message
            == "Please select organisation(s) from below to resend invitation"
        )

    def test_returns_error_when_active_org_is_selected(
        self, client_factory, user_factory
    ):
        active_orgs, inactive_orgs = self.setup_organisations()

        client = client_factory(host=self.host)
        admin = user_factory(account_type=AccountType.site_admin.value)
        client.force_login(user=admin)
        queryparams = "?bulk_invite=true"
        for org in active_orgs[:-1] + inactive_orgs:
            queryparams += f"&invites={org.id}"

        response = client.get(self.manage_url + queryparams)
        assert response.status_code == 200
        assert response.context_data["form"].errors["__all__"].data[0].message == (
            "You cannot send invites to already active organisations, "
            "please select pending ones"
        )

    def test_nothing_bad_happens_with_bad_org_ids(
        self, client_factory, user_factory, mailoutbox
    ):
        client = client_factory(host=self.host)
        admin = user_factory(account_type=AccountType.site_admin.value)
        _, orgs = self.setup_organisations()

        client.force_login(user=admin)
        queryparams = "?bulk_invite=true"
        for org in orgs:
            queryparams += f"&invites={org.id}"

        response = client.get(self.manage_url + queryparams + "&invites=99999")
        assert response.status_code == 302

        response = client.post(self.bulk_url, data={"submit": "submit"})
        expected_results = (
            Invitation.objects.filter(organisation_id__in=[org.id for org in orgs])
            .order_by("email")
            .values_list("email", flat=True)
        )
        assert response.status_code == 302
        assert sorted([mail.to[0] for mail in mailoutbox]) == list(expected_results)

    def test_nothing_bad_happens_with_bad_bulk_invite_arg(
        self, client_factory, user_factory, mailoutbox
    ):
        client = client_factory(host=self.host)
        admin = user_factory(account_type=AccountType.site_admin.value)
        _, orgs = self.setup_organisations()

        client.force_login(user=admin)
        queryparams = "?bulk_invite=badwordhere"
        for org in orgs:
            queryparams += f"&invites={org.id}"

        response = client.get(self.manage_url + queryparams)
        assert response.status_code == 302

        response = client.post(self.bulk_url, data={"submit": "submit"})
        expected_results = (
            Invitation.objects.filter(organisation_id__in=[org.id for org in orgs])
            .order_by("email")
            .values_list("email", flat=True)
        )
        assert response.status_code == 302
        assert sorted([mail.to[0] for mail in mailoutbox]) == list(expected_results)


class TestInviteView:
    host = ADMIN_HOST

    def test_view_permission_mixin(self):
        """Tests the view subclasses SiteAdminViewMixin.

        The mixin has been tested in users/tests/test_view_mixins.py so we don't
        need to test the permissions again"""
        assert issubclass(InviteView, SiteAdminViewMixin)

    def test_correct_template_used(self, client_factory):
        client = client_factory(host=self.host)
        user = UserFactory(account_type=AccountType.site_admin.value)
        client.force_login(user=user)
        org = OrganisationFactory.create()
        url = reverse("users:org-user-invite", kwargs={"pk": org.id}, host=self.host)

        response = client.get(url)

        assert response.status_code == 200
        assert "site_admin/users_invite.html" in [t.name for t in response.templates]

    def test_stash_data(self, request_factory, mocker):
        """Tests data is stashed in session"""
        request = request_factory.get("fake-url/")
        request = add_session_middleware(request)

        view = InviteView()
        view.request = request

        mocked_form = mocker.Mock()
        mocked_form.cleaned_data = {"email": "test@test.com"}
        adapter = get_adapter(request)
        view.stash_data(mocked_form)

        assert adapter.stash_contains_invite_email(request)
        assert adapter.unstash_invite_email(request) == "test@test.com"


class TestResendOrgUserInviteView:
    host = ADMIN_HOST

    def test_view_permission_mixin(self):
        """Tests the view subclasses SiteAdminViewMixin.

        The mixin has been tested in users/tests/test_view_mixins.py so we don't
        need to test the permissions again"""
        assert issubclass(ResendOrgUserInviteView, SiteAdminViewMixin)

    def test_correct_template_used(self, mocker, request_factory):
        view = ResendOrgUserInviteView()
        user = UserFactory(account_type=AccountType.site_admin.value)
        organisation = OrganisationFactory.create()

        mocked_invitation = mocker.Mock(id=123)
        mocker.patch.object(view, "get_object", return_value=mocked_invitation)
        mocker.patch.object(view, "get_organisation", return_value=organisation)

        request = request_factory.get("fake-url/")
        request.user = user
        request.host = get_host(self.host)

        view.request = request

        response = view.post(request)

        assert response.status_code == 302
        mocked_invitation.send_invitation.assert_called_once_with(request)
        assert response.url == reverse(
            "users:manage-user-re-invite-success",
            kwargs={"pk": organisation.id, "pk1": mocked_invitation.id},
            host=self.host,
        )
