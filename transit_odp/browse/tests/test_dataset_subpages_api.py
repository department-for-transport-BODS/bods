import pytest
from django.conf import settings
from django_hosts import reverse

from config.hosts import DATA_HOST
from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    DatasetRevisionFactory,
    DatasetSubscriptionFactory,
    FaresDatasetRevisionFactory,
    OrganisationFactory,
)
from transit_odp.organisation.models import ConsumerFeedback, DatasetSubscription
from transit_odp.pipelines.factories import (
    DataQualityTaskFactory,
    DatasetETLErrorFactory,
)
from transit_odp.users.constants import OrgAdminType, SiteAdminType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db

KINDS = {
    "timetables": (DatasetRevisionFactory, "TIMETABLE"),
    "avl": (AVLDatasetRevisionFactory, "AVL"),
    "fares": (FaresDatasetRevisionFactory, "FARES"),
}
FEEDBACK_TEXT = "The timetable is wrong."


def api_url(name, kind, pk):
    return reverse(f"api:browser-{kind}-{name}", args=[pk], host=DATA_HOST)


@pytest.fixture()
def data_client(client_factory):
    return client_factory(host=DATA_HOST)


@pytest.fixture()
def user():
    return UserFactory()


def make_revision(kind, **kwargs):
    factory = KINDS[kind][0]
    org = OrganisationFactory()
    UserFactory(account_type=SiteAdminType)
    publisher = UserFactory(account_type=OrgAdminType, organisations=(org,))
    return factory(
        dataset__contact=publisher,
        dataset__organisation=org,
        status=kwargs.pop("status", FeedStatus.live.value),
        published_by=publisher,
        last_modified_user=publisher,
        **kwargs,
    )


class TestChangelogApi:
    @pytest.mark.parametrize("kind", KINDS)
    def test_anonymous_can_read_changelog(self, data_client, kind):
        revision = make_revision(kind, comment="First import")
        dataset = revision.dataset

        response = data_client.get(api_url("changelog", kind, dataset.id))

        assert response.status_code == 200
        body = response.json()
        assert body["datasetId"] == dataset.id
        assert body["datasetType"] == KINDS[kind][1]
        assert body["name"] == revision.name
        assert body["showDataQuality"] is (kind == "timetables")
        assert (body["count"], body["page"], body["totalPages"]) == (1, 1, 1)
        row = body["results"][0]
        assert row["revisionId"] == revision.id
        assert row["comment"] == "First import"
        assert row["statusLabel"] == "Published"
        assert row["statusClass"] == "status-indicator--success"
        assert row["updatedAt"]
        assert row["showErrors"] is False
        assert ("dataQuality" in row) is (kind == "timetables")

    def test_timetable_without_report_has_no_data_quality(self, data_client):
        revision = make_revision("timetables")

        body = data_client.get(
            api_url("changelog", "timetables", revision.dataset.id)
        ).json()

        assert body["results"][0]["dataQuality"] == {"text": "Not available"}

    def test_timetable_with_young_pending_task_is_generating(self, data_client):
        revision = make_revision("timetables")
        DataQualityTaskFactory(revision=revision, status="PENDING")

        body = data_client.get(
            api_url("changelog", "timetables", revision.dataset.id)
        ).json()

        assert body["results"][0]["dataQuality"] == {"text": "Generating..."}

    def test_error_revision_lists_errors(self, data_client):
        revision = make_revision("timetables", status=FeedStatus.error.value)
        DatasetETLErrorFactory(revision=revision, description="Bad file")

        row = data_client.get(
            api_url("changelog", "timetables", revision.dataset.id)
        ).json()["results"][0]

        assert row["statusLabel"] == "Error"
        assert row["showErrors"] is True
        assert row["errors"] == ["Bad file"]

    def test_unpublished_revisions_are_not_listed_and_order_is_newest_first(
        self, data_client
    ):
        first = make_revision("timetables", comment="old")
        dataset = first.dataset
        second = DatasetRevisionFactory(
            dataset=dataset, comment="new", status=FeedStatus.live.value
        )
        DatasetRevisionFactory(
            dataset=dataset,
            is_published=False,
            status=FeedStatus.draft.value,
            comment="draft",
        )

        body = data_client.get(api_url("changelog", "timetables", dataset.id)).json()

        assert [r["comment"] for r in body["results"]] == ["new", "old"]
        assert body["results"][0]["revisionId"] == second.id

    def test_pagination(self, data_client):
        first = make_revision("timetables")
        for _ in range(11):
            DatasetRevisionFactory(dataset=first.dataset)
        url = api_url("changelog", "timetables", first.dataset.id)

        page_one = data_client.get(url).json()
        page_two = data_client.get(url, {"page": 2}).json()

        assert (page_one["count"], page_one["totalPages"]) == (12, 2)
        assert len(page_one["results"]) == 10
        assert len(page_two["results"]) == 2
        assert page_two["page"] == 2

    @pytest.mark.parametrize("page", ["0", "3", "abc"])
    def test_invalid_page_is_404(self, data_client, page):
        revision = make_revision("timetables")

        response = data_client.get(
            api_url("changelog", "timetables", revision.dataset.id), {"page": page}
        )

        assert response.status_code == 404

    @pytest.mark.parametrize("kind", KINDS)
    def test_unknown_dataset_is_404(self, data_client, kind):
        assert data_client.get(api_url("changelog", kind, 999999)).status_code == 404

    @pytest.mark.parametrize(
        "kind, other",
        [("timetables", "avl"), ("avl", "fares"), ("fares", "timetables")],
    )
    def test_wrong_dataset_type_is_404(self, data_client, kind, other):
        revision = make_revision(other)

        response = data_client.get(api_url("changelog", kind, revision.dataset.id))

        assert response.status_code == 404


