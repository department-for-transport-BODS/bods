from pathlib import Path

import pytest
from django.conf import settings
from django.urls import set_urlconf
from django_hosts.resolvers import get_host, reverse, reverse_host
from lxml import etree

import config.hosts
from transit_odp.fares.netex import NeTExDocument, NeTExElement, get_documents_from_zip
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.factories import DatasetFactory, DatasetRevisionFactory
from transit_odp.users.constants import AccountType

FIXTURES = Path(__file__).parent.joinpath("fixtures")

TEST_NETEX = """<PublicationDelivery version="1.1" xsi:schemaLocation="http://www.netex.org.uk/netex http://netex.uk/netex/schema/1.09c/xsd/NeTEx_publication.xsd" xmlns="http://www.netex.org.uk/netex" xmlns:siri="http://www.siri.org.uk/siri" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <PublicationTimestamp>2119-06-22T13:51:43.044Z</PublicationTimestamp>
    <ParticipantRef>SYS001</ParticipantRef>
    <PublicationRequest version="1.0">
        <RequestTimestamp>2119-06-22T13:51:43.044Z</RequestTimestamp>
        <ParticipantRef>SYS002</ParticipantRef>
        <Description>Request for HCTY Line_16.</Description>
    </PublicationRequest>
</PublicationDelivery>"""  # noqa


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
    user = user_factory(account_type=AccountType.org_admin.value)

    # Login into browser session
    client.force_login(user)
    dataset = DatasetFactory.create(
        organisation=user.organisation,
        live_revision=None,
        dataset_type=DatasetType.FARES.value,
        contact=user,
    )
    DatasetRevisionFactory.create(is_published=is_published, dataset=dataset)
    return client, dataset


@pytest.fixture
def netexdocument():
    netex_filepath = str(FIXTURES.joinpath("sample1.xml"))
    return NeTExDocument(netex_filepath)


@pytest.fixture
def netexelement():
    element = NeTExElement(etree.fromstring(TEST_NETEX))
    return element


@pytest.fixture
def netexdocuments():
    zip_filepath = str(FIXTURES.joinpath("sample.zip"))
    return get_documents_from_zip(zip_filepath)


@pytest.fixture
def unpublished_update_url(user_factory, publish_client):
    """
    Reimplimented unittest2 setup function in pytest for
    fares upload/update wizard view tests
    returns URL to post data to.
    """
    client, dataset = setup_datasets(publish_client, user_factory)

    return (
        reverse(
            "fares:feed-update",
            kwargs={"pk1": dataset.organisation_id, "pk": dataset.id},
            host=config.hosts.PUBLISH_HOST,
        ),
        publish_client,
    )


@pytest.fixture
def published_archive_url(user_factory, publish_client):
    client, dataset = setup_datasets(publish_client, user_factory, is_published=True)

    return (
        reverse(
            "fares:feed-archive",
            kwargs={"pk1": dataset.organisation_id, "pk": dataset.id},
            host=config.hosts.PUBLISH_HOST,
        ),
        publish_client,
    )
