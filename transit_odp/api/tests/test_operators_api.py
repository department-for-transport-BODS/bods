import pytest
from django.conf import settings
from waffle.testutils import override_flag

from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.organisation.models import ConsumerFeedback
from transit_odp.users.constants import OrgAdminType, SiteAdminType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db

LIST_URL = "/api/browser/operators/"
FEEDBACK = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."


def detail_url(pk):
    return f"/api/browser/operators/{pk}/"


def contact_url(pk):
    return f"/api/browser/operators/{pk}/contact/"


class TestOperatorsList:
    def test_lists_active_operators_by_name(self, data_client):
        OrganisationFactory(name="Beta Buses")
        OrganisationFactory(name="Alpha Travel")
        OrganisationFactory(name="Hidden Coaches", is_active=False)

        response = data_client.get(LIST_URL)

        assert response.status_code == 200
        payload = response.json()
        assert [r["name"] for r in payload["results"]] == [
            "Alpha Travel",
            "Beta Buses",
        ]
        assert payload["count"] == 2
        assert payload["ordering"] == "name"
        assert payload["page"] == 1
        assert payload["numPages"] == 1
        assert set(payload["operatorNames"]) == {"Alpha Travel", "Beta Buses"}
        assert set(payload["results"][0]) == {"id", "name", "created"}

    def test_search_is_case_insensitive_and_stripped(self, data_client):
        OrganisationFactory(name="Alpha Travel")
        OrganisationFactory(name="Beta Buses")

        response = data_client.get(LIST_URL, {"q": "  ALPHA "})

        payload = response.json()
        assert [r["name"] for r in payload["results"]] == ["Alpha Travel"]
        assert payload["count"] == 1
        assert payload["q"] == "  ALPHA "

    def test_no_results(self, data_client):
        OrganisationFactory(name="Alpha Travel")

        payload = data_client.get(LIST_URL, {"q": "zzz"}).json()

        assert payload["count"] == 0
        assert payload["results"] == []

    @pytest.mark.parametrize(
        ("ordering", "expected"),
        [
            ("name", ["A", "B", "C"]),
            ("-name", ["C", "B", "A"]),
            ("created", ["B", "C", "A"]),
            ("-created", ["A", "C", "B"]),
        ],
    )
    def test_ordering(self, data_client, ordering, expected):
        OrganisationFactory(name="B")
        OrganisationFactory(name="C")
        OrganisationFactory(name="A")

        payload = data_client.get(LIST_URL, {"ordering": ordering}).json()

        assert [r["name"] for r in payload["results"]] == expected
        assert payload["ordering"] == ordering

    def test_unknown_ordering_falls_back_to_name(self, data_client):
        OrganisationFactory(name="B")
        OrganisationFactory(name="A")

        payload = data_client.get(LIST_URL, {"ordering": "password"}).json()

        assert payload["ordering"] == "name"
        assert [r["name"] for r in payload["results"]] == ["A", "B"]

    def test_pagination_is_ten_per_page(self, data_client):
        for index in range(12):
            OrganisationFactory(name=f"Operator {index:02d}")

        first = data_client.get(LIST_URL).json()
        second = data_client.get(LIST_URL, {"page": 2}).json()

        assert first["count"] == 12
        assert first["numPages"] == 2
        assert first["pageSize"] == 10
        assert len(first["results"]) == 10
        assert second["page"] == 2
        assert [r["name"] for r in second["results"]] == [
            "Operator 10",
            "Operator 11",
        ]

    @pytest.mark.parametrize("page", ["3", "0", "abc"])
    def test_invalid_page_is_404(self, data_client, page):
        OrganisationFactory(name="Alpha Travel")

        response = data_client.get(LIST_URL, {"page": page})

        assert response.status_code == 404
        assert response.json() == {"error": "Invalid page"}

    def test_post_is_not_allowed(self, data_client):
        assert data_client.post(LIST_URL).status_code == 405


