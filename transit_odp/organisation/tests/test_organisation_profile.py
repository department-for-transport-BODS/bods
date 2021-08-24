import pytest
from django_hosts import reverse

from config.hosts import PUBLISH_HOST
from transit_odp.organisation.factories import LicenceFactory, OrganisationFactory
from transit_odp.organisation.models import Organisation
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestOrganisationProfile:
    # Note: a 302 redirect indicates a success while a 200 is redisplaying the
    # same page with errors
    default_management_form_data = {
        "short_name": "test",
        "nocs-TOTAL_FORMS": ["1"],
        "nocs-INITIAL_FORMS": ["1"],
        "nocs-MIN_NUM_FORMS": ["1"],
        "nocs-MAX_NUM_FORMS": ["1000"],
        "nocs-0-id": [""],
        "nocs-0-noc": ["bc"],
        "nocs-0-DELETE": [""],
        "nocs-__prefix__-id": [""],
        "nocs-__prefix__-noc": [""],
        "nocs-__prefix__-DELETE": [""],
        "licences-TOTAL_FORMS": ["0"],
        "licences-INITIAL_FORMS": ["0"],
        "licences-MIN_NUM_FORMS": ["0"],
        "licences-MAX_NUM_FORMS": ["1000"],
        "licences-__prefix__- id": "",
        "licences - __prefix__-number": "",
        "licences - __prefix__-DELETE": "",
    }

    def setup(self):
        self.host = PUBLISH_HOST
        self.org = OrganisationFactory(name="TestOrganisation", short_name="test")
        noc = self.org.nocs.first()
        # This is annoying, we need to specify at least one noc
        self.default_management_form_data["nocs-0-id"] = str(noc.id)
        self.default_management_form_data["nocs-0-noc"] = noc.noc
        self.user = UserFactory(
            account_type=AccountType.org_admin.value, organisations=(self.org,)
        )
        self.org.key_contact = self.user
        self.org.save()

        self.url = reverse(
            "users:edit-org-profile",
            host=self.host,
            kwargs={"pk": self.org.id},
        )

    def test_can_add_one_licence(self, client_factory):
        client = client_factory(host=self.host)
        client.force_login(user=self.user)
        data = self.default_management_form_data.copy()
        data.update(
            {
                "licences-0-id": "",
                "licences-0-number": "fg4578452",
                "licences-0-DELETE": "",
                "licences-TOTAL_FORMS": ["1"],
            }
        )

        response = client.post(self.url, data=data)

        modified_org = Organisation.objects.get(id=self.org.id)

        assert response.status_code == 302
        assert modified_org.licences.first().number == "fg4578452"

    def test_can_turn_off_licences(self, client_factory):
        client = client_factory(host=self.host)
        client.force_login(user=self.user)
        data = self.default_management_form_data.copy()
        data.update(
            {
                "licence_required": "on"
                # this is the i do not need a licence button
            }
        )

        response = client.post(self.url, data=data)

        modified_org = Organisation.objects.get(id=self.org.id)

        assert response.status_code == 302
        assert modified_org.licence_required is False

    def test_backend_wont_allow_both_checkbox_and_licence(self, client_factory):
        client = client_factory(host=self.host)
        client.force_login(user=self.user)
        data = self.default_management_form_data.copy()
        data.update(
            {
                "licence_required": "on",
                # this is the i do not need a licence button
                "licences-0-id": "",
                "licences-0-number": "fg4578452",
                "licences-0-DELETE": "",
                "licences-TOTAL_FORMS": ["1"],
            }
        )

        response = client.post(self.url, data=data)

        assert response.status_code == 200
        assert (
            response.context_data["form"].errors["licence_required"][0]
            == 'Untick "I do not have a PSV licence number" checkbox to add licences'
        )

    def test_delete_and_check_box(self, client_factory):
        client = client_factory(host=self.host)
        client.force_login(user=self.user)
        licences = LicenceFactory.create_batch(3, organisation=self.org)
        data = self.default_management_form_data.copy()
        data.update(
            {
                "licence_required": "on",
                # this is the i do not need a licence button
                "licences-TOTAL_FORMS": "3",
                "licences-INITIAL_FORMS": "3",
            }
        )

        for index, licence in enumerate(licences):
            data[f"licences-{index}-id"] = str(licence.id)
            data[f"licences-{index}-DELETE"] = "on"

        response = client.post(self.url, data=data)

        modified_org = Organisation.objects.get(id=self.org.id)

        assert response.status_code == 302
        assert modified_org.licence_required is False
        assert modified_org.licences.count() == 0

    def test_uncheck_and_add_licences(self, client_factory):
        client = client_factory(host=self.host)
        client.force_login(user=self.user)
        self.org.licence_required = False
        self.org.save()
        data = self.default_management_form_data.copy()
        data.update(
            {
                "licences-TOTAL_FORMS": "3",
            }
        )

        new_licences = [f"jb000000{num}" for num in range(3)]
        for index, licence in enumerate(new_licences):
            data[f"licences-{index}-number"] = licence
            data[f"licences-{index}-id"] = ""
            data[f"licences-{index}-DELETE"] = ""

        response = client.post(self.url, data=data)

        modified_org = Organisation.objects.get(id=self.org.id)

        assert response.status_code == 302
        assert modified_org.licence_required is True
        assert modified_org.licences.count() == 3

    def test_fail_validation_on_one_licence(self, client_factory):
        client = client_factory(host=self.host)
        client.force_login(user=self.user)
        data = self.default_management_form_data.copy()
        data.update(
            {
                "licences-0-id": "",
                "licences-0-number": "bad",
                "licences-0-DELETE": "",
                "licences-TOTAL_FORMS": ["1"],
            }
        )

        response = client.post(self.url, data=data)
        expected_message = "Licence number entered with the wrong format"

        assert response.status_code == 200
        errors = response.context_data["form"].nested_psv.errors
        assert len(errors) == 1
        assert errors[0]["number"][0] == expected_message
