import json

import pytest

from config import hosts
from transit_odp.organisation.factories import (
    LicenceFactory,
    OperatorCodeFactory,
    OrganisationFactory,
    SeasonalServiceFactory,
    ServiceCodeExemptionFactory,
)
from transit_odp.organisation.models import Licence, OperatorCode
from transit_odp.organisation.models.data import ServiceCodeExemption
from transit_odp.users.factories import OrgAdminFactory

pytestmark = pytest.mark.django_db


def update_url(organisation_id: int) -> str:
    return f"/api/organisation/profile/{organisation_id}/update/"


def post(client, organisation_id: int, **body):
    return client.post(
        update_url(organisation_id),
        data=json.dumps(body),
        content_type="application/json",
    )


@pytest.fixture
def org_admin_client(client_factory):
    organisation = OrganisationFactory(licence_required=True)
    admin = OrgAdminFactory(organisations=(organisation,))
    client = client_factory(host=hosts.PUBLISH_HOST)
    client.force_login(user=admin)
    return client, organisation


def test_update_requires_authentication(client_factory):
    organisation = OrganisationFactory()
    client = client_factory(host=hosts.PUBLISH_HOST)

    response = post(client, organisation.id, shortName="Anything", nocs=["ABCD"])

    assert response.status_code == 401


def test_update_keeps_unchanged_licences_and_their_related_records(org_admin_client):
    """Regression test: re-saving the profile used to delete every licence and
    recreate it, cascading away exemptions and seasonal services."""
    client, organisation = org_admin_client
    kept = LicenceFactory(organisation=organisation, number="PD0000001")
    OperatorCodeFactory(organisation=organisation, noc="KEPT")
    exemption = ServiceCodeExemptionFactory(licence=kept)
    seasonal = SeasonalServiceFactory(licence=kept)

    response = post(
        client,
        organisation.id,
        shortName="Still here",
        licenceRequired=True,
        nocs=["KEPT", "ADDED"],
        licenceNumbers=["PD0000001", "PD0000002"],
    )

    assert response.status_code == 200
    kept.refresh_from_db()
    assert kept.pk is not None
    assert ServiceCodeExemption.objects.filter(pk=exemption.pk).exists()
    assert seasonal.licence_id == kept.pk
    assert set(organisation.nocs.values_list("noc", flat=True)) == {"KEPT", "ADDED"}
    assert set(organisation.licences.values_list("number", flat=True)) == {
        "PD0000001",
        "PD0000002",
    }


def test_update_removes_only_the_licences_the_user_dropped(org_admin_client):
    client, organisation = org_admin_client
    kept = LicenceFactory(organisation=organisation, number="PD0000001")
    dropped = LicenceFactory(organisation=organisation, number="PD0000002")
    OperatorCodeFactory(organisation=organisation, noc="KEPT")
    dropped_exemption = ServiceCodeExemptionFactory(licence=dropped)

    response = post(
        client,
        organisation.id,
        shortName="Fewer licences",
        licenceRequired=True,
        nocs=["KEPT"],
        licenceNumbers=["PD0000001"],
    )

    assert response.status_code == 200
    assert Licence.objects.filter(pk=kept.pk).exists()
    assert not Licence.objects.filter(pk=dropped.pk).exists()
    assert not ServiceCodeExemption.objects.filter(pk=dropped_exemption.pk).exists()


def test_update_removes_only_the_nocs_the_user_dropped(org_admin_client):
    client, organisation = org_admin_client
    kept = OperatorCodeFactory(organisation=organisation, noc="KEPT")
    dropped = OperatorCodeFactory(organisation=organisation, noc="DROPPED")

    response = post(
        client,
        organisation.id,
        shortName="Fewer NOCs",
        licenceRequired=True,
        nocs=["KEPT"],
        licenceNumbers=[],
    )

    assert response.status_code == 200
    assert OperatorCode.objects.filter(pk=kept.pk).exists()
    assert not OperatorCode.objects.filter(pk=dropped.pk).exists()


def test_update_deduplicates_repeated_values(org_admin_client):
    client, organisation = org_admin_client

    response = post(
        client,
        organisation.id,
        shortName="Duplicates",
        licenceRequired=True,
        nocs=["ABCD", "ABCD"],
        licenceNumbers=["PD0000001", "PD0000001"],
    )

    assert response.status_code == 200
    assert organisation.nocs.count() == 1
    assert organisation.licences.count() == 1


def test_update_requires_at_least_one_noc(org_admin_client):
    client, organisation = org_admin_client
    OperatorCodeFactory(organisation=organisation, noc="KEPT")
    nocs_before = set(organisation.nocs.values_list("noc", flat=True))

    response = post(
        client, organisation.id, shortName="No NOCs", licenceRequired=True, nocs=[]
    )

    assert response.status_code == 400
    assert "nocs" in response.json()["field_errors"]
    assert set(organisation.nocs.values_list("noc", flat=True)) == nocs_before


def test_update_rejects_licence_numbers_when_licence_not_required(org_admin_client):
    client, organisation = org_admin_client

    response = post(
        client,
        organisation.id,
        shortName="Contradiction",
        licenceRequired=False,
        nocs=["ABCD"],
        licenceNumbers=["PD0000001"],
    )

    assert response.status_code == 400
    assert "licenceRequired" in response.json()["field_errors"]


def test_update_rejects_malformed_licence_numbers(org_admin_client):
    client, organisation = org_admin_client

    response = post(
        client,
        organisation.id,
        shortName="Bad licence",
        licenceRequired=True,
        nocs=["ABCD"],
        licenceNumbers=["nope"],
    )

    assert response.status_code == 400
    assert "licenceNumbers" in response.json()["field_errors"]
