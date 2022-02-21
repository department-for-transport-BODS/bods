import io
import zipfile

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django_hosts.resolvers import reverse, reverse_host

from config.hosts import ADMIN_HOST
from transit_odp.fares.factories import FaresMetadataFactory
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    LicenceFactory,
    TXCFileAttributesFactory,
)
from transit_odp.otc.factories import ServiceModelFactory
from transit_odp.site_admin.tasks import task_create_operational_exports_archive
from transit_odp.users.constants import OrgStaffType, SiteAdminType

pytestmark = pytest.mark.django_db
User = get_user_model()


class TestMetricsDownloadView:
    host = ADMIN_HOST

    def test_standard_user_cant_access(self, client_factory, user_factory):
        client = client_factory(host=self.host)
        user = user_factory(account_type=OrgStaffType)
        url = reverse("bods-metrics", host=self.host)
        client.force_login(user=user)
        response = client.get(url)
        assert response.status_code == 403

    def test_site_admin_can_access(self, client_factory, user_factory):
        client = client_factory(host=self.host)
        user = user_factory(account_type=SiteAdminType)
        url = reverse("bods-metrics", host=self.host)
        client.force_login(user=user)
        response = client.get(url)
        assert response.status_code == 200
        assert "site_admin/metrics/index.html" in response.template_name


class TestOperationalMetricsFileView:
    host = ADMIN_HOST

    def test_standard_user_cant_access(self, client_factory, user_factory):
        client = client_factory(host=self.host)
        user = user_factory(account_type=OrgStaffType)
        url = reverse("operational-metrics", host=self.host)
        client.force_login(user=user)
        response = client.get(url)
        assert response.status_code == 403

    def test_site_admin_can_download_zip(self, client_factory, user_factory):
        client = client_factory(host=self.host)
        user = user_factory(account_type=SiteAdminType)
        url = reverse("operational-metrics", host=self.host)
        client.force_login(user=user)
        service = ServiceModelFactory()
        TXCFileAttributesFactory(
            licence_number=service.licence.number,
            service_code=service.registration_number.replace("/", ":"),
        )
        AVLDatasetRevisionFactory()
        FaresMetadataFactory()
        LicenceFactory(number=service.licence.number)
        task_create_operational_exports_archive()

        expected_disposition = "attachment; filename=operationalexports.zip"
        expected_files = [
            "publishers.csv",
            "consumers.csv",
            "stats.csv",
            "agents.csv",
            "datasetpublishing.csv",
            "organisations_data_catalogue.csv",
            "timetables_data_catalogue.csv",
            "overall_data_catalogue.csv",
            "location_data_catalogue.csv",
        ]

        response = client.get(url)
        response_file = io.BytesIO(b"".join(response.streaming_content))
        assert response.status_code == 200
        assert response.get("Content-Disposition") == expected_disposition
        with zipfile.ZipFile(response_file, "r") as zout:
            files = [name for name in zout.namelist()]
        assert files == expected_files


class TestAPIMetricsFileView:
    host = ADMIN_HOST
    url = reverse("download-metrics", host=host)

    def get_page(self, user):
        hostname = reverse_host(self.host)
        client = Client(HTTP_HOST=hostname)
        client.force_login(user=user)
        response = client.get(self.url)
        return response

    def test_standard_user_cant_access(self, user_factory):
        user = user_factory(account_type=OrgStaffType)
        response = self.get_page(user)

        assert response.status_code == 403
