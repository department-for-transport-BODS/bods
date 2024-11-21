import urllib.parse
import pytest
from django.conf import settings
from django.urls import set_urlconf
from django_hosts.resolvers import get_host, reverse, reverse_host
import requests_mock
import urllib

import config.hosts
from transit_odp.organisation.constants import AVLType
from transit_odp.organisation.factories import DatasetFactory, DatasetRevisionFactory
from transit_odp.users.constants import OrgAdminType


def setup_datasets(client, user_factory, is_published=False):
    """
    Set up method to create datasets
    returns a configured client and the dataset
    """
    host = get_host(config.hosts.PUBLISH_HOST)
    HTTP_HOST = reverse_host(config.hosts.PUBLISH_HOST)
    settings.DEFAULT_HOST = config.hosts.PUBLISH_HOST
    set_urlconf(host.urlconf)
    client.defaults.setdefault("HTTP_HOST", HTTP_HOST)
    user = user_factory(account_type=OrgAdminType)

    # Login into browser session
    client.force_login(user)
    dataset = DatasetFactory.create(
        organisation=user.organisation,
        live_revision=None,
        dataset_type=AVLType,
        contact=user,
    )
    DatasetRevisionFactory.create(is_published=is_published, dataset=dataset)
    return client, dataset


@pytest.fixture
def unpublished_update_url(user_factory, publish_client):
    """
    Reimplimented unittest2 setup function in pytest for
    avl upload/update wizard view tests
    returns URL to post data to.
    """
    client, dataset = setup_datasets(publish_client, user_factory)

    return (
        reverse(
            "avl:feed-update",
            kwargs={"pk1": dataset.organisation_id, "pk": dataset.id},
            host=config.hosts.PUBLISH_HOST,
        ),
        publish_client,
        dataset,
    )


@pytest.fixture
def published_archive_url(user_factory, publish_client):
    client, dataset = setup_datasets(publish_client, user_factory, is_published=True)

    return (
        reverse(
            "avl:feed-archive",
            kwargs={"pk1": dataset.organisation_id, "pk": dataset.id},
            host=config.hosts.PUBLISH_HOST,
        ),
        publish_client,
    )


@pytest.fixture
def abods_avl_line_level_url():
    with requests_mock.Mocker() as mock:
        data = {
            "data": {
                "avlLineLevelStatus": [
                    {
                        "lineName": 43,
                        "lastRecordedAtTime": "2024-11-04T16:40:40.000Z",
                        "operatorNoc": "SDCU",
                    },
                    {
                        "lineName": 42,
                        "lastRecordedAtTime": "2024-11-04T16:40:40.000Z",
                        "operatorNoc": "SDCU",
                    },
                    {
                        "lineName": 41,
                        "lastRecordedAtTime": "2024-11-04T16:40:40.000Z",
                        "operatorNoc": "SDCU",
                    },
                    {
                        "lineName": 41,
                        "lastRecordedAtTime": "2024-11-04T16:40:40.000Z",
                        "operatorNoc": "SDCU",
                    },
                ]
            }
        }

        print("Conftest called")
        print(settings.ABODS_AVL_LINE_LEVEL_DETAILS_URL)
        query = "?query=query+ExampleQuery+%7B+avlLineLevelStatus+%7B+operatorNoc+lineName+lastRecordedAtTime+%7D+%7D "

        print("final url")
        print(f"{settings.ABODS_AVL_LINE_LEVEL_DETAILS_URL}{query}")
        mock.post(
            f"{settings.ABODS_AVL_LINE_LEVEL_DETAILS_URL}{query}",
            json=data,
        )
    yield mock