class TestSubscriptionApi:
    @pytest.mark.parametrize("kind", KINDS)
    def test_anonymous_get_returns_gatekeeper_state(self, data_client, kind):
        revision = make_revision(kind)

        response = data_client.get(api_url("subscription", kind, revision.dataset.id))

        assert response.status_code == 200
        body = response.json()
        assert body["isAuthenticated"] is False
        assert body["isSubscribed"] is None
        assert body["name"] == revision.name

    def test_signed_in_get_reports_subscription_state(self, data_client, user):
        revision = make_revision("timetables")
        url = api_url("subscription", "timetables", revision.dataset.id)
        data_client.force_login(user)

        before = data_client.get(url).json()
        DatasetSubscriptionFactory(dataset=revision.dataset, user=user)
        after = data_client.get(url).json()

        assert before["isAuthenticated"] is True
        assert before["isSubscribed"] is False
        assert before["detailPath"] == f"/timetable/dataset/{revision.dataset.id}/"
        assert after["isSubscribed"] is True

    @pytest.mark.parametrize("kind", KINDS)
    def test_anonymous_post_is_401(self, data_client, kind):
        revision = make_revision(kind)

        response = data_client.post(
            api_url("subscription", kind, revision.dataset.id),
            data={},
            content_type="application/json",
        )

        assert response.status_code == 401
        assert not DatasetSubscription.objects.exists()

    @pytest.mark.parametrize("kind", KINDS)
    def test_post_toggles_subscription(self, data_client, user, kind):
        revision = make_revision(kind)
        dataset = revision.dataset
        url = api_url("subscription", kind, dataset.id)
        data_client.force_login(user)

        subscribed = data_client.post(url, data={}, content_type="application/json")
        assert subscribed.json() == {"isSubscribed": True}
        assert user.subscriptions.filter(id=dataset.id).exists()

        unsubscribed = data_client.post(url, data={}, content_type="application/json")
        assert unsubscribed.json() == {"isSubscribed": False}
        assert not user.subscriptions.filter(id=dataset.id).exists()

    @pytest.mark.parametrize("kind", KINDS)
    def test_unpublished_or_missing_dataset_is_404(self, data_client, user, kind):
        draft = make_revision(kind, status=FeedStatus.draft.value, is_published=False)
        data_client.force_login(user)

        assert (
            data_client.get(api_url("subscription", kind, draft.dataset.id)).status_code
            == 404
        )
        assert data_client.get(api_url("subscription", kind, 999999)).status_code == 404

    def test_wrong_dataset_type_is_404(self, data_client, user):
        revision = make_revision("avl")
        data_client.force_login(user)

        for name in ("subscription", "subscription-success"):
            response = data_client.get(api_url(name, "timetables", revision.dataset.id))
            assert response.status_code == 404

    def test_success_defaults_back_to_detail(self, data_client, user):
        revision = make_revision("avl")
        dataset = revision.dataset
        data_client.force_login(user)

        body = data_client.get(
            api_url("subscription-success", "avl", dataset.id)
        ).json()

        assert body["isSubscribed"] is False
        assert body["backPath"] == f"/avl/dataset/{dataset.id}/"
        assert body["backButtonText"] == "Go back to data feed"

    @pytest.mark.parametrize(
        "kind, text",
        [("timetables", "data set"), ("fares", "data set")],
    )
    def test_success_back_button_text(self, data_client, user, kind, text):
        revision = make_revision(kind)
        data_client.force_login(user)

        body = data_client.get(
            api_url("subscription-success", kind, revision.dataset.id)
        ).json()

        assert body["backButtonText"] == f"Go back to {text}"

    def test_success_returns_to_stashed_manage_page(self, data_client, user):
        revision = make_revision("timetables")
        dataset = revision.dataset
        DatasetSubscriptionFactory(dataset=dataset, user=user)
        data_client.force_login(user)

        data_client.get(
            api_url("subscription", "timetables", dataset.id),
            {"backPath": "/account/manage?page=4"},
        )
        body = data_client.get(
            api_url("subscription-success", "timetables", dataset.id)
        ).json()

        assert body["backPath"] == "/account/manage?page=1"
        assert body["backButtonText"] == "Go back to manage subscriptions"

    @pytest.mark.parametrize("back", ["//evil.example", "https://evil.example", "x"])
    def test_unsafe_back_path_falls_back_to_detail(self, data_client, user, back):
        revision = make_revision("timetables")
        dataset = revision.dataset
        data_client.force_login(user)

        data_client.get(
            api_url("subscription", "timetables", dataset.id), {"backPath": back}
        )
        body = data_client.get(
            api_url("subscription-success", "timetables", dataset.id)
        ).json()

        assert body["backPath"] == f"/timetable/dataset/{dataset.id}/"

    def test_anonymous_success_is_public_without_back_path(self, data_client):
        revision = make_revision("timetables")

        body = data_client.get(
            api_url("subscription-success", "timetables", revision.dataset.id)
        ).json()

        assert body["isAuthenticated"] is False
        assert "backPath" not in body


