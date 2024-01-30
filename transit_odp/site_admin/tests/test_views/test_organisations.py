from datetime import datetime, timedelta
from random import randint

import pytest
from django.contrib.auth import get_user_model
from django_hosts.resolvers import reverse

import config.hosts
from transit_odp.organisation.constants import (
    ORG_ACTIVE,
    ORG_INACTIVE,
    ORG_NOT_YET_INVITED,
    ORG_PENDING_INVITE,
)
from transit_odp.organisation.factories import (
    OperatorCodeFactory,
    OrganisationFactory,
    ServiceCodeExemptionFactory,
)
from transit_odp.organisation.models import Organisation, ServiceCodeExemption
from transit_odp.site_admin.forms import CHECKBOX_FIELD_KEY
from transit_odp.site_admin.forms.service_code_exemptions import DUPLICATE_SERVICE_CODE
from transit_odp.site_admin.views import (
    OrganisationArchiveView,
    OrganisationCreateView,
    OrganisationDetailView,
    OrganisationListView,
    OrganisationUsersManageView,
)
from transit_odp.users.constants import AccountType, OrgAdminType, SiteAdminType
from transit_odp.users.factories import (
    AgentUserFactory,
    AgentUserInviteFactory,
    InvitationFactory,
    UserFactory,
)
from transit_odp.users.models import Invitation
from transit_odp.users.views.mixins import SiteAdminViewMixin

pytestmark = pytest.mark.django_db
User = get_user_model()

TEST_NUMBER_ACTIVE_ORGS = 6
TEST_NUMBER_INACTIVE_ORGS = 5
TEST_NUMBER_PENDING_ORGS = 4
TEST_NUMBER_NOT_YET_INVITED_ORGS = 3


class TestOrganisationListView:
    host = config.hosts.ADMIN_HOST
    url = reverse("users:organisation-manage", host=config.hosts.ADMIN_HOST)

    def test_view_permission_mixin(self):
        """Tests the view subclasses SiteAdminViewMixin.

        The mixin has been tested in users/tests/test_view_mixins.py so we don't
        need to test the permissions again"""
        assert issubclass(OrganisationListView, SiteAdminViewMixin)

    def test_standard_user_cant_access(self, client_factory, user_factory):
        client = client_factory(host=self.host)
        user = user_factory(account_type=AccountType.org_staff.value)
        client.force_login(user=user)
        response = client.get(self.url)
        assert response.status_code == 403

    def test_correct_template_used(self, client_factory, user_factory):
        client = client_factory(host=self.host)
        user = user_factory(account_type=AccountType.site_admin.value)
        client.force_login(user=user)
        response = client.get(self.url)
        assert response.status_code == 200
        assert "site_admin/organisation_list.html" in [
            t.name for t in response.templates
        ]

    def test_queryset_has_annotations(self, client_factory):
        client = client_factory(host=self.host)
        organisation = OrganisationFactory.create()
        user = UserFactory.create(account_type=AccountType.site_admin.value)
        client.force_login(user=user)
        UserFactory.create(
            account_type=AccountType.org_admin.value, organisations=[organisation]
        )
        UserFactory.create_batch(
            3, account_type=AccountType.org_staff.value, organisations=[organisation]
        )
        response = client.get(self.url)
        queryset = response.context_data["object_list"]
        assert list(queryset) == [organisation]
        expected_org = queryset.first()
        assert expected_org.status == ORG_ACTIVE
        assert expected_org.first_letter == organisation.name[0].upper()

    def test_filter_by_operator(self, user_factory, client_factory):
        admin = user_factory(account_type=AccountType.site_admin.value)
        [OrganisationFactory.create(name=name) for name in list("abc")]
        expected = [OrganisationFactory.create(name=name) for name in list("xyz")]

        client = client_factory(host=self.host)
        client.force_login(user=admin)
        url = f"{self.url}?letters=X&letters=Y&letters=Z&submitform=submit"
        response = client.get(url)

        context = response.context
        orgs = context["organisation_list"]
        assert list(orgs.order_by("id")) == expected

    def test_filter_by_status(self, user_factory, client_factory):
        admin = user_factory(account_type=AccountType.site_admin.value)

        active = []
        for _ in range(TEST_NUMBER_ACTIVE_ORGS):
            org = OrganisationFactory.create(is_active=True)
            active.append(org)

        inactive = []
        for _ in range(TEST_NUMBER_INACTIVE_ORGS):
            org = OrganisationFactory.create(is_active=False)
            UserFactory.create(
                account_type=AccountType.org_admin.value, organisations=[org]
            )
            inactive.append(org)

        pending = []
        for _ in range(TEST_NUMBER_PENDING_ORGS):
            org = OrganisationFactory.create(
                is_active=False,
            )
            InvitationFactory.create(
                organisation=org,
                account_type=OrgAdminType,
            )
            pending.append(org)

        not_yet_invited = []
        for _ in range(TEST_NUMBER_NOT_YET_INVITED_ORGS):
            org = OrganisationFactory.create(
                is_active=False,
            )
            not_yet_invited.append(org)

        client = client_factory(host=self.host)
        client.force_login(user=admin)

        response = client.get(self.url, {"status": ORG_ACTIVE})
        context = response.context
        orgs = context["organisation_list"]
        assert len(orgs) == TEST_NUMBER_ACTIVE_ORGS
        assert list(orgs.order_by("id")) == active

        response = client.get(self.url, {"status": ORG_INACTIVE})
        context = response.context
        orgs = context["organisation_list"]
        assert len(orgs) == TEST_NUMBER_INACTIVE_ORGS
        assert list(orgs.order_by("id")) == inactive

        response = client.get(self.url, {"status": ORG_NOT_YET_INVITED})
        context = response.context
        orgs = context["organisation_list"]
        assert len(orgs) == TEST_NUMBER_NOT_YET_INVITED_ORGS
        assert list(orgs.order_by("id")) == not_yet_invited

        response = client.get(self.url, {"status": ORG_PENDING_INVITE})
        context = response.context
        orgs = context["organisation_list"]
        assert len(orgs) == TEST_NUMBER_PENDING_ORGS
        assert list(orgs.order_by("id")) == pending

    def test_bucket_counts(self, client_factory, user_factory):
        org_names = [
            "Aorganisation",
            "aorganisation",
            "Borganisation",
            "dorganisation",
            "Zorganisation",
        ]
        _ = [OrganisationFactory(name=name) for name in org_names]

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
        assert first_letter_count["0 - 9"] == 0
        assert first_letter_count["A"] == 2
        assert first_letter_count["B"] == 1
        assert first_letter_count["D"] == 1
        assert first_letter_count["Z"] == 1
        for ch in "CEFGHIJKLMNOPQRSTUVWXY":
            assert first_letter_count[ch] == 0


