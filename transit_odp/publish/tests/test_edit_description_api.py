import pytest

from config import hosts
from transit_odp.organisation.constants import (
    AVLType,
    FaresType,
    FeedStatus,
    TimetableType,
)
from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetRevisionFactory,
    OrganisationFactory,
)
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import OrgAdminFactory, UserFactory

pytestmark = pytest.mark.django_db

DATASET_TYPES = [("timetables", TimetableType), ("fares", FaresType)]
EDIT_MODES = ["dataset-edit", "revision-edit"]


def _url(api_type, mode, org_id, dataset_id, save=False):
    suffix = "save/" if save else ""
    return f"/api/{api_type}/{mode}/{org_id}/{dataset_id}/{suffix}"


def _create_dataset(organisation, dataset_type, with_draft):
    dataset = DatasetFactory(
        organisation=organisation,
        dataset_type=dataset_type,
        live_revision__description="Live description",
        live_revision__short_description="Live short",
    )
    draft = None
    if with_draft:
        draft = DatasetRevisionFactory(
            dataset=dataset,
            is_published=False,
            status=FeedStatus.draft.value,
            description="Draft description",
            short_description="Draft short",
        )
    dataset.refresh_from_db()
    return dataset, draft


@pytest.fixture
def org_client(client_factory):
    organisation = OrganisationFactory()
    user = OrgAdminFactory(organisations=(organisation,))
    client = client_factory(host=hosts.PUBLISH_HOST)
    client.force_login(user=user)
    return client, organisation


@pytest.mark.parametrize("mode", EDIT_MODES)
@pytest.mark.parametrize("api_type,dataset_type", DATASET_TYPES)
def test_edit_description_requires_authentication(
    client_factory, api_type, dataset_type, mode
):
    organisation = OrganisationFactory()
    dataset, _ = _create_dataset(organisation, dataset_type, with_draft=False)
    client = client_factory(host=hosts.PUBLISH_HOST)

    get_response = client.get(_url(api_type, mode, organisation.id, dataset.id))
    post_response = client.post(
        _url(api_type, mode, organisation.id, dataset.id, save=True)
    )

    assert get_response.status_code == 401
    assert post_response.status_code == 401


@pytest.mark.parametrize("mode", EDIT_MODES)
@pytest.mark.parametrize("api_type,dataset_type", DATASET_TYPES)
def test_edit_description_is_forbidden_for_another_org(
    org_client, api_type, dataset_type, mode
):
    client, _ = org_client
    other_org = OrganisationFactory()
    dataset, _ = _create_dataset(other_org, dataset_type, with_draft=False)

    response = client.get(_url(api_type, mode, other_org.id, dataset.id))
    save_response = client.post(
        _url(api_type, mode, other_org.id, dataset.id, save=True),
        {"description": "x", "short_description": "y"},
    )

    assert response.status_code == 403
    assert save_response.status_code == 403
    dataset.live_revision.refresh_from_db()
    assert dataset.live_revision.description == "Live description"


def test_edit_description_is_forbidden_for_abods_user(client_factory):
    organisation = OrganisationFactory()
    user = UserFactory(
        account_type=AccountType.abods_user.value, organisations=(organisation,)
    )
    dataset, _ = _create_dataset(organisation, TimetableType, with_draft=False)
    client = client_factory(host=hosts.PUBLISH_HOST)
    client.force_login(user=user)

    response = client.get(
        _url("timetables", "dataset-edit", organisation.id, dataset.id)
    )

    assert response.status_code == 403


@pytest.mark.parametrize("mode", EDIT_MODES)
@pytest.mark.parametrize(
    "api_type,wrong_type",
    [("timetables", FaresType), ("fares", TimetableType), ("fares", AVLType)],
)
def test_edit_description_404s_for_wrong_dataset_type(
    org_client, api_type, wrong_type, mode
):
    client, organisation = org_client
    dataset, _ = _create_dataset(organisation, wrong_type, with_draft=False)

    response = client.get(_url(api_type, mode, organisation.id, dataset.id))
    save_response = client.post(
        _url(api_type, mode, organisation.id, dataset.id, save=True),
        {"description": "x", "short_description": "y"},
    )

    assert response.status_code == 404
    assert response.json() == {"error": "Dataset not found"}
    assert save_response.status_code == 404