class TestFeedbackApi:
    @pytest.mark.parametrize("name", ["feedback", "feedback-success"])
    @pytest.mark.parametrize("kind", KINDS)
    def test_anonymous_is_401(self, data_client, kind, name):
        revision = make_revision(kind)

        response = data_client.get(api_url(name, kind, revision.dataset.id))

        assert response.status_code == 401

    def test_anonymous_post_is_401(self, data_client):
        revision = make_revision("timetables")

        response = data_client.post(
            api_url("feedback", "timetables", revision.dataset.id),
            data={"feedback": FEEDBACK_TEXT},
            content_type="application/json",
        )

        assert response.status_code == 401
        assert not ConsumerFeedback.objects.exists()

    @pytest.mark.parametrize("kind", KINDS)
    def test_get_returns_dataset_details(self, data_client, user, kind):
        revision = make_revision(kind)
        dataset = revision.dataset
        data_client.force_login(user)

        response = data_client.get(api_url("feedback", kind, dataset.id))

        assert response.status_code == 200
        body = response.json()
        assert body["datasetId"] == dataset.id
        assert body["datasetType"] == KINDS[kind][1]
        assert body["name"] == revision.name
        assert body["service"] is None
        assert body["backPath"].endswith(f"/dataset/{dataset.id}/")

    def test_get_unknown_dataset_is_404(self, data_client, user):
        data_client.force_login(user)

        response = data_client.get(api_url("feedback", "timetables", 999999))

        assert response.status_code == 404

    def test_get_dataset_without_live_revision_is_404(self, data_client, user):
        revision = make_revision(
            "timetables", status=FeedStatus.draft.value, is_published=False
        )
        data_client.force_login(user)

        response = data_client.get(
            api_url("feedback", "timetables", revision.dataset.id)
        )

        assert response.status_code == 404

    @pytest.mark.parametrize("payload", [{}, {"feedback": ""}, {"feedback": "  "}])
    def test_post_requires_feedback(self, data_client, user, payload):
        revision = make_revision("timetables")
        data_client.force_login(user)

        response = data_client.post(
            api_url("feedback", "timetables", revision.dataset.id),
            data=payload,
            content_type="application/json",
        )

        assert response.status_code == 400
        body = response.json()
        assert body["field_errors"] == {"feedback": ["Enter feedback in the box below"]}
        assert not ConsumerFeedback.objects.exists()

    @pytest.mark.parametrize("kind", KINDS)
    def test_post_saves_feedback_and_sends_emails(
        self, data_client, user, kind, mailoutbox
    ):
        revision = make_revision(kind)
        dataset = revision.dataset
        data_client.force_login(user)

        response = data_client.post(
            api_url("feedback", kind, dataset.id),
            data={"feedback": FEEDBACK_TEXT, "anonymous": False},
            content_type="application/json",
        )

        assert response.status_code == 200
        segment = "timetable" if kind == "timetables" else kind
        assert response.json()["redirectPath"] == (
            f"/{segment}/dataset/{dataset.id}/feedback/success"
        )
        feedback = ConsumerFeedback.objects.get(dataset=dataset)
        assert feedback.consumer == user
        assert feedback.feedback == FEEDBACK_TEXT
        assert feedback.revision == revision
        assert len(mailoutbox) == 3
        assert mailoutbox[0].from_email == settings.DEFAULT_FROM_EMAIL

    def test_post_anonymous_flag_drops_consumer(self, data_client, user):
        revision = make_revision("timetables")
        data_client.force_login(user)

        response = data_client.post(
            api_url("feedback", "timetables", revision.dataset.id),
            data={"feedback": FEEDBACK_TEXT, "anonymous": True},
            content_type="application/json",
        )

        assert response.status_code == 200
        assert ConsumerFeedback.objects.get(dataset=revision.dataset).consumer is None

    def test_success_back_paths(self, data_client, user):
        timetable = make_revision("timetables").dataset
        avl = make_revision("avl").dataset
        fares = make_revision("fares").dataset
        data_client.force_login(user)

        def back(kind, dataset):
            response = data_client.get(api_url("feedback-success", kind, dataset.id))
            assert response.status_code == 200
            return response.json()["backPath"]

        assert (
            back("timetables", timetable)
            == f"/timetable/dataset/{timetable.id}/detail/"
        )
        assert back("avl", avl) == f"/avl/dataset/{avl.id}/"
        assert back("fares", fares) == f"/fares/dataset/{fares.id}/"
