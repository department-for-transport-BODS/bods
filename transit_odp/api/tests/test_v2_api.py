import pytest
from django_hosts import reverse, reverse_host
from rest_framework.test import APIClient

from config.hosts import DATA_HOST
from transit_odp.organisation.constants import TimetableType
from transit_odp.organisation.factories import (
    DatasetFactory,
    OrganisationFactory,
    TXCFileAttributesFactory,
)
from transit_odp.users.constants import DeveloperType

pytestmark = pytest.mark.django_db


def test_no_filters(user_factory):
    host = reverse_host(DATA_HOST)
    user = user_factory(account_type=DeveloperType)
    client = APIClient()

    DatasetFactory.create_batch(3, dataset_type=TimetableType)
    dataset = DatasetFactory(dataset_type=TimetableType)
    TXCFileAttributesFactory.create_batch(3, revision=dataset.live_revision)

    url = reverse("api:v2:timetables-list", host=DATA_HOST)
    response = client.get(url, data={"api_key": user.auth_token.key}, HTTP_HOST=host)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 4
    [result] = [ds for ds in data["results"] if ds["id"] == dataset.id]

    assert result["name"] == dataset.live_revision.name
    assert len(result["files"]) == dataset.live_revision.txc_file_attributes.count()


def test_filter_noc(user_factory):
    host = reverse_host(DATA_HOST)
    user = user_factory(account_type=DeveloperType)
    client = APIClient()
    TXCFileAttributesFactory(national_operator_code="noc1")
    TXCFileAttributesFactory.create_batch(5)

    url = reverse("api:v2:timetables-list", host=DATA_HOST)
    response = client.get(
        url, data={"api_key": user.auth_token.key, "noc": "noc1"}, HTTP_HOST=host
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    result = data["results"][0]

    assert len(result["files"]) == 1
    assert result["files"][0]["national_operator_code"] == "noc1"


def test_filter_line_in_single_array(user_factory):
    host = reverse_host(DATA_HOST)
    user = user_factory(account_type=DeveloperType)
    client = APIClient()
    TXCFileAttributesFactory(line_names=["testline1"])
    TXCFileAttributesFactory.create_batch(5)

    url = reverse("api:v2:timetables-list", host=DATA_HOST)
    response = client.get(
        url,
        data={"api_key": user.auth_token.key, "line_name": "testline1"},
        HTTP_HOST=host,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    result = data["results"][0]

    assert len(result["files"]) == 1
    assert result["files"][0]["line_names"] == ["testline1"]


def test_filter_line_in_multiple_array(user_factory):
    host = reverse_host(DATA_HOST)
    user = user_factory(account_type=DeveloperType)
    client = APIClient()
    TXCFileAttributesFactory(line_names=["testline1", "testline2"])
    TXCFileAttributesFactory.create_batch(5)

    url = reverse("api:v2:timetables-list", host=DATA_HOST)
    response = client.get(
        url,
        data={"api_key": user.auth_token.key, "line_name": "testline1"},
        HTTP_HOST=host,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    result = data["results"][0]

    assert len(result["files"]) == 1
    assert result["files"][0]["line_names"] == ["testline1", "testline2"]


def test_filter_line_part_match_returns_empty(user_factory):
    host = reverse_host(DATA_HOST)
    user = user_factory(account_type=DeveloperType)
    client = APIClient()
    TXCFileAttributesFactory(line_names=["testline1", "testline2"])
    TXCFileAttributesFactory.create_batch(5)

    url = reverse("api:v2:timetables-list", host=DATA_HOST)
    response = client.get(
        url,
        data={"api_key": user.auth_token.key, "line_name": "testlin"},
        HTTP_HOST=host,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0


def test_noc_operators(user_factory):
    org = OrganisationFactory.create(nocs=["noc1"])
    host = reverse_host(DATA_HOST)
    user = user_factory(account_type=DeveloperType)
    client = APIClient()

    url = reverse("api:v2:operators-list", host=DATA_HOST)
    response = client.get(
        url,
        data={"api_key": user.auth_token.key, "noc": "noc1", "organisation": org},
        HTTP_HOST=host,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    result = data["results"]

    assert len(result) == 1
    assert result[0]["nocs"][0] == "noc1"
