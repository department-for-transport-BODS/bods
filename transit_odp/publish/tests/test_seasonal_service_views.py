import datetime

import pytest
import pytz
from django_hosts import reverse
from freezegun import freeze_time

from config.hosts import PUBLISH_HOST
from transit_odp.organisation.factories import LicenceFactory as BODSLicenceFactory
from transit_odp.organisation.factories import (
    OrganisationFactory,
    SeasonalServiceFactory,
)
from transit_odp.organisation.models import SeasonalService
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestSeasonalServiceView:
    NUMBER_SEASONAL_SERVICE_PER_ORGANISATION = 15

    def setup(self):
        self.user = UserFactory.create(account_type=AccountType.org_staff.value)
        self.org = self.user.organisation
        self.licence = BODSLicenceFactory(organisation=self.org)
        for i in range(self.NUMBER_SEASONAL_SERVICE_PER_ORGANISATION):
            SeasonalServiceFactory(licence=self.licence)
        self.url = reverse(
            "seasonal-service", host=PUBLISH_HOST, kwargs={"pk1": self.org.id}
        )

    def test_create_table_seasonal_service(self, publish_client):
        """
        GIVEN : a NUMBER_SEASONAL_SERVICE_PER_ORGANISATION number of
                seasonal services
        WHEN  : we open the `seasonal-service' link
        THEN  : the data should be appear in a table, with the columns:
               `Licence number'	`Service code' `Service begins'
               `Service ends' `Actions'
               and the number of rows has to be equal to
               NUMBER_SEASONAL_SERVICE_PER_ORGANISATION
        """
        publish_client.force_login(user=self.user)
        response = publish_client.get(self.url)

        assert response.status_code == 200
        assert response.context.get("table").paginator.num_pages == 2
        assert (
            response.context.get("table").data.model.objects.count()
            == self.NUMBER_SEASONAL_SERVICE_PER_ORGANISATION
        )

    def test_delete_first_seasonal_service(self, publish_client):
        """
        GIVEN : a NUMBER_SEASONAL_SERVICE_PER_ORGANISATION number of
                seasonal services
        WHEN  : we open the `seasonal-service' link
        THEN  : the data should be appear in a table, with the columns:
               `Licence number'	`Service code' `Service begins'
               `Service ends' `Actions'
               and the number of rows has to be equal to
               NUMBER_SEASONAL_SERVICE_PER_ORGANISATION
               then we delete the first seasonal service and the number
               of the rows has to be equal to
               NUMBER_SEASONAL_SERVICE_PER_ORGANISATION - 1
        """
        publish_client.force_login(user=self.user)
        response = publish_client.get(self.url)

        assert response.status_code == 200
        assert response.context.get("table").paginator.num_pages == 2
        assert (
            response.context.get("table").data.model.objects.count()
            == self.NUMBER_SEASONAL_SERVICE_PER_ORGANISATION
        )
        delete_url = reverse(
            "delete-seasonal-service",
            host=PUBLISH_HOST,
            kwargs={"pk1": self.org.id},
        )

        seasonal_services = SeasonalService.objects.first()
        delete_data = {"id": seasonal_services.id}
        publish_client.post(
            delete_url,
            data=delete_data,
        )
        assert (
            response.context.get("table").data.model.objects.count()
            == self.NUMBER_SEASONAL_SERVICE_PER_ORGANISATION - 1
        )

    def test_cant_delete_other_orgs_seasonal_service(self, publish_client):
        other_org = OrganisationFactory()
        publish_client.force_login(self.user)
        other_seasonal_service = SeasonalServiceFactory(licence__organisation=other_org)
        delete_url = reverse(
            "delete-seasonal-service",
            host=PUBLISH_HOST,
            kwargs={"pk1": self.org.id},
        )

        delete_data = {"id": other_seasonal_service.id}
        publish_client.post(
            delete_url,
            data=delete_data,
        )
        assert SeasonalService.objects.filter(id=other_seasonal_service.id).exists()

    def test_delete_last_seasonal_service(self, publish_client):
        """
        GIVEN : a NUMBER_SEASONAL_SERVICE_PER_ORGANISATION number of
                seasonal services
        WHEN  : we open the `seasonal-service' link
        THEN  : the data should be appear in a table, with the columns:
               `Licence number'	`Service code' `Service begins'
               `Service ends' `Actions'
               and the number of rows has to be equal to
               NUMBER_SEASONAL_SERVICE_PER_ORGANISATION
               then we delete the first seasonal service and the number
               of the rows has to be equal to
               NUMBER_SEASONAL_SERVICE_PER_ORGANISATION - 1
        """
        publish_client.force_login(user=self.user)
        response = publish_client.get(self.url + "?page=2")

        assert response.status_code == 200
        assert response.context.get("table").paginator.num_pages == 2
        assert (
            response.context.get("table").data.model.objects.count()
            == self.NUMBER_SEASONAL_SERVICE_PER_ORGANISATION
        )
        seasonal_services = SeasonalService.objects.last()
        delete_data = {"id": seasonal_services.id}
        delete_url = reverse(
            "delete-seasonal-service",
            host=PUBLISH_HOST,
            kwargs={"pk1": self.org.id},
        )
        publish_client.post(
            delete_url,
            data=delete_data,
        )
        assert (
            response.context.get("table").data.model.objects.count()
            == self.NUMBER_SEASONAL_SERVICE_PER_ORGANISATION - 1
        )

    def test_transition_page_when_delete_seasonal_service(self, publish_client):
        SEASONAL_SERVICE_UPGRADE = 6
        publish_client.force_login(user=self.user)
        for _ in range(SEASONAL_SERVICE_UPGRADE):
            SeasonalServiceFactory(licence=self.licence)
        # up to 3 pages
        response = publish_client.get(self.url + "?page=3")

        assert response.status_code == 200
        assert response.context.get("table").paginator.num_pages == 3
        assert (
            response.context.get("table").data.model.objects.count()
            == self.NUMBER_SEASONAL_SERVICE_PER_ORGANISATION + SEASONAL_SERVICE_UPGRADE
        )

        seasonal_services = SeasonalService.objects.last()
        delete_data = {"id": seasonal_services.id}
        delete_url = reverse(
            "delete-seasonal-service",
            host=PUBLISH_HOST,
            kwargs={"pk1": self.org.id},
        )
        response = publish_client.post(
            delete_url,
            data=delete_data,
            follow=True,
        )
        # redirect to list table
        assert response.status_code == 200
        assert len(response.context_data["table"].data) > 0
        # the 3rd page no longer exists!
        response = publish_client.get(
            self.url + "?page=3",
        )
        assert response.status_code == 404
        # the last page now is the second one
        response = publish_client.get(self.url + "?page=2")
        assert response.status_code == 200


