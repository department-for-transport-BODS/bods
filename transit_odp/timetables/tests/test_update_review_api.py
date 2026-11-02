from unittest.mock import Mock, patch

import pytest
from django.test import override_settings
from django.utils.dateparse import parse_datetime
from django_hosts import reverse

from config.hosts import PUBLISH_HOST
from transit_odp.data_quality.factories.report import PTIObservationFactory
from transit_odp.organisation.constants import TimetableType
from transit_odp.organisation.factories import DatasetFactory, DatasetRevisionFactory
from transit_odp.users.constants import OrgAdminType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


def _success_url(dataset):
    return reverse(
        "nextjs-timetables-update-success",
        host=PUBLISH_HOST,
        kwargs={"pk1": dataset.organisation_id, "pk": dataset.id},
    )


@pytest.fixture
def update_success(client_factory):
    user = UserFactory(account_type=OrgAdminType)
    dataset = DatasetFactory(
        organisation=user.organisations.first(), dataset_type=TimetableType
    )
    return client_factory(host=PUBLISH_HOST), user, dataset


@override_settings(PTI_ENFORCED_DATE=parse_datetime("2021-08-02T00:00:00"))
def test_update_success_returns_pti_context_for_live_revision(update_success):
    client, user, dataset = update_success
    client.force_login(user)

    response = client.get(_success_url(dataset))

    assert response.status_code == 200
    assert response.json() == {
        "isPtiCompliant": True,
        "ptiEnforcedDate": "2021-08-02",
    }


def test_update_success_flags_live_revision_with_pti_observations(update_success):
    client, user, dataset = update_success
    PTIObservationFactory(revision=dataset.live_revision)
    client.force_login(user)

    response = client.get(_success_url(dataset))

    assert response.status_code == 200
    assert response.json()["isPtiCompliant"] is False


def test_update_success_requires_authentication(update_success):
    client, _, dataset = update_success

    response = client.get(_success_url(dataset))

    assert response.status_code == 401
    assert response.json() == {"error": "Authentication required"}


def test_update_success_rejects_user_from_another_organisation(update_success):
    client, _, dataset = update_success
    client.force_login(UserFactory(account_type=OrgAdminType))

    response = client.get(_success_url(dataset))

    assert response.status_code == 404
    assert response.json() == {"error": "Organisation not found"}


def test_update_success_rejects_non_org_user(update_success):
    client, _, dataset = update_success
    client.force_login(UserFactory())

    assert client.get(_success_url(dataset)).status_code == 403


def test_update_success_404_for_dataset_in_another_organisation(update_success):
    client, user, _ = update_success
    other_dataset = DatasetFactory(dataset_type=TimetableType)
    client.force_login(user)

    response = client.get(
        reverse(
            "nextjs-timetables-update-success",
            host=PUBLISH_HOST,
            kwargs={"pk1": user.organisations.first().id, "pk": other_dataset.id},
        )
    )

    assert response.status_code == 404
    assert response.json() == {"error": "Dataset not found"}


def test_update_success_is_get_only(update_success):
    client, user, dataset = update_success
    client.force_login(user)

    assert client.post(_success_url(dataset)).status_code == 405


@pytest.mark.parametrize(
    ("is_update", "expected_path"),
    [
        ("true", "update/review"),
        (None, "review"),
    ],
)
def test_update_draft_redirects_to_the_matching_review_route(
    client_factory, is_update, expected_path
):
    user = UserFactory(account_type=OrgAdminType)
    dataset = DatasetFactory(
        organisation=user.organisations.first(), dataset_type=TimetableType
    )
    DatasetRevisionFactory(dataset=dataset, is_published=False)
    client = client_factory(host=PUBLISH_HOST)
    client.force_login(user)
    url = reverse(
        "nextjs-timetables-update",
        host=PUBLISH_HOST,
        kwargs={"pk1": dataset.organisation_id, "pk": dataset.id},
    )
    data = {"modify_draft": "true"}
    if is_update:
        data["is_update"] = is_update

    with patch("transit_odp.timetables.views.api.FeedUploadForm") as form_class, patch(
        "transit_odp.timetables.views.api._trigger_timetables_processing"
    ):
        form_class.return_value = Mock(
            is_valid=Mock(return_value=True), cleaned_data={}
        )
        response = client.post(url, data)

    assert response.status_code == 201
    assert response.json() == {
        "redirect": (
            f"/publish/org/{dataset.organisation_id}/dataset/timetable/"
            f"{dataset.id}/{expected_path}"
        )
    }


def _update_url(dataset):
    return reverse(
        "nextjs-timetables-update",
        host=PUBLISH_HOST,
        kwargs={"pk1": dataset.organisation_id, "pk": dataset.id},
    )


