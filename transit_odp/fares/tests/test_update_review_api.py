from unittest.mock import Mock, patch

import pytest
from django_hosts import reverse
from waffle.testutils import override_flag

from config.hosts import PUBLISH_HOST
from transit_odp.fares_validator.factories import FaresValidationResultFactory
from transit_odp.organisation.constants import FaresType, TimetableType
from transit_odp.organisation.factories import DatasetFactory, DatasetRevisionFactory
from transit_odp.users.constants import OrgAdminType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


def _url(name, dataset, org_id=None):
    return reverse(
        name,
        host=PUBLISH_HOST,
        kwargs={"pk1": org_id or dataset.organisation_id, "pk": dataset.id},
    )


@pytest.fixture
def fares_dataset(client_factory):
    user = UserFactory(account_type=OrgAdminType)
    dataset = DatasetFactory(
        organisation=user.organisations.first(), dataset_type=FaresType
    )
    return client_factory(host=PUBLISH_HOST), user, dataset


@override_flag("is_fares_validator_active", active=False)
def test_update_success_hides_validator_error_when_flag_is_off(fares_dataset):
    client, user, dataset = fares_dataset
    FaresValidationResultFactory(
        revision=dataset.live_revision, organisation=dataset.organisation, count=3
    )
    client.force_login(user)

    response = client.get(_url("nextjs-fares-update-success", dataset))

    assert response.status_code == 200
    assert response.json() == {
        "isFaresValidatorActive": False,
        "validatorError": False,
    }


@pytest.mark.parametrize(("count", "expected"), [(3, True), (0, False)])
@override_flag("is_fares_validator_active", active=True)
def test_update_success_reports_live_revision_validation_result(
    fares_dataset, count, expected
):
    client, user, dataset = fares_dataset
    FaresValidationResultFactory(
        revision=dataset.live_revision, organisation=dataset.organisation, count=count
    )
    client.force_login(user)

    response = client.get(_url("nextjs-fares-update-success", dataset))

    assert response.status_code == 200
    assert response.json() == {
        "isFaresValidatorActive": True,
        "validatorError": expected,
    }


@override_flag("is_fares_validator_active", active=True)
def test_update_success_tolerates_missing_validation_result(fares_dataset):
    client, user, dataset = fares_dataset
    client.force_login(user)

    response = client.get(_url("nextjs-fares-update-success", dataset))

    assert response.status_code == 200
    assert response.json()["validatorError"] is False


def test_update_success_requires_authentication(fares_dataset):
    client, _, dataset = fares_dataset

    response = client.get(_url("nextjs-fares-update-success", dataset))

    assert response.status_code == 401
    assert response.json() == {"error": "Authentication required"}


def test_update_success_rejects_user_from_another_organisation(fares_dataset):
    client, _, dataset = fares_dataset
    client.force_login(UserFactory(account_type=OrgAdminType))

    response = client.get(_url("nextjs-fares-update-success", dataset))

    assert response.status_code == 404
    assert response.json() == {"error": "Organisation not found"}


def test_update_success_rejects_non_org_user(fares_dataset):
    client, _, dataset = fares_dataset
    client.force_login(UserFactory())

    response = client.get(_url("nextjs-fares-update-success", dataset))

    assert response.status_code == 403


def test_update_success_404_for_other_dataset_type(fares_dataset):
    client, user, _ = fares_dataset
    timetable = DatasetFactory(
        organisation=user.organisations.first(), dataset_type=TimetableType
    )
    client.force_login(user)

    response = client.get(_url("nextjs-fares-update-success", timetable))

    assert response.status_code == 404
    assert response.json() == {"error": "Dataset not found"}


def test_update_success_is_get_only(fares_dataset):
    client, user, dataset = fares_dataset
    client.force_login(user)

    assert client.post(_url("nextjs-fares-update-success", dataset)).status_code == 405


@pytest.mark.parametrize("modify_draft", [True, False])
def test_update_always_redirects_to_update_review(fares_dataset, modify_draft):
    """Django's wizard and modify views all finish on ``update/review``."""
    client, user, dataset = fares_dataset
    draft = DatasetRevisionFactory(dataset=dataset, is_published=False)
    client.force_login(user)
    data = {"modify_draft": "true"} if modify_draft else {}
    valid_form = Mock(is_valid=Mock(return_value=True), cleaned_data={})

    with patch(
        "transit_odp.fares.views.api.FaresFeedUploadForm", return_value=valid_form
    ), patch(
        "transit_odp.fares.views.api.FaresFeedCommentForm", return_value=valid_form
    ), patch(
        "transit_odp.fares.views.api._trigger_fares_processing"
    ), patch(
        "transit_odp.organisation.models.Dataset.start_revision", return_value=draft
    ):
        response = client.post(_url("nextjs-fares-update", dataset), data)

    assert response.status_code == 201
    assert response.json() == {
        "redirect": (
            f"/publish/org/{dataset.organisation_id}/dataset/fares/"
            f"{dataset.id}/update/review"
        )
    }
