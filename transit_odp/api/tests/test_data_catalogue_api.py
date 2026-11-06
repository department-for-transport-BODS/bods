from unittest.mock import patch

import pytest

from config import hosts
from transit_odp.site_admin.constants import DataCatalogue
from transit_odp.site_admin.models import DocumentArchive

pytestmark = pytest.mark.django_db


def test_catalogue_api_returns_signed_download_url(client_factory):
    DocumentArchive.objects.create(
        category=DataCatalogue,
        archive="bodsdatacatalogue.zip",
    )
    client = client_factory(host=hosts.ROOT_HOST)
    signed_url = "https://cdn.example.test/data-catalogue/bodsdatacatalogue.zip"

    with patch(
        "transit_odp.browse.views.data_catalogue.generate_signed_url",
        return_value=signed_url,
    ) as generate_signed_url:
        response = client.get("/api/catalogue/")

    assert response.status_code == 200
    assert response.json() == {"url": signed_url}
    generate_signed_url.assert_called_once_with("data-catalogue/bodsdatacatalogue.zip")


def test_catalogue_api_returns_404_when_no_archive_exists(client_factory):
    client = client_factory(host=hosts.ROOT_HOST)

    response = client.get("/api/catalogue/")

    assert response.status_code == 404


def test_catalogue_api_returns_json_error_when_signing_fails(client_factory):
    DocumentArchive.objects.create(
        category=DataCatalogue,
        archive="bodsdatacatalogue.zip",
    )
    client = client_factory(host=hosts.ROOT_HOST)

    with patch(
        "transit_odp.browse.views.data_catalogue.generate_signed_url",
        side_effect=ValueError("Invalid CloudFront key"),
    ):
        response = client.get("/api/catalogue/")

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Unable to generate the data catalogue download URL."
    }