@pytest.mark.parametrize("api_type,dataset_type", DATASET_TYPES)
def test_dataset_edit_404s_without_live_revision(org_client, api_type, dataset_type):
    client, organisation = org_client
    dataset = DatasetFactory(
        organisation=organisation, dataset_type=dataset_type, live_revision=None
    )
    DatasetRevisionFactory(
        dataset=dataset, is_published=False, status=FeedStatus.draft.value
    )

    response = client.get(_url(api_type, "dataset-edit", organisation.id, dataset.id))

    assert response.status_code == 404
    assert response.json() == {"error": "Dataset revision not found"}


@pytest.mark.parametrize("api_type,dataset_type", DATASET_TYPES)
def test_dataset_edit_gets_and_saves_live_revision(org_client, api_type, dataset_type):
    client, organisation = org_client
    dataset, draft = _create_dataset(organisation, dataset_type, with_draft=True)
    live = dataset.live_revision

    response = client.get(_url(api_type, "dataset-edit", organisation.id, dataset.id))

    assert response.status_code == 200
    assert response.json() == {
        "datasetId": dataset.id,
        "name": live.name,
        "description": "Live description",
        "shortDescription": "Live short",
        "isRevisionUpdate": True,
    }

    save_response = client.post(
        _url(api_type, "dataset-edit", organisation.id, dataset.id, save=True),
        {"description": "New description", "short_description": "New short"},
    )

    assert save_response.status_code == 200
    assert save_response.json()["description"] == "New description"
    live.refresh_from_db()
    draft.refresh_from_db()
    assert live.description == "New description"
    assert live.short_description == "New short"
    assert draft.description == "Draft description"


@pytest.mark.parametrize("api_type,dataset_type", DATASET_TYPES)
def test_revision_edit_gets_and_saves_latest_revision(
    org_client, api_type, dataset_type
):
    client, organisation = org_client
    dataset, draft = _create_dataset(organisation, dataset_type, with_draft=True)
    live = dataset.live_revision

    response = client.get(_url(api_type, "revision-edit", organisation.id, dataset.id))

    assert response.status_code == 200
    assert response.json() == {
        "datasetId": dataset.id,
        "name": draft.name,
        "description": "Draft description",
        "shortDescription": "Draft short",
        "isRevisionUpdate": True,
    }

    save_response = client.post(
        _url(api_type, "revision-edit", organisation.id, dataset.id, save=True),
        {"description": "New description", "short_description": "New short"},
    )

    assert save_response.status_code == 200
    draft.refresh_from_db()
    live.refresh_from_db()
    assert draft.description == "New description"
    assert draft.short_description == "New short"
    assert live.description == "Live description"


@pytest.mark.parametrize("api_type,dataset_type", DATASET_TYPES)
def test_revision_edit_for_new_dataset_is_not_an_update(
    org_client, api_type, dataset_type
):
    client, organisation = org_client
    dataset = DatasetFactory(
        organisation=organisation, dataset_type=dataset_type, live_revision=None
    )
    draft = DatasetRevisionFactory(
        dataset=dataset, is_published=False, status=FeedStatus.draft.value
    )

    response = client.get(_url(api_type, "revision-edit", organisation.id, dataset.id))

    assert response.status_code == 200
    assert response.json()["name"] == draft.name
    assert response.json()["isRevisionUpdate"] is False


@pytest.mark.parametrize("mode", EDIT_MODES)
@pytest.mark.parametrize("api_type,dataset_type", DATASET_TYPES)
def test_edit_description_returns_form_errors(org_client, api_type, dataset_type, mode):
    client, organisation = org_client
    dataset, _ = _create_dataset(organisation, dataset_type, with_draft=True)

    response = client.post(
        _url(api_type, mode, organisation.id, dataset.id, save=True),
        {"description": "", "short_description": "x" * 31},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "Description validation failed"
    assert body["field_errors"]["description"] == [
        "Enter a description in the data set description box below "
    ]
    assert body["field_errors"]["short_description"] == [
        "Ensure this value has at most 30 characters (it has 31)."
    ]


@pytest.mark.parametrize("api_type,dataset_type", DATASET_TYPES)
def test_edit_description_returns_required_short_description_error(
    org_client, api_type, dataset_type
):
    client, organisation = org_client
    dataset, _ = _create_dataset(organisation, dataset_type, with_draft=False)

    response = client.post(
        _url(api_type, "dataset-edit", organisation.id, dataset.id, save=True),
        {"description": "Something", "short_description": ""},
    )

    assert response.status_code == 400
    assert response.json()["field_errors"] == {
        "short_description": [
            "Enter a short description in the data set short description box below "
        ]
    }
