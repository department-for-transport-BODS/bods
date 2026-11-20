import factory
import pytest
from django_hosts.resolvers import reverse

from config.hosts import PUBLISH_HOST
from transit_odp.avl.factories import (
    AVLValidationReportFactory,
    PostPublishingCheckReportFactory,
)
from transit_odp.avl.models import PPCReportType
from transit_odp.organisation.constants import AVLType
from transit_odp.organisation.factories import DatasetFactory, OrganisationFactory
from transit_odp.users.factories import OrgStaffFactory

pytestmark = pytest.mark.django_db

ORG_DOWNLOADS = ["service-codes", "compliance-report", "ppc-archive"]
DATASET_DOWNLOADS = ["avl:download-matching-report", "avl:validation-report-download"]
MISSING_ID = 999999999


@pytest.fixture
def avl_dataset():
    organisation = OrganisationFactory()
    dataset = DatasetFactory(organisation=organisation, dataset_type=AVLType)
    PostPublishingCheckReportFactory(
        dataset=dataset,
        granularity=PPCReportType.WEEKLY,
        vehicle_activities_analysed=10,
        vehicle_activities_completely_matching=5,
        file=factory.django.FileField(filename="ppc_weekly.zip"),
    )
    AVLValidationReportFactory(revision=dataset.live_revision)
    return dataset


def _download_url(name, dataset):
    if name in DATASET_DOWNLOADS:
        args = (dataset.organisation_id, dataset.id)
    else:
        args = (dataset.organisation_id,)
    return reverse(name, args=args, host=PUBLISH_HOST)


@pytest.mark.parametrize("user_type", ["anonymous", "other_org", "member"])
@pytest.mark.parametrize("name", ORG_DOWNLOADS + DATASET_DOWNLOADS)
def test_downloads_stay_public(client_factory, avl_dataset, name, user_type):
    """The data-host operator profile, AVL dataset page and data catalogue link
    consumers straight to these downloads, so they must not require org access.
    """
    client = client_factory(host=PUBLISH_HOST)
    if user_type != "anonymous":
        org = (
            avl_dataset.organisation if user_type == "member" else OrganisationFactory()
        )
        client.force_login(user=OrgStaffFactory(organisations=(org,)))

    response = client.get(_download_url(name, avl_dataset))

    assert response.status_code == 200
    assert response["Content-Disposition"].startswith("attachment; filename=")


@pytest.mark.parametrize("name", ORG_DOWNLOADS)
def test_org_downloads_404_for_missing_organisation(client_factory, name):
    client = client_factory(host=PUBLISH_HOST)
    response = client.get(reverse(name, args=(MISSING_ID,), host=PUBLISH_HOST))
    assert response.status_code == 404


@pytest.mark.parametrize("name", DATASET_DOWNLOADS)
def test_dataset_downloads_404_for_dataset_in_another_org(
    client_factory, avl_dataset, name
):
    client = client_factory(host=PUBLISH_HOST)
    other_org = OrganisationFactory()
    url = reverse(name, args=(other_org.id, avl_dataset.id), host=PUBLISH_HOST)
    assert client.get(url).status_code == 404


def test_matching_report_404_when_no_report(client_factory):
    dataset = DatasetFactory(dataset_type=AVLType)
    client = client_factory(host=PUBLISH_HOST)
    response = client.get(_download_url("avl:download-matching-report", dataset))
    assert response.status_code == 404


def test_validation_report_404_when_no_reports(client_factory):
    dataset = DatasetFactory(dataset_type=AVLType)
    client = client_factory(host=PUBLISH_HOST)
    response = client.get(_download_url("avl:validation-report-download", dataset))
    assert response.status_code == 404


def test_validation_report_404_when_reports_have_no_issues(client_factory):
    dataset = DatasetFactory(dataset_type=AVLType)
    AVLValidationReportFactory(
        revision=dataset.live_revision, critical_count=0, non_critical_count=0
    )
    client = client_factory(host=PUBLISH_HOST)
    response = client.get(_download_url("avl:validation-report-download", dataset))
    assert response.status_code == 404
