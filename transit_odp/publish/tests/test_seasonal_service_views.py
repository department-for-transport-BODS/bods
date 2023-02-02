import pytest
from django_hosts import reverse

from config.hosts import PUBLISH_HOST
from transit_odp.organisation.factories import LicenceFactory as BODSLicenceFactory
from transit_odp.organisation.factories import SeasonalServiceFactory
from transit_odp.organisation.models import SeasonalService
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestCreateSeasonalServiceView:
    wizard_name = "seasonal_service_wizard_add_new_view"
    form1_name = "select_psv_licence_number"
    form2_name = "provide_operating_dates"
    REGISTRATION_CODE = 5

    def setup(self):
        self.user = UserFactory.create(account_type=AccountType.org_staff.value)
        self.org = self.user.organisation
        self.url = reverse(
            "add-seasonal-service", host=PUBLISH_HOST, kwargs={"pk1": self.org.id}
        )

    def test_can_add_seasonal_service(self, publish_client):
        licence = BODSLicenceFactory(organisation=self.org)
        publish_client.force_login(user=self.user)
        step1_data = {
            f"{self.wizard_name}-current_step": "select_psv_licence_number",
            f"{self.form1_name}-licence": licence.id,
            "submit": "submit",
        }
        step2_data = {
            f"{self.wizard_name}-current_step": "provide_operating_dates",
            f"{self.form2_name}-registration_code": self.REGISTRATION_CODE,
            f"{self.form2_name}-start": "2023-01-05",
            f"{self.form2_name}-end": "2023-01-15",
            "submit": "submit",
        }
        publish_client.post(
            self.url,
            data=step1_data,
        )
        publish_client.post(self.url, data=step2_data)

        assert SeasonalService.objects.filter(
            licence=licence, registration_code=self.REGISTRATION_CODE
        ).exists()

    def test_licence_object_is_in_form(self, publish_client):
        licence = BODSLicenceFactory(organisation=self.org)
        publish_client.force_login(user=self.user)
        step1_data = {
            f"{self.wizard_name}-current_step": "select_psv_licence_number",
            f"{self.form1_name}-licence": licence.id,
            "submit": "submit",
        }

        response = publish_client.post(
            self.url,
            data=step1_data,
        )
        # Its important that the licence is added to the form so that
        # the seasonal service can be added to it and the number is also
        # displayed in the frontend.
        assert response.context_data["form"].licence == licence

    def test_seasonal_service_errors_on_duplicate(self, publish_client):
        licence = BODSLicenceFactory(organisation=self.org)
        SeasonalServiceFactory(
            licence=licence, registration_code=self.REGISTRATION_CODE
        )
        publish_client.force_login(user=self.user)
        step1_data = {
            f"{self.wizard_name}-current_step": "select_psv_licence_number",
            f"{self.form1_name}-licence": licence.id,
            "submit": "submit",
        }
        step2_data = {
            f"{self.wizard_name}-current_step": "provide_operating_dates",
            f"{self.form2_name}-registration_code": self.REGISTRATION_CODE,
            f"{self.form2_name}-start": "2023-01-05",
            f"{self.form2_name}-end": "2023-01-15",
            "submit": "submit",
        }
        publish_client.post(
            self.url,
            data=step1_data,
        )
        response = publish_client.post(self.url, data=step2_data)

        assert (
            response.context_data["form"].errors["registration_code"][0]
            == "This service code has already been set up with a date range"
        )

    def test_seasonal_service_errors_on_end_before_start(self, publish_client):
        licence = BODSLicenceFactory(organisation=self.org)
        publish_client.force_login(user=self.user)
        step1_data = {
            f"{self.wizard_name}-current_step": "select_psv_licence_number",
            f"{self.form1_name}-licence": licence.id,
            "submit": "submit",
        }
        step2_data = {
            f"{self.wizard_name}-current_step": "provide_operating_dates",
            f"{self.form2_name}-registration_code": self.REGISTRATION_CODE,
            f"{self.form2_name}-start": "2023-01-15",
            f"{self.form2_name}-end": "2023-01-5",
            "submit": "submit",
        }
        publish_client.post(
            self.url,
            data=step1_data,
        )
        response = publish_client.post(self.url, data=step2_data)

        assert (
            response.context_data["form"].errors["__all__"][0]
            == "Start date must be earlier than end date"
        )

    @pytest.mark.parametrize(
        "start,end", [("", "2023-01-15"), ("2023-01-05", ""), ("", "")]
    )
    def test_seasonal_service_errors_on_empty_dates(self, publish_client, start, end):
        licence = BODSLicenceFactory(organisation=self.org)
        publish_client.force_login(user=self.user)
        step1_data = {
            f"{self.wizard_name}-current_step": "select_psv_licence_number",
            f"{self.form1_name}-licence": licence.id,
            "submit": "submit",
        }
        step2_data = {
            f"{self.wizard_name}-current_step": "provide_operating_dates",
            f"{self.form2_name}-registration_code": self.REGISTRATION_CODE,
            f"{self.form2_name}-start": start,
            f"{self.form2_name}-end": end,
            "submit": "submit",
        }
        publish_client.post(
            self.url,
            data=step1_data,
        )
        response = publish_client.post(self.url, data=step2_data)

        errors = response.context_data["form"].errors
        for error in errors.values():
            assert error[0] == "This date is required"
