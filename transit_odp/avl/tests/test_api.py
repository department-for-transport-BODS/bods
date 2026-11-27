import datetime
from unittest.mock import patch

import pytest
import pytz
from django_hosts import reverse

from config.hosts import PUBLISH_HOST
from transit_odp.avl.factories import CAVLValidationTaskResultFactory
from transit_odp.avl.models import CAVLValidationTaskResult
from transit_odp.organisation.factories import AVLDatasetRevisionFactory
from transit_odp.users.constants import OrgAdminType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


def get_feed_detail(client_factory, avl_feed_last_checked):
    user = UserFactory(account_type=OrgAdminType)
    revision = AVLDatasetRevisionFactory(
        dataset__organisation=user.organisations.first(),
    )
    dataset = revision.dataset
    dataset.avl_feed_last_checked = avl_feed_last_checked
    dataset.save()
    client = client_factory(host=PUBLISH_HOST)
    client.force_login(user)
    url = reverse(
        "nextjs-avl-detail",
        host=PUBLISH_HOST,
        kwargs={"pk1": dataset.organisation_id, "pk": dataset.id},
    )
    response = client.get(url)
    assert response.status_code == 200
    return response.json()


def test_feed_detail_last_server_update_blank_when_never_checked(client_factory):
    detail = get_feed_detail(client_factory, avl_feed_last_checked=None)
    assert detail["lastServerUpdate"] == ""


def test_feed_detail_last_server_update_uses_last_checked(client_factory):
    detail = get_feed_detail(
        client_factory,
        avl_feed_last_checked=datetime.datetime(2026, 7, 15, 9, 35, tzinfo=pytz.utc),
    )
    assert detail["lastServerUpdate"] == "15 Jul 2026 10:35"


def _org_admin_client(client_factory):
    user = UserFactory(account_type=OrgAdminType)
    client = client_factory(host=PUBLISH_HOST)
    client.force_login(user)
    return user, client


def _api_url(name, dataset):
    return reverse(
        name,
        host=PUBLISH_HOST,
        kwargs={"pk1": dataset.organisation_id, "pk": dataset.id},
    )


def _draft_revision(**kwargs):
    revision = AVLDatasetRevisionFactory(is_published=False, status="success", **kwargs)
    CAVLValidationTaskResultFactory(
        revision=revision,
        status=CAVLValidationTaskResult.SUCCESS,
        result=CAVLValidationTaskResult.VALID,
    )
    return revision


def test_feed_detail_reports_live_revision(client_factory):
    user, client = _org_admin_client(client_factory)
    org = user.organisations.first()
    live = AVLDatasetRevisionFactory(dataset__organisation=org).dataset
    draft_only = _draft_revision(dataset__organisation=org).dataset

    assert client.get(_api_url("nextjs-avl-detail", live)).json()["hasLiveRevision"]
    response = client.get(_api_url("nextjs-avl-detail", draft_only))
    assert response.json()["hasLiveRevision"] is False


@pytest.mark.parametrize("has_live_revision", [False, True])
@patch("transit_odp.organisation.models.data.CAVLService")
def test_publish_redirects_to_public_success_page(
    _cavl, client_factory, has_live_revision
):
    user, client = _org_admin_client(client_factory)
    org = user.organisations.first()
    if has_live_revision:
        dataset = AVLDatasetRevisionFactory(dataset__organisation=org).dataset
        _draft_revision(dataset=dataset)
    else:
        dataset = _draft_revision(dataset__organisation=org).dataset

    response = client.post(_api_url("nextjs-avl-publish", dataset))

    assert response.status_code == 200
    success = "update/success/" if has_live_revision else "success/"
    assert response.json()["redirect"] == (
        f"/org/{org.id}/dataset/avl/{dataset.id}/{success}"
    )


@patch("transit_odp.avl.views.api.delete_dataset_revision")
def test_delete_redirects_to_public_success_page(_delete, client_factory):
    user, client = _org_admin_client(client_factory)
    dataset = _draft_revision(dataset__organisation=user.organisations.first()).dataset

    response = client.post(_api_url("nextjs-avl-delete", dataset))

    assert response.json()["redirect"] == (
        f"/org/{dataset.organisation_id}/dataset/avl/{dataset.id}/delete/success/"
    )


def test_edit_description_redirects_to_public_feed_detail(client_factory):
    user, client = _org_admin_client(client_factory)
    dataset = AVLDatasetRevisionFactory(
        dataset__organisation=user.organisations.first()
    ).dataset

    response = client.post(
        _api_url("nextjs-avl-dataset-edit-save", dataset),
        {"description": "New description", "short_description": "Short"},
    )

    assert response.status_code == 200
    assert response.json()["redirect"] == (
        f"/org/{dataset.organisation_id}/dataset/avl/{dataset.id}/"
    )
