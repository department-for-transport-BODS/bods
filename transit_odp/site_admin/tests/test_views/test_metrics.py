import io
import zipfile

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django_hosts.resolvers import reverse, reverse_host

from config.hosts import ADMIN_HOST
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
        assert "site_admin/metrics/download.html" in response.template_name


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

        expected_disposition = "attachment; filename=operationalexports.zip"
        expected_files = [
            "organisations.csv",
            "publishers.csv",
            "consumers.csv",
            "stats.csv",
            "agents.csv",
        ]

        response = client.get(url)
        response_file = io.BytesIO(b"".join(response.streaming_content))
        assert response.status_code == 200
        assert response.get("Content-Disposition") == expected_disposition
        with zipfile.ZipFile(response_file, "r") as zout:
            files = [name for name in zout.namelist()]
        assert expected_files == files


class TestAPIMetricsFileView:
    host = ADMIN_HOST
    url = reverse("api-metrics", host=host)

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

    def test_site_admin_can_download_zip(self, user_factory):
        user = user_factory(account_type=SiteAdminType)
        response = self.get_page(user)

        expected_disposition = "attachment; filename=apimetrics.zip"
        expected_files = [
            "dailyaggregates.csv",
            "dailyconsumerbreakdown.csv",
            "rawapimetrics.csv",
        ]
        response_file = io.BytesIO(b"".join(response.streaming_content))

        assert response.status_code == 200
        assert response.get("Content-Disposition") == expected_disposition
        with zipfile.ZipFile(response_file, "r") as zout:
            files = [name for name in zout.namelist()]
        assert expected_files == files