class TestOrganisationCreateView:
    host = config.hosts.ADMIN_HOST
    url = reverse("users:organisation-new", host=config.hosts.ADMIN_HOST)
    target_module = "transit_odp.users.views.site_management"
    invitee_email = "invited_org_admin@testO.com"
    test_organisation_name = "Test Organisation"
    test_organisation_short_name = "testO"
    default_form_data = {
        "nocs-__prefix__-DELETE": "",
        "nocs-__prefix__-noc": "",
        "nocs-__prefix__-id": "",
        "nocs-TOTAL_FORMS": "3",
        "nocs-INITIAL_FORMS": "0",
        "nocs-MIN_NUM_FORMS": "1",
        "nocs-MAX_NUM_FORMS": "1000",
        "licences-TOTAL_FORMS": "3",
        "licences-INITIAL_FORMS": "0",
        "name": test_organisation_name,
        "short_name": test_organisation_short_name,
        "email": invitee_email,
    }

    def test_view_permission_mixin(self):
        """Tests the view subclasses SiteAdminViewMixin.

        The mixin has been tested in users/tests/test_view_mixins.py so we don't
        need to test the permissions again"""
        assert issubclass(OrganisationCreateView, SiteAdminViewMixin)

    def test_correct_template_used(self, client_factory, user_factory):
        client = client_factory(host=self.host)

        user = user_factory(account_type=AccountType.site_admin.value)
        client.force_login(user=user)

        response = client.get(self.url)

        assert response.status_code == 200
        assert "site_admin/organisation_form.html" in [
            t.name for t in response.templates
        ]

    def test_form_value_creates_org_and_sends_invitation(
        self, client_factory, mailoutbox
    ):
        client = client_factory(host=self.host)
        user = UserFactory(account_type=AccountType.site_admin.value)
        client.force_login(user=user)
        data = self.default_form_data.copy()
        for index in range(3):
            data.update(
                {
                    f"nocs-{index}-noc": f"noc{index}",
                    f"nocs-{index}-id": "",
                    f"nocs-{index}-DELETE": "",
                }
            )

        response = client.post(self.url, data)
        organisation = Organisation.objects.get(name="Test Organisation")
        invite = Invitation.objects.get(email=self.invitee_email)
        assert (
            response.status_code == 302
        ), "assert we get successfully redirected on POST "
        assert (
            organisation.short_name == self.test_organisation_short_name
        ), "assert we created the correct organisation"
        assert (
            organisation.nocs.count() == 3
        ), "assert we have the correct number of noc codes on the organisation"
        assert (
            mailoutbox[-1].subject == "You have been invited to publish bus data"
        ), "assert we receive an email"
        assert (
            mailoutbox[-1].to[0] == self.invitee_email
        ), "assert email is sent to correct person"
        assert (
            invite.is_key_contact is True
        ), "assert invite is created with key contact flag set to true"
        assert (
            invite.email == self.invitee_email
        ), "assert invite is created with correct email"

    def test_empty_nocs_fail_loudly(self, client_factory):
        client = client_factory(host=self.host)
        user = UserFactory(account_type=AccountType.site_admin.value)
        client.force_login(user=user)
        data = self.default_form_data.copy()
        data.update(
            {
                "nocs-0-noc": "",
                "nocs-0-id": "",
                "nocs-0-DELETE": "",
                "nocs-TOTAL_FORMS": "1",
            }
        )

        response = client.post(self.url, data)
        assert response.status_code == 200
        expected = "National Operator Code cannot be blank"
        assert response.context_data["form"].nested_noc.errors[0]["noc"][0] == expected

    def test_absent_nocs_fail_loudly(self, client_factory):
        client = client_factory(host=self.host)
        user = UserFactory(account_type=AccountType.site_admin.value)
        client.force_login(user=user)
        data = self.default_form_data.copy()
        data.update(
            {
                "nocs-0-noc": "",
                "nocs-0-id": "",
                "nocs-0-DELETE": "",
                "nocs-TOTAL_FORMS": "1",
            }
        )

        response = client.post(self.url, data)
        assert response.status_code == 200
        expected = "Please submit 1 or more National Operator Codes"
        assert response.context_data["form"].nested_noc.non_form_errors()[0] == expected

    def test_clashing_nocs_fail_loudly(self, client_factory):
        OrganisationFactory(nocs=["clash1"])
        client = client_factory(host=self.host)
        user = UserFactory(account_type=AccountType.site_admin.value)
        client.force_login(user=user)
        data = self.default_form_data.copy()
        data.update(
            {
                "nocs-0-noc": "clash1",
                "nocs-0-id": "",
                "nocs-0-DELETE": "",
                "nocs-TOTAL_FORMS": "1",
            }
        )

        response = client.post(self.url, data)
        assert response.status_code == 200
        expected = "Operator code with this National Operator Code already exists."
        assert response.context_data["form"].nested_noc.errors[0]["noc"][0] == expected

    def test_clashing_email_already_exists_fails_loudly(self, client_factory):
        email = self.invitee_email
        Invitation.objects.create(email=email)

        client = client_factory(host=self.host)
        user = UserFactory(account_type=SiteAdminType)
        client.force_login(user=user)
        data = self.default_form_data.copy()
        # data.update({"email": email})

        response = client.post(self.url, data)
        assert response.status_code == 200
        expected = f"{email} has been already invited."
        assert response.context_data["form"].errors["email"][0] == expected

    @pytest.mark.skip
    def test_existing_invite_error(self, client_factory):
        four_days_ago = datetime.now() - timedelta(days=4)
        client = client_factory(host=self.host)
        old_org = OrganisationFactory()
        admin = UserFactory(account_type=AccountType.site_admin.value)

        old_invite = InvitationFactory(
            email="invited_org_admin@testO.com",
            organisation=old_org,
            sent=four_days_ago,
            account_type=AccountType.org_admin.value,
            is_key_contact=True,
        )
        client.force_login(user=admin)
        data = self.default_form_data.copy()
        data.update({"nocs-0-noc": f"{data['short_name']}1"})
        response = client.post(self.url, data)
        invitation = Invitation.objects.get(id=old_invite.id)
        assert response.status_code == 302
        assert invitation.organisation.name == self.test_organisation_name
        assert invitation.organisation.short_name == self.test_organisation_short_name
        assert invitation.sent.day == datetime.now().day, "sent out today"
        assert invitation.inviter == admin

    def test_create_org_without_key_contact(self, client_factory):
        client = client_factory(host=self.host)
        user = UserFactory(account_type=AccountType.site_admin.value)
        client.force_login(user=user)
        data = self.default_form_data.copy()
        data.update({"email": "", "nocs-0-noc": f"{data['short_name']}1"})

        response = client.post(self.url, data)
        assert response.status_code == 302
        orgs = Organisation.objects.all()
        assert orgs.count() == 1
        assert orgs.first().name == "Test Organisation"
        assert Invitation.objects.count() == 0

    def test_create_org_with_psv_licence(self, client_factory):
        client = client_factory(host=self.host)
        user = UserFactory(account_type=AccountType.site_admin.value)
        client.force_login(user=user)
        data = self.default_form_data.copy()
        licence_number = "PS0000001"
        data.update(
            {
                "email": "",
                "nocs-0-noc": f"{data['short_name']}1",
                "licences-0-number": licence_number,
            }
        )

        response = client.post(self.url, data)
        assert response.status_code == 302
        org = Organisation.objects.first()
        assert org.licences.count() == 1
        assert org.licences.first().number == licence_number

    def test_badly_formatted_licence_fails_loudly(self, client_factory):
        OrganisationFactory()
        client = client_factory(host=self.host)
        user = UserFactory(account_type=AccountType.site_admin.value)
        client.force_login(user=user)
        data = self.default_form_data.copy()
        data.update(
            {
                "email": "",
                "nocs-0-noc": f"{data['short_name']}1",
                "licences-0-number": "INVALID",
            }
        )

        response = client.post(self.url, data)
        assert response.status_code == 200
        expected_error = "Licence number entered with the wrong format"
        assert (
            response.context_data["form"].nested_psv.errors[0]["number"][0]
            == expected_error
        )

    def test_clashing_licence_fails_loudly(self, client_factory):
        licence_number = "PS0000001"
        OrganisationFactory(licences=[licence_number])
        client = client_factory(host=self.host)
        user = UserFactory(account_type=AccountType.site_admin.value)
        client.force_login(user=user)
        data = self.default_form_data.copy()
        data.update(
            {
                "email": "",
                "nocs-0-noc": f"{data['short_name']}1",
                "licences-0-number": licence_number,
            }
        )

        response = client.post(self.url, data)
        assert response.status_code == 200
        expected_error = "Licence with this PSV Licence Number already exists."
        assert (
            response.context_data["form"].nested_psv.errors[0]["number"][0]
            == expected_error
        )