UPDATE_FROM_LIVE_DATA = {
    "comment": "New timetables for the summer",
    "selected_item": "url_link-conditional",
    "url_link": "https://example.com/timetables.zip",
}


def test_update_from_live_creates_a_draft_revision(update_success):
    """Django ``FeedUpdateWizard`` starts a new draft from the live data set."""
    client, user, dataset = update_success
    client.force_login(user)

    with patch(
        "transit_odp.timetables.views.api._trigger_timetables_processing"
    ) as trigger:
        response = client.post(_update_url(dataset), UPDATE_FROM_LIVE_DATA)

    assert response.status_code == 201
    assert response.json() == {
        "redirect": (
            f"/publish/org/{dataset.organisation_id}/dataset/timetable/"
            f"{dataset.id}/update/review"
        )
    }
    draft = dataset.revisions.get(is_published=False)
    assert draft.comment == "New timetables for the summer"
    assert draft.url_link == "https://example.com/timetables.zip"
    assert draft.last_modified_user == user
    assert draft.description == dataset.live_revision.description
    trigger.assert_called_once_with(draft)


def test_update_from_live_requires_a_comment(update_success):
    client, user, dataset = update_success
    client.force_login(user)

    response = client.post(
        _update_url(dataset), {**UPDATE_FROM_LIVE_DATA, "comment": ""}
    )

    assert response.status_code == 400
    assert response.json()["field_errors"] == {
        "comment": ["Enter a comment in the box below"]
    }
    assert not dataset.revisions.filter(is_published=False).exists()


def test_update_from_live_validates_the_upload(update_success):
    client, user, dataset = update_success
    client.force_login(user)

    response = client.post(
        _update_url(dataset), {**UPDATE_FROM_LIVE_DATA, "url_link": ""}
    )

    assert response.status_code == 400
    assert response.json()["field_errors"] == {
        "url_link": ["Please provide a URL link"]
    }
    assert not dataset.revisions.filter(is_published=False).exists()


def test_update_from_live_rejects_an_existing_draft(update_success):
    """Django redirects to ``feed-draft-exists`` instead of starting a second draft."""
    client, user, dataset = update_success
    DatasetRevisionFactory(dataset=dataset, is_published=False)
    client.force_login(user)

    response = client.post(_update_url(dataset), UPDATE_FROM_LIVE_DATA)

    assert response.status_code == 409
    assert response.json() == {"error": "A draft update already exists"}
    assert dataset.revisions.filter(is_published=False).count() == 1


def test_update_from_live_get_returns_the_live_url_link(update_success):
    """Django's ``FeedUpdateWizard`` pre-fills the upload from the live revision."""
    client, user, dataset = update_success
    dataset.live_revision.url_link = "https://example.com/live.zip"
    dataset.live_revision.save()
    client.force_login(user)

    response = client.get(_update_url(dataset))

    assert response.status_code == 200
    assert response.json() == {"urlLink": "https://example.com/live.zip"}
    assert not dataset.revisions.filter(is_published=False).exists()


def test_update_404_for_dataset_in_another_organisation(update_success):
    client, user, _ = update_success
    other_dataset = DatasetFactory(dataset_type=TimetableType)
    client.force_login(user)

    response = client.post(
        reverse(
            "nextjs-timetables-update",
            host=PUBLISH_HOST,
            kwargs={"pk1": user.organisations.first().id, "pk": other_dataset.id},
        ),
        UPDATE_FROM_LIVE_DATA,
    )

    assert response.status_code == 404
    assert response.json() == {"error": "Dataset not found"}


@pytest.mark.parametrize(
    ("has_live_revision", "expected_path"),
    [(False, "success"), (True, "update/success")],
)
def test_publish_redirects_to_the_matching_success_page(
    client_factory, has_live_revision, expected_path
):
    user = UserFactory(account_type=OrgAdminType)
    factory_kwargs = {} if has_live_revision else {"live_revision": None}
    dataset = DatasetFactory(
        organisation=user.organisations.first(),
        dataset_type=TimetableType,
        **factory_kwargs,
    )
    DatasetRevisionFactory(dataset=dataset, is_published=False, status="success")
    client = client_factory(host=PUBLISH_HOST)
    client.force_login(user)

    with patch("transit_odp.organisation.models.DatasetRevision.publish"):
        response = client.post(
            reverse(
                "nextjs-timetables-publish",
                host=PUBLISH_HOST,
                kwargs={"pk1": dataset.organisation_id, "pk": dataset.id},
            )
        )

    assert response.status_code == 200
    assert response.json() == {
        "redirect": (
            f"/publish/org/{dataset.organisation_id}/dataset/timetable/"
            f"{dataset.id}/{expected_path}"
        ),
        "published": True,
    }