class TestEditSeasonalServiceView:
    REGISTRATION_CODE = 15

    def setup(self):
        self.user = UserFactory.create(account_type=AccountType.org_staff.value)
        self.org = self.user.organisation
        self.licence = BODSLicenceFactory(organisation=self.org)
        self.seasonal_service = SeasonalServiceFactory(
            licence=self.licence,
            registration_code=self.REGISTRATION_CODE,
            start=datetime.datetime(2023, 1, 1, tzinfo=pytz.utc),
            end=datetime.datetime(2023, 2, 1, tzinfo=pytz.utc),
        )
        self.url = reverse(
            "edit-seasonal-service-date",
            host=PUBLISH_HOST,
            kwargs={"pk1": self.org.id, "pk": self.seasonal_service.id},
        )

    @freeze_time("2023-01-01")
    def test_edit_seasonal_service_date(self, publish_client):
        """
        GIVEN : a new seasonal services
        WHEN  : we'd like to modify the start and end dates, with a post form
        THEN  : the data in the db should be updated with the new dates
        """
        publish_client.force_login(user=self.user)
        form_data = {"start": "2023-01-10", "end": "2023-02-20"}
        publish_client.post(
            self.url,
            data=form_data,
        )
        seasonal_service = SeasonalService.objects.filter(
            licence=self.licence, registration_code=self.REGISTRATION_CODE
        ).first()

        assert seasonal_service.start == datetime.date(2023, 1, 10)
        assert seasonal_service.end == datetime.date(2023, 2, 20)

    def test_cant_edit_another_orgs_seasonal_service(self, publish_client):
        start = datetime.datetime(2023, 12, 25, tzinfo=pytz.utc)
        end = datetime.datetime(2023, 12, 26, tzinfo=pytz.utc)
        other_org = OrganisationFactory()
        licence = BODSLicenceFactory(organisation=other_org)
        seasonal_service = SeasonalServiceFactory(
            licence=licence,
            registration_code=101,
            start=start,
            end=end,
        )
        url = reverse(
            "edit-seasonal-service-date",
            host=PUBLISH_HOST,
            kwargs={"pk1": self.org.id, "pk": seasonal_service.id},
        )

        publish_client.force_login(user=self.user)
        form_data = {"start": "2023-01-10", "end": "2023-02-20"}
        response = publish_client.post(
            url,
            data=form_data,
        )
        seasonal_service.refresh_from_db()
        assert response.status_code == 404
        assert seasonal_service.start == start.date()
        assert seasonal_service.end == end.date()

    @freeze_time("2023-01-09")
    def test_edit_seasonal_service_errors_on_end_before_start(self, publish_client):
        """
        GIVEN : a new seasonal services
        WHEN  : we'd like to modify the start and end dates, with a post form
        THEN  : if the end date is earlier of the start date and error
                should be raise and no data will be updated
        """
        publish_client.force_login(user=self.user)
        form_data = {"start": "2023-02-10", "end": "2023-01-10"}
        response = publish_client.post(
            self.url,
            data=form_data,
        )
        assert (
            response.context_data["form"].errors["end"][0]
            == "Start date must be earlier than end date"
        )


class TestCreateSeasonalServiceView:
    wizard_name = "wizard_add_new_view"
    form1_name = "select_psv_licence_number"
    form2_name = "provide_operating_dates"
    REGISTRATION_CODE = 5

    def setup(self):
        self.user = UserFactory.create(account_type=AccountType.org_staff.value)
        self.org = self.user.organisation
        self.url = reverse(
            "add-seasonal-service", host=PUBLISH_HOST, kwargs={"pk1": self.org.id}
        )

    @freeze_time("2023-01-10")
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

    @freeze_time("2023-01-04")
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
            response.context_data["form"].errors["end"][0]
            == "Start date must be earlier than end date"
        )

    @freeze_time("2023-01-10")
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