class TestOrganisationDetailView:
    host = config.hosts.ADMIN_HOST

    def test_view_permission_mixin(self):
        """Tests the view subclasses SiteAdminViewMixin.

        The mixin has been tested in users/tests/test_view_mixins.py so we don't
        need to test the permissions again"""
        assert issubclass(OrganisationDetailView, SiteAdminViewMixin)

    def test_correct_template_used(self, client_factory, user_factory):
        client = client_factory(host=self.host)

        user = user_factory(account_type=AccountType.site_admin.value)
        client.force_login(user=user)

        organisation = OrganisationFactory()
        url = reverse(
            "users:organisation-detail", args=[organisation.id], host=self.host
        )

        response = client.get(url)

        assert response.status_code == 200
        assert "site_admin/organisation_detail.html" in [
            t.name for t in response.templates
        ]


class TestOrganisationEditView:
    default_management_form_data = {
        "nocs-TOTAL_FORMS": ["1"],
        "nocs-INITIAL_FORMS": ["1"],
        "nocs-MIN_NUM_FORMS": ["1"],
        "nocs-MAX_NUM_FORMS": ["1000"],
        "nocs-0-id": ["9"],
        "nocs-0-noc": ["2"],
        "nocs-0-DELETE": [""],
        "nocs-__prefix__-id": [""],
        "nocs-__prefix__-noc": [""],
        "nocs-__prefix__-DELETE": [""],
        "licences-TOTAL_FORMS": ["0"],
        "licences-INITIAL_FORMS": ["0"],
        "licences-MIN_NUM_FORMS": ["0"],
        "licences-MAX_NUM_FORMS": ["1000"],
        "licences-__prefix__-id": "",
        "licences-__prefix__-number": "",
        "licences-__prefix__-DELETE": "",
        "licence_required": "off",
    }

    def test_unsafe_get_doesnt_edit_organisation(self, client_factory):
        host = config.hosts.ADMIN_HOST
        client = client_factory(host=host)
        org = OrganisationFactory.create(name="TestOrganisation", short_name="TestOrg")
        user = UserFactory.create(account_type=AccountType.site_admin.value)
        client.force_login(user=user)
        url = reverse("users:organisation-update", host=host, kwargs={"pk": org.id})
        response = client.get(url)
        Organisation.objects.get(pk=org.id)
        assert response.status_code == 200

    def test_cancel_button_update_page(self, client_factory):
        host = config.hosts.ADMIN_HOST
        org = OrganisationFactory.create(name="TestOrganisation", short_name="TestOrg")
        OperatorCodeFactory.create(id=9, noc="2", organisation=org)
        org_user = UserFactory.create(
            id=10, account_type=AccountType.org_admin.value, organisations=(org,)
        )
        org.key_contact = org_user
        org.save()

        user = UserFactory(account_type=AccountType.site_admin.value)

        url_update = reverse(
            "users:organisation-update",
            host=config.hosts.ADMIN_HOST,
            kwargs={"pk": org.id},
        )
        url_cancel = reverse(
            "users:organisation-detail",
            host=config.hosts.ADMIN_HOST,
            kwargs={"pk": org.id},
        )

        client = client_factory(host=host)
        client.force_login(user=user)

        response = client.get(url_update)
        assert response.status_code == 200
        assert response.context["form"].cancel_url == url_cancel

    def test_edit_name_short_name(self, client_factory):
        host = config.hosts.ADMIN_HOST
        org = OrganisationFactory.create(name="TestOrganisation", short_name="TestOrg")
        OperatorCodeFactory.create(id=9, noc="2", organisation=org)
        org_user = UserFactory.create(
            id=10, account_type=AccountType.org_admin.value, organisations=(org,)
        )
        org.key_contact = org_user
        org.save()

        user = UserFactory(account_type=AccountType.site_admin.value)

        url = reverse(
            "users:organisation-update",
            host=config.hosts.ADMIN_HOST,
            kwargs={"pk": org.id},
        )

        client = client_factory(host=host)
        client.force_login(user=user)

        data = self.default_management_form_data.copy()
        data.update(
            {
                "name": ["TestOrganisation1"],
                "short_name": ["TestOrg1"],
                "key_contact": ["10"],
            }
        )

        response = client.post(url, data=data)

        modified_org = Organisation.objects.get(id=org.id)

        assert response.status_code == 302
        assert modified_org.name == "TestOrganisation1"
        assert modified_org.short_name == "TestOrg1"

    def test_edit_key_contact(self, client_factory):
        host = config.hosts.ADMIN_HOST

        org = OrganisationFactory.create(name="TestOrganisation", short_name="TestOrg")

        OperatorCodeFactory.create(id=9, noc="2", organisation=org)

        org_user1 = UserFactory.create(
            id=10,
            account_type=AccountType.org_admin.value,
            organisations=(org,),
            email="org_user1@org_user1.com",
        )

        UserFactory.create(
            id=11,
            account_type=AccountType.org_admin.value,
            organisations=(org,),
            email="org_user2@org_user2.com",
        )

        org.key_contact = org_user1
        org.save()

        user = UserFactory(account_type=AccountType.site_admin.value)

        url = reverse(
            "users:organisation-update",
            host=config.hosts.ADMIN_HOST,
            kwargs={"pk": org.id},
        )

        client = client_factory(host=host)
        client.force_login(user=user)

        data = self.default_management_form_data.copy()
        data.update(
            {
                "name": ["TestOrganisation"],
                "short_name": ["TestOrg"],
                "key_contact": ["11"],  # org_user2
            }
        )

        response = client.post(url, data=data)
        modified_org = Organisation.objects.get(id=org.id)

        assert response.status_code == 302
        assert modified_org.key_contact.id == 11
        assert modified_org.key_contact.email == "org_user2@org_user2.com"

    def test_edit_no_licence_back_to_organisation_datail(self, client_factory):
        host = config.hosts.ADMIN_HOST
        org = OrganisationFactory.create(name="TestOrganisation", short_name="TestOrg")
        OperatorCodeFactory.create(id=9, noc="2", organisation=org)
        org_user = UserFactory.create(
            id=10, account_type=AccountType.org_admin.value, organisations=(org,)
        )
        org.key_contact = org_user
        org.save()

        user = UserFactory(account_type=AccountType.site_admin.value)

        url = reverse(
            "users:organisation-update",
            host=config.hosts.ADMIN_HOST,
            kwargs={"pk": org.id},
        )

        client = client_factory(host=host)
        client.force_login(user=user)

        data = self.default_management_form_data.copy()
        data.update(
            {
                "key_contact": "",
                "licence_required": "on",
            }
        )

        response = client.post(url, data=data)

        modified_org = Organisation.objects.get(id=org.id)

        assert response.status_code == 200
        assert modified_org.name == "TestOrganisation"
        assert modified_org.short_name == "TestOrg"


