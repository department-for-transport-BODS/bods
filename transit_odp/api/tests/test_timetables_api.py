from datetime import datetime

import pytest
from django_hosts import reverse

from config.hosts import DATA_HOST
from transit_odp.data_quality.factories import DataQualityReportFactory
from transit_odp.data_quality.factories.report import PTIObservationFactory
from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.users.constants import DeveloperType

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "score,percent,rag",
    (
        (0.91, "91.0%", "amber"),
        (1, "100.0%", "green"),
        (0.33, "33.0%", "red"),
        (0.90005, "90.0%", "red"),
        (0.9999, "99.9%", "amber"),
        (0.005, "0.5%", "red"),
    ),
)
def test_dq_rag(client_factory, user_factory, score, percent, rag):
    developer = user_factory(account_type=DeveloperType)
    url = reverse("api:feed-list", host=DATA_HOST)
    client = client_factory(host=DATA_HOST)
    client.force_login(user=developer)

    DataQualityReportFactory(score=score)
    params = {"dqRag": rag}
    response = client.get(url, params)
    api_dataset = response.data["results"][0]
    assert response.data["count"] == 1
    assert api_dataset["dqRag"] == rag
    assert api_dataset["dqScore"] == percent


def test_unavailable_dq_rag(client_factory, user_factory):
    developer = user_factory(account_type=DeveloperType)
    url = reverse("api:feed-list", host=DATA_HOST)
    client = client_factory(host=DATA_HOST)
    client.force_login(user=developer)

    DataQualityReportFactory(score=0)
    response = client.get(url)
    api_dataset = response.data["results"][0]
    assert response.data["count"] == 1
    assert api_dataset["dqRag"] == "unavailable"
    assert api_dataset["dqScore"] == "0.0%"


def test_dq_rag_with_active_filtering(client_factory, user_factory):
    developer = user_factory(account_type=DeveloperType)
    url = reverse("api:feed-list", host=DATA_HOST)
    client = client_factory(host=DATA_HOST)
    client.force_login(user=developer)

    DataQualityReportFactory(score=0.0)
    DataQualityReportFactory(score=0.33)
    DataQualityReportFactory(score=0.91)
    DataQualityReportFactory(score=1)
    response = client.get(url)
    assert response.data["count"] == 4

    response = client.get(url, {"dqRag": "red"})
    assert response.data["count"] == 1

    response = client.get(url, {"dqRag": "amber"})
    assert response.data["count"] == 1

    response = client.get(url, {"dqRag": "green"})
    assert response.data["count"] == 1


@pytest.mark.parametrize("pti_compliant,count", ((True, 1), (False, 2), ("", 5)))
def test_bods_compliant(client_factory, user_factory, pti_compliant, count):
    developer = user_factory(account_type=DeveloperType)
    url = reverse("api:feed-list", host=DATA_HOST)
    client = client_factory(host=DATA_HOST)
    client.force_login(user=developer)
    params = {}

    # dataset with live revision before pti, no observations
    DatasetRevisionFactory.create_batch(2, created=datetime(2000, 1, 1))

    # dataset with live revision after pti, no observations
    DatasetRevisionFactory.create_batch(1)

    # dataset with live revision after pti, with observations
    PTIObservationFactory.create_batch(2)

    params.update({"bodsCompliance": pti_compliant})

    response = client.get(url, params)

    assert response.data["count"] == count
    for dataset in response.data["results"]:
        if pti_compliant != "":
            assert dataset["bodsCompliance"] == pti_compliant