class TestOperatorDetail:
    def test_unknown_operator_is_404(self, data_client):
        response = data_client.get(detail_url(999999))

        assert response.status_code == 404
        assert response.json() == {"error": "Operator not found"}

    def test_inactive_operator_is_404(self, data_client):
        org = OrganisationFactory(is_active=False)

        assert data_client.get(detail_url(org.id)).status_code == 404

    def test_payload_for_anonymous_user(self, data_client):
        org = OrganisationFactory(name="Alpha Travel Ltd", short_name="Alpha")

        response = data_client.get(detail_url(org.id))

        assert response.status_code == 200
        payload = response.json()
        assert payload["id"] == org.id
        assert payload["name"] == "Alpha Travel Ltd"
        assert payload["shortName"] == "Alpha"
        assert payload["isAuthenticated"] is False
        assert payload["timetableFeedUrl"] is None
        assert payload["avlFeedUrl"] is None
        assert payload["faresFeedUrl"] is None
        assert set(payload["flags"]) == {
            "isCompleteServicePagesActive",
            "isAvlRequireAttentionActive",
            "isFaresRequireAttentionActive",
        }
        for key in (
            "totalInScopeInSeasonServices",
            "totalServicesRequiringAttention",
            "timetableServicesRequiringAttentionCount",
            "operatorLicences",
            "licenceNumbers",
            "nocs",
        ):
            assert key in payload

    def test_feed_urls_for_authenticated_user(self, data_client):
        org = OrganisationFactory()
        user = UserFactory()
        data_client.force_login(user)

        payload = data_client.get(detail_url(org.id)).json()

        assert payload["isAuthenticated"] is True
        token = user.auth_token.key
        for key in ("timetableFeedUrl", "avlFeedUrl", "faresFeedUrl"):
            assert payload[key].endswith(f"&api_key={token}")

    @pytest.mark.parametrize("active", [True, False])
    def test_complete_service_pages_flag_is_reported(self, data_client, active):
        org = OrganisationFactory()

        with override_flag("is_complete_service_pages_active", active=active):
            payload = data_client.get(detail_url(org.id)).json()

        assert payload["flags"]["isCompleteServicePagesActive"] is active

    @pytest.mark.parametrize("active", [True, False])
    def test_avl_and_fares_flags_are_reported(self, data_client, active):
        org = OrganisationFactory()

        with override_flag("is_avl_require_attention_active", active=active):
            with override_flag("is_fares_require_attention_active", active=active):
                payload = data_client.get(detail_url(org.id)).json()

        assert payload["flags"]["isAvlRequireAttentionActive"] is active
        assert payload["flags"]["isFaresRequireAttentionActive"] is active


class TestOperatorContact:
    @pytest.fixture()
    def org(self):
        UserFactory(account_type=SiteAdminType)
        org = OrganisationFactory()
        UserFactory(account_type=OrgAdminType, organisations=(org,))
        return org

    def test_requires_login(self, data_client, org):
        assert data_client.get(contact_url(org.id)).status_code == 401
        response = data_client.post(
            contact_url(org.id),
            data={"feedback": FEEDBACK},
            content_type="application/json",
        )
        assert response.status_code == 401
        assert response.json() == {"error": "Authentication required"}
        assert not ConsumerFeedback.objects.exists()

    def test_unknown_operator_is_404(self, data_client, user):
        data_client.force_login(user)

        assert data_client.get(contact_url(999999)).status_code == 404

    def test_get_returns_operator_name_even_if_inactive(self, data_client, user):
        org = OrganisationFactory(name="Dormant Buses", is_active=False)
        data_client.force_login(user)

        response = data_client.get(contact_url(org.id))

        assert response.status_code == 200
        assert response.json() == {"id": org.id, "name": "Dormant Buses"}

    def test_feedback_is_required(self, data_client, user, org):
        data_client.force_login(user)

        response = data_client.post(
            contact_url(org.id),
            data={"feedback": "", "anonymous": False},
            content_type="application/json",
        )

        assert response.status_code == 400
        payload = response.json()
        assert payload["error"] == "Validation failed"
        assert payload["field_errors"] == {
            "feedback": ["Enter feedback in the box below"]
        }
        assert not ConsumerFeedback.objects.exists()

    def test_feedback_is_saved_and_emailed(
        self, data_client, user, org, bods_mailoutbox
    ):
        data_client.force_login(user)

        response = data_client.post(
            contact_url(org.id),
            data={"feedback": FEEDBACK, "anonymous": False},
            content_type="application/json",
        )

        assert response.status_code == 200
        assert response.json() == {"success": True}
        feedback = ConsumerFeedback.objects.get()
        assert feedback.feedback == FEEDBACK
        assert feedback.organisation == org
        assert feedback.consumer == user
        assert feedback.dataset_id is None
        # site admin + submitter copies, then the org admin notification
        assert len(bods_mailoutbox) == 3
        notification = bods_mailoutbox[-1]
        assert user.email in notification.body
        assert org.name in notification.body
        assert notification.from_email == settings.DEFAULT_FROM_EMAIL

    def test_anonymous_feedback_hides_consumer(
        self, data_client, user, org, bods_mailoutbox
    ):
        data_client.force_login(user)

        response = data_client.post(
            contact_url(org.id),
            data={"feedback": FEEDBACK, "anonymous": True},
            content_type="application/json",
        )

        assert response.status_code == 200
        feedback = ConsumerFeedback.objects.get()
        assert feedback.consumer is None
        assert user.email not in bods_mailoutbox[-1].body