class TestOrganisationArchiveView:
    def test_view_permission_mixin(self):
        """Tests the view subclasses SiteAdminViewMixin.

        The mixin has been tested in users/tests/test_view_mixins.py so we don't
        need to test the permissions again"""
        assert issubclass(OrganisationArchiveView, SiteAdminViewMixin)

    def test_deactivate_org(self, client_factory, user_factory):
        organisation = OrganisationFactory.create()
        host = config.hosts.ADMIN_HOST
        url = reverse(
            "users:organisation-archive",
            kwargs={"pk": organisation.id},
            host=config.hosts.ADMIN_HOST,
        )

        client = client_factory(host=host)

        user = user_factory(account_type=AccountType.site_admin.value)
        client.force_login(user=user)

        response = client.get(url)

        assert response.status_code == 200
        assert "site_admin/organisation_archive.html" in [
            t.name for t in response.templates
        ]

    def test_form_deactivate_org(self, client_factory):
        organisation = OrganisationFactory.create()
        user1 = UserFactory.create(
            account_type=AccountType.org_staff.value, organisations=(organisation,)
        )
        agent_user = AgentUserFactory(organisations=(organisation,))
        host = config.hosts.ADMIN_HOST
        url = reverse(
            "users:organisation-archive",
            kwargs={"pk": organisation.id},
            host=config.hosts.ADMIN_HOST,
        )

        client = client_factory(host=host)
        user = UserFactory(account_type=AccountType.site_admin.value)
        client.force_login(user=user)

        assert organisation.is_active
        assert user1.is_active
        assert agent_user.is_active
        assert agent_user.organisations.count() == 1

        response = client.post(url, {})

        organisation.refresh_from_db()
        user1.refresh_from_db()
        agent_user.refresh_from_db()

        assert response.status_code == 302
        assert not organisation.is_active
        assert not user1.is_active
        assert agent_user.is_active
        assert agent_user.organisations.count() == 0

    def test_activate_org(self, client_factory, user_factory):
        organisation = OrganisationFactory.create()
        host = config.hosts.ADMIN_HOST
        url = reverse(
            "users:organisation-archive",
            kwargs={"pk": organisation.id},
            host=config.hosts.ADMIN_HOST,
        )

        client = client_factory(host=host)

        user = user_factory(account_type=AccountType.site_admin.value)
        client.force_login(user=user)

        response = client.get(url)

        assert response.status_code == 200
        assert "site_admin/organisation_archive.html" in [
            t.name for t in response.templates
        ]

    def test_form_deactivate_org_again(self, client_factory):
        organisation = OrganisationFactory.create(is_active=False)
        user1 = UserFactory.create(
            account_type=AccountType.org_staff.value,
            organisations=(organisation,),
            is_active=False,
        )
        agent_user = AgentUserFactory(is_active=False, organisations=(organisation,))
        host = config.hosts.ADMIN_HOST
        url = reverse(
            "users:organisation-archive",
            kwargs={"pk": organisation.id},
            host=config.hosts.ADMIN_HOST,
        )

        client = client_factory(host=host)
        user = UserFactory(account_type=AccountType.site_admin.value)
        client.force_login(user=user)

        assert not organisation.is_active
        assert not user1.is_active

        response = client.post(url, {})

        organisation.refresh_from_db()
        user1.refresh_from_db()
        agent_user.refresh_from_db()

        assert response.status_code == 302
        assert organisation.is_active
        assert user1.is_active
        assert not agent_user.is_active


