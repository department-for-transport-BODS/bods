import pytest
from django_hosts import reverse

from config.hosts import PUBLISH_HOST
from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.factories import (
    DatasetRevisionFactory,
    FaresDatasetRevisionFactory,
    OrganisationFactory,
)
from transit_odp.pipelines.factories import DatasetETLErrorFactory
from transit_odp.users.constants import OrgAdminType, SiteAdminType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db

REVISION_FACTORIES = {
    "timetables": DatasetRevisionFactory,
    "fares": FaresDatasetRevisionFactory,
}
DATASET_TYPE_NAMES = {"timetables": "TIMETABLE", "fares": "FARES"}


@pytest.fixture(params=list(REVISION_FACTORIES))
def kind(request):
    return request.param


@pytest.fixture
def publish_client(client_factory):
    return client_factory(host=PUBLISH_HOST)


def changelog_url(kind, org_id, dataset_id, page=None):
    url = reverse(
        f"nextjs-{kind}-changelog",
        host=PUBLISH_HOST,
        kwargs={"pk1": org_id, "pk": dataset_id},
    )
    return f"{url}?page={page}" if page else url


def make_live_revision(kind, **kwargs):
    org = OrganisationFactory()
    user = UserFactory(account_type=OrgAdminType, organisations=(org,))
    revision = REVISION_FACTORIES[kind](
        dataset__organisation=org,
        dataset__contact=user,
        status=kwargs.pop("status", FeedStatus.live.value),
        published_by=user,
        last_modified_user=user,
        **kwargs,
    )
    return user, org, revision


def test_requires_authentication(publish_client, kind):
    _, org, revision = make_live_revision(kind)

    response = publish_client.get(changelog_url(kind, org.id, revision.dataset_id))

    assert response.status_code == 401
    assert response.json() == {"error": "Authentication required"}


def test_requires_org_user(publish_client, kind):
    _, org, revision = make_live_revision(kind)
    publish_client.force_login(UserFactory(account_type=SiteAdminType))

    response = publish_client.get(changelog_url(kind, org.id, revision.dataset_id))

    assert response.status_code == 403
    assert response.json() == {"error": "Org user access required"}


def test_user_of_another_organisation_gets_404(publish_client, kind):
    _, org, revision = make_live_revision(kind)
    outsider = UserFactory(account_type=OrgAdminType)
    publish_client.force_login(outsider)

    response = publish_client.get(changelog_url(kind, org.id, revision.dataset_id))

    assert response.status_code == 404
    assert response.json() == {"error": "Organisation not found"}


def test_dataset_of_another_organisation_gets_404(publish_client, kind):
    user, _, _ = make_live_revision(kind)
    _, _, other_revision = make_live_revision(kind)
    publish_client.force_login(user)

    response = publish_client.get(
        changelog_url(kind, user.organisations.first().id, other_revision.dataset_id)
    )

    assert response.status_code == 404
    assert response.json() == {"error": "Dataset not found"}


def test_unknown_dataset_gets_404(publish_client, kind):
    user, org, _ = make_live_revision(kind)
    publish_client.force_login(user)

    response = publish_client.get(changelog_url(kind, org.id, 999999))

    assert response.status_code == 404
    assert response.json() == {"error": "Dataset not found"}


def test_dataset_of_the_other_type_gets_404(publish_client):
    user, org, fares_revision = make_live_revision("fares")
    publish_client.force_login(user)

    response = publish_client.get(
        changelog_url("timetables", org.id, fares_revision.dataset_id)
    )

    assert response.status_code == 404
    assert response.json() == {"error": "Dataset not found"}


def test_returns_changelog_payload(publish_client, kind):
    user, org, revision = make_live_revision(kind, comment="First import")
    publish_client.force_login(user)

    response = publish_client.get(changelog_url(kind, org.id, revision.dataset_id))

    assert response.status_code == 200
    body = response.json()
    assert body["datasetId"] == revision.dataset_id
    assert body["datasetType"] == DATASET_TYPE_NAMES[kind]
    assert body["name"] == revision.name
    assert body["showDataQuality"] is (kind == "timetables")
    assert (body["count"], body["page"], body["pageSize"], body["totalPages"]) == (
        1,
        1,
        10,
        1,
    )
    row = body["results"][0]
    assert row["revisionId"] == revision.id
    assert row["comment"] == "First import"
    assert row["statusLabel"] == "Published"
    assert row["statusClass"] == "status-indicator--success"
    assert row["updatedAt"]
    assert row["showErrors"] is False
    assert row["errors"] == []
    assert ("dataQuality" in row) is (kind == "timetables")


def test_timetable_without_report_has_no_data_quality(publish_client):
    user, org, revision = make_live_revision("timetables")
    publish_client.force_login(user)

    body = publish_client.get(
        changelog_url("timetables", org.id, revision.dataset_id)
    ).json()

    assert body["results"][0]["dataQuality"] == {"text": "Not available"}


def test_error_revision_lists_its_errors(publish_client, kind):
    user, org, revision = make_live_revision(kind, status=FeedStatus.error.value)
    DatasetETLErrorFactory(revision=revision, description="Bad file")
    publish_client.force_login(user)

    row = publish_client.get(changelog_url(kind, org.id, revision.dataset_id)).json()[
        "results"
    ][0]

    assert row["statusLabel"] == "Error"
    assert row["statusClass"] == "status-indicator--error"
    assert row["showErrors"] is True
    assert row["errors"] == ["Bad file"]


def test_lists_published_revisions_newest_first_and_skips_drafts(publish_client, kind):
    user, org, first = make_live_revision(kind, comment="old")
    dataset = first.dataset
    second = REVISION_FACTORIES[kind](
        dataset=dataset, comment="new", status=FeedStatus.live.value
    )
    REVISION_FACTORIES[kind](
        dataset=dataset,
        is_published=False,
        status=FeedStatus.draft.value,
        comment="draft",
    )
    publish_client.force_login(user)

    body = publish_client.get(changelog_url(kind, org.id, dataset.id)).json()

    assert [row["comment"] for row in body["results"]] == ["new", "old"]
    assert body["results"][0]["revisionId"] == second.id


def test_paginates_ten_revisions_per_page(publish_client, kind):
    user, org, first = make_live_revision(kind, comment="rev-0")
    dataset = first.dataset
    for index in range(1, 12):
        REVISION_FACTORIES[kind](
            dataset=dataset, comment=f"rev-{index}", status=FeedStatus.live.value
        )
    publish_client.force_login(user)

    page_one = publish_client.get(changelog_url(kind, org.id, dataset.id)).json()
    page_two = publish_client.get(changelog_url(kind, org.id, dataset.id, 2)).json()

    assert (page_one["count"], page_one["page"], page_one["totalPages"]) == (12, 1, 2)
    assert len(page_one["results"]) == 10
    assert (page_two["page"], page_two["totalPages"]) == (2, 2)
    assert [row["comment"] for row in page_two["results"]] == ["rev-1", "rev-0"]


@pytest.mark.parametrize("page", ["3", "0", "abc"])
def test_out_of_range_page_gets_404(publish_client, kind, page):
    user, org, revision = make_live_revision(kind)
    publish_client.force_login(user)

    response = publish_client.get(
        changelog_url(kind, org.id, revision.dataset_id, page)
    )

    assert response.status_code == 404
    assert response.json() == {"error": "Page not found"}


def test_post_is_not_allowed(publish_client, kind):
    user, org, revision = make_live_revision(kind)
    publish_client.force_login(user)

    response = publish_client.post(changelog_url(kind, org.id, revision.dataset_id))

    assert response.status_code == 405
