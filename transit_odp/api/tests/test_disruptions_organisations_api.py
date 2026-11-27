import pytest
from django_hosts import reverse, reverse_host
from rest_framework import status
from rest_framework.test import APIClient

from config.hosts import DATA_HOST

pytestmark = pytest.mark.django_db


def test_disruptions_organisations_list(monkeypatch, settings):
    settings.DISRUPTIONS_API_BASE_URL = "https://disruptions.example/api"
    settings.DISRUPTIONS_API_KEY = "test-api-key"
    expected_data = [
        {
            "id": "org-id",
            "name": "Example operator",
            "stats": {
                "lastUpdated": "2026-10-12T11:07:29.000Z",
                "totalDisruptionsCount": 2,
            },
        }
    ]
    calls = []

    def get_organisations(url, headers):
        calls.append((url, headers))
        return expected_data, status.HTTP_200_OK

    monkeypatch.setattr(
        "transit_odp.api.app.views._get_disruptions_organisation_data",
        get_organisations,
    )
    client = APIClient()
    hostname = reverse_host(DATA_HOST)
    url = reverse("api:app:disruption_organisations-list", host=DATA_HOST)

    response = client.get(url, HTTP_HOST=hostname)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_data
    assert calls == [
        (
            "https://disruptions.example/api/organisations",
            {"x-api-key": "test-api-key"},
        )
    ]