class TestOrganisationServiceCodeExemptionView:
    host = config.hosts.ADMIN_HOST
    url_name = "users:service-code-exemptions-edit"
    test_organisation_name = "Test Organisation"
    test_organisation_short_name = "testO"
    prefix = "service_code_exemptions"
    default_form_data = {
        f"{prefix}-TOTAL_FORMS": "1",
        f"{prefix}-INITIAL_FORMS": "0",
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }

    def test_add_one_exemption(self, client_factory):
        org = OrganisationFactory(
            name=self.test_organisation_name,
            short_name=self.test_organisation_short_name,
            licences=1,
        )
        url = reverse(
            self.url_name,
            host=self.host,
            kwargs={"pk": org.id},
        )

        form_data = {
            f"{self.prefix}-0-id": "",
            f"{self.prefix}-0-licence": org.licences.first().id,
            f"{self.prefix}-0-registration_code": 88,
            f"{self.prefix}-0-justification": "because",
        }

        data = {**form_data, **self.default_form_data}

        admin = UserFactory(account_type=SiteAdminType)
        client = client_factory(host=self.host)
        client.force_login(user=admin)

        response = client.post(url, data)
        licence = org.licences.first()
        exemption = licence.service_code_exemptions.first()

        assert response.status_code == 302
        assert exemption.justification == "because"
        assert exemption.exempted_by == admin
        assert exemption.registration_code == 88

    def test_add_many_exemption_to_existing(self, client_factory):
        org = OrganisationFactory(
            name=self.test_organisation_name,
            short_name=self.test_organisation_short_name,
            licences=2,
        )

        for licence in org.licences.all():
            ServiceCodeExemptionFactory.create_batch(2, licence=licence)

        url = reverse(
            self.url_name,
            host=self.host,
            kwargs={"pk": org.id},
        )
        form_data = {
            f"{self.prefix}-TOTAL_FORMS": "6",
            f"{self.prefix}-INITIAL_FORMS": "4",
        }
        for index, exemption in enumerate(ServiceCodeExemption.objects.all()):
            prepend = f"{self.prefix}-{index}"
            form_data.update(
                {
                    f"{prepend}-id": exemption.id,
                    f"{prepend}-licence": exemption.licence.id,
                    f"{prepend}-registration_code": exemption.registration_code,
                    f"{prepend}-justification": exemption.justification,
                }
            )

        total = ServiceCodeExemption.objects.count()

        for index, licence in enumerate(org.licences.all()):
            prepend = f"{self.prefix}-{total + index}"
            form_data.update(
                {
                    f"{prepend}-id": "",
                    f"{prepend}-licence": licence.id,
                    f"{prepend}-registration_code": index + 1,
                    f"{prepend}-justification": f"reason: {licence.number}",
                }
            )

        data = {**self.default_form_data, **form_data}

        admin = UserFactory(account_type=SiteAdminType)
        client = client_factory(host=self.host)
        client.force_login(user=admin)

        response = client.post(url, data)
        assert response.status_code == 302
        assert ServiceCodeExemption.objects.count() == 6

    def test_modify_one_exemption(self, client_factory):
        org = OrganisationFactory(
            name=self.test_organisation_name,
            short_name=self.test_organisation_short_name,
            licences=1,
        )
        exemption = ServiceCodeExemptionFactory(
            licence=org.licences.first(),
            registration_code=1,
            justification="first",
        )

        url = reverse(
            self.url_name,
            host=self.host,
            kwargs={"pk": org.id},
        )

        form_data = {
            f"{self.prefix}-TOTAL_FORMS": "1",
            f"{self.prefix}-INITIAL_FORMS": "1",
            f"{self.prefix}-0-id": exemption.id,
            f"{self.prefix}-0-licence": exemption.licence.id,
            f"{self.prefix}-0-registration_code": 88,
            f"{self.prefix}-0-justification": "changed",
        }

        data = {**self.default_form_data, **form_data}

        admin = UserFactory(account_type=SiteAdminType)
        client = client_factory(host=self.host)
        client.force_login(user=admin)

        response = client.post(url, data)
        licence = org.licences.first()
        exemption = licence.service_code_exemptions.first()

        assert response.status_code == 302
        assert exemption.justification == "changed"
        assert exemption.exempted_by == admin
        assert exemption.registration_code == 88

    def test_delete_one_from_many(self, client_factory):
        org = OrganisationFactory(
            name=self.test_organisation_name,
            short_name=self.test_organisation_short_name,
            licences=2,
        )

        for licence in org.licences.all():
            ServiceCodeExemptionFactory.create_batch(2, licence=licence)

        url = reverse(
            self.url_name,
            host=self.host,
            kwargs={"pk": org.id},
        )
        form_data = {
            f"{self.prefix}-TOTAL_FORMS": "4",
            f"{self.prefix}-INITIAL_FORMS": "4",
        }
        for index, exemption in enumerate(ServiceCodeExemption.objects.all()):
            prepend = f"{self.prefix}-{index}"
            form_data.update(
                {
                    f"{prepend}-id": exemption.id,
                    f"{prepend}-licence": exemption.licence.id,
                    f"{prepend}-registration_code": exemption.registration_code,
                    f"{prepend}-justification": exemption.justification,
                }
            )

        deletion_candidate = form_data[f"{self.prefix}-0-id"]
        form_data[f"{self.prefix}-0-DELETE"] = "on"

        data = {**self.default_form_data, **form_data}

        admin = UserFactory(account_type=SiteAdminType)
        client = client_factory(host=self.host)
        client.force_login(user=admin)

        assert ServiceCodeExemption.objects.filter(id=deletion_candidate).exists()
        response = client.post(url, data)
        assert response.status_code == 302
        assert not ServiceCodeExemption.objects.filter(id=deletion_candidate).exists()

    def test_clash_service_codes(self, client_factory):
        total_clashing_service_codes = 3
        org = OrganisationFactory(
            name=self.test_organisation_name,
            short_name=self.test_organisation_short_name,
            licences=1,
        )
        url = reverse(
            self.url_name,
            host=self.host,
            kwargs={"pk": org.id},
        )

        form_data = {
            f"{self.prefix}-TOTAL_FORMS": "3",
            f"{self.prefix}-INITIAL_FORMS": "0",
        }
        for index in range(total_clashing_service_codes):
            form_data.update(
                {
                    f"{self.prefix}-{index}-id": "",
                    f"{self.prefix}-{index}-licence": org.licences.first().id,
                    f"{self.prefix}-{index}-registration_code": 88,
                    f"{self.prefix}-{index}-justification": "changed",
                }
            )

        data = {**self.default_form_data, **form_data}

        admin = UserFactory(account_type=SiteAdminType)
        client = client_factory(host=self.host)
        client.force_login(user=admin)

        response = client.post(url, data)

        assert response.status_code == 200
        errors = response.context_data["form"].errors
        assert len(errors)
        counter = 0
        for error in errors:
            # we want to make sure we have the same number of errors as we do
            # clashing service codes
            if error["registration_code"][0] == DUPLICATE_SERVICE_CODE:
                counter += 1
        assert counter == total_clashing_service_codes


class TestOrganisationUsersManageView:
    def test_view_permission_mixin(self):
        """Tests the view subclasses SiteAdminViewMixin.

        The mixin has been tested in users/tests/test_view_mixins.py so we don't
        need to test the permissions again"""
        assert issubclass(OrganisationUsersManageView, SiteAdminViewMixin)

    def test_correct_template_used(self, client_factory, user_factory):
        user = user_factory(account_type=AccountType.site_admin.value)

        invitation = InvitationFactory.create(
            id=randint(50, 100), account_type=AccountType.org_admin.value, inviter=user
        )
        invitation.organisation.is_active = True
        invitation.organisation.save()
        admin_count = 2
        UserFactory.create_batch(
            admin_count,
            organisations=(invitation.organisation,),
            account_type=AccountType.org_admin.value,
        )
        staff_count = 3
        UserFactory.create_batch(
            staff_count,
            organisations=(invitation.organisation,),
            account_type=AccountType.org_staff.value,
        )
        agent_count = 2
        AgentUserInviteFactory.create_batch(
            agent_count, organisation=invitation.organisation
        )

        host = config.hosts.ADMIN_HOST
        url = reverse(
            "users:org-user-manage",
            kwargs={"pk": invitation.organisation.id},
            host=config.hosts.ADMIN_HOST,
        )

        client = client_factory(host=host)
        client.force_login(user=user)

        response = client.get(url)

        assert response.status_code == 200
        assert "site_admin/organisation_user_manage.html" in [
            t.name for t in response.templates
        ]
        assert len(response.context["users"]) == admin_count + staff_count
        assert len(response.context["pending_standard_invites"]) == 1
        assert len(response.context["pending_agent_invites"]) == agent_count

        reinvite_link = reverse(
            "users:manage-user-re-invite",
            kwargs={"pk": invitation.organisation.id, "pk1": invitation.id},
            host=config.hosts.ADMIN_HOST,
        )
        assert reinvite_link in response.content.decode("utf-8")
