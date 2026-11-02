import pytest
from django.utils import timezone
from waffle.testutils import override_flag

from config import hosts
from transit_odp.organisation.constants import (
    AVLType,
    FaresType,
    FeedStatus,
    TimetableType,
)
from transit_odp.organisation.factories import (
    ConsumerFeedbackFactory,
    DatasetFactory,
    DatasetRevisionFactory,
    DraftDatasetFactory,
    OrganisationFactory,
    SeasonalServiceFactory,
)
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import (
    AgentUserFactory,
    OrgAdminFactory,
    OrgStaffFactory,
    UserFactory,
)

pytestmark = pytest.mark.django_db

LIST_URLS = {
    TimetableType: "/api/timetables/list/{org}/",
    AVLType: "/api/avl/list/{org}/",
    FaresType: "/api/fares/list/{org}/",
}
ALL_TYPES = pytest.mark.parametrize(
    "dataset_type", [TimetableType, AVLType, FaresType], ids=["txc", "avl", "fares"]
)


def _get(client_factory, user, dataset_type, org_id, query=""):
    client = client_factory(host=hosts.PUBLISH_HOST)
    if user is not None:
        client.force_login(user=user)
    return client.get(LIST_URLS[dataset_type].format(org=org_id) + query)


def _live(organisation, dataset_type, **revision_kwargs):
    dataset = DatasetFactory(
        organisation=organisation, dataset_type=dataset_type, live_revision=None
    )
    revision_kwargs.setdefault("status", FeedStatus.live.value)
    revision = DatasetRevisionFactory(
        dataset=dataset,
        is_published=True,
        published_at=timezone.now(),
        **revision_kwargs,
    )
    dataset.live_revision = revision
    dataset.save()
    return dataset


HTML_LIST_URLS = {
    TimetableType: "/org/{org}/dataset/timetable/",
    AVLType: "/org/{org}/dataset/avl/",
    FaresType: "/org/{org}/dataset/fares/",
}


def _get_html(client_factory, user, dataset_type, org_id):
    client = client_factory(host=hosts.PUBLISH_HOST)
    if user is not None:
        client.force_login(user=user)
    return client.get(HTML_LIST_URLS[dataset_type].format(org=org_id))


@ALL_TYPES
def test_list_requires_authentication(client_factory, dataset_type):
    organisation = OrganisationFactory()

    response = _get(client_factory, None, dataset_type, organisation.id)

    assert response.status_code == 401
    # Django redirects an anonymous visitor to log in; the Next.js page does the same.
    html = _get_html(client_factory, None, dataset_type, organisation.id)
    assert html.status_code == 302
    assert "/account/login/" in html["Location"]


@ALL_TYPES
def test_list_is_forbidden_for_non_org_users(client_factory, dataset_type):
    organisation = OrganisationFactory()
    user = UserFactory(account_type=AccountType.developer.value)

    response = _get(client_factory, user, dataset_type, organisation.id)

    assert response.status_code == 403
    assert (
        _get_html(client_factory, user, dataset_type, organisation.id).status_code
        == 403
    )


@ALL_TYPES
def test_list_is_forbidden_for_abods_users(client_factory, dataset_type):
    organisation = OrganisationFactory()
    user = UserFactory(
        account_type=AccountType.abods_user.value, organisations=(organisation,)
    )

    response = _get(client_factory, user, dataset_type, organisation.id)

    assert response.status_code == 403
    assert (
        _get_html(client_factory, user, dataset_type, organisation.id).status_code
        == 403
    )


@ALL_TYPES
def test_list_is_forbidden_for_another_organisation_like_django(
    client_factory, dataset_type
):
    """OrgUserViewMixin.has_permission rejects with a 403, not a 404."""
    organisation = OrganisationFactory()
    other = OrganisationFactory()
    user = OrgAdminFactory(organisations=(other,))

    response = _get(client_factory, user, dataset_type, organisation.id)

    assert response.status_code == 403
    assert (
        _get_html(client_factory, user, dataset_type, organisation.id).status_code
        == 403
    )


@ALL_TYPES
def test_list_is_forbidden_for_an_organisation_that_does_not_exist(
    client_factory, dataset_type
):
    user = OrgAdminFactory()

    response = _get(client_factory, user, dataset_type, 999999)

    assert response.status_code == 403
    assert _get_html(client_factory, user, dataset_type, 999999).status_code == 403


@ALL_TYPES
@pytest.mark.parametrize(
    "factory",
    [OrgAdminFactory, OrgStaffFactory, AgentUserFactory],
    ids=lambda f: f.__name__,
)
def test_list_is_available_to_org_admin_staff_and_agents(
    client_factory, dataset_type, factory
):
    organisation = OrganisationFactory()
    user = factory(organisations=(organisation,))
    _live(organisation, dataset_type, name="Live feed")

    response = _get(client_factory, user, dataset_type, organisation.id)

    assert response.status_code == 200
    payload = response.json()
    assert payload["isAgentUser"] is (factory is AgentUserFactory)
    assert payload["organisation"] == {
        "id": organisation.id,
        "name": organisation.name,
    }
    subject = organisation.name if factory is AgentUserFactory else "my"
    assert payload["pageTitle"].startswith(f"Review {subject} ")
    assert [row["name"] for row in payload["results"]] == ["Live feed"]


@ALL_TYPES
def test_list_only_returns_the_requested_organisations_datasets(
    client_factory, dataset_type
):
    organisation = OrganisationFactory()
    user = OrgAdminFactory(organisations=(organisation,))
    _live(organisation, dataset_type, name="Mine")
    _live(OrganisationFactory(), dataset_type, name="Someone else's")

    payload = _get(client_factory, user, dataset_type, organisation.id).json()

    assert [row["name"] for row in payload["results"]] == ["Mine"]


@ALL_TYPES
def test_list_tabs_split_active_inactive_and_draft(client_factory, dataset_type):
    organisation = OrganisationFactory()
    user = OrgAdminFactory(organisations=(organisation,))
    _live(organisation, dataset_type, name="Active")
    _live(organisation, dataset_type, name="Gone", status=FeedStatus.inactive.value)
    DraftDatasetFactory(organisation=organisation, dataset_type=dataset_type)

    def names(tab):
        payload = _get(
            client_factory, user, dataset_type, organisation.id, f"?tab={tab}"
        ).json()
        assert payload["tab"] == tab
        return [row["name"] for row in payload["results"]]

    assert names("active") == ["Active"]
    assert names("archive") == ["Gone"]
    assert len(names("draft")) == 1


@ALL_TYPES
def test_list_unknown_tab_has_no_table_like_django(client_factory, dataset_type):
    organisation = OrganisationFactory()
    user = OrgAdminFactory(organisations=(organisation,))
    _live(organisation, dataset_type, name="Active")

    payload = _get(
        client_factory, user, dataset_type, organisation.id, "?tab=nope"
    ).json()

    assert payload["results"] == []
    assert payload["columns"] == []
    assert payload["count"] == 0


@ALL_TYPES
def test_list_sorts_by_django_tables2_sort_param(client_factory, dataset_type):
    organisation = OrganisationFactory()
    user = OrgAdminFactory(organisations=(organisation,))
    for name in ["b", "c", "a"]:
        _live(organisation, dataset_type, name=name)

    def names(sort):
        payload = _get(
            client_factory, user, dataset_type, organisation.id, f"?sort={sort}"
        ).json()
        assert payload["sort"] == sort
        return [row["name"] for row in payload["results"]]

    assert names("name") == ["a", "b", "c"]
    assert names("-name") == ["c", "b", "a"]


@ALL_TYPES
def test_list_columns_flag_the_sorted_column(client_factory, dataset_type):
    organisation = OrganisationFactory()
    user = OrgAdminFactory(organisations=(organisation,))
    _live(organisation, dataset_type, name="x")

    payload = _get(
        client_factory, user, dataset_type, organisation.id, "?sort=-id"
    ).json()

    columns = {column["key"]: column for column in payload["columns"]}
    assert columns["id"]["direction"] == "desc"
    assert columns["id"]["nextSort"] == "id"
    assert columns["name"]["direction"] is None
    assert columns["name"]["nextSort"] == "name"


def test_list_columns_match_django_tables(client_factory):
    organisation = OrganisationFactory()
    user = OrgAdminFactory(organisations=(organisation,))

    def labels(dataset_type):
        payload = _get(client_factory, user, dataset_type, organisation.id).json()
        return [column["label"] for column in payload["columns"]]

    assert labels(TimetableType) == [
        "Status",
        "Data set name",
        "Data set ID",
        "Last updated",
        "Short description",
    ]
    assert labels(AVLType) == [
        "Status",
        "AVL to Timetable matching",
        "Data feed name",
        "Data feed ID",
        "Last automated update",
        "Short description",
    ]
    assert labels(FaresType) == [
        "Status",
        "Data set name",
        "Data set ID",
        "Last updated",
        "Short description",
    ]


@ALL_TYPES
def test_list_paginates_ten_rows_per_page(client_factory, dataset_type):
    organisation = OrganisationFactory()
    user = OrgAdminFactory(organisations=(organisation,))
    for index in range(12):
        _live(organisation, dataset_type, name=f"feed {index:02}")

    first = _get(
        client_factory, user, dataset_type, organisation.id, "?sort=name"
    ).json()
    second = _get(
        client_factory, user, dataset_type, organisation.id, "?sort=name&page=2"
    ).json()

    assert (first["page"], first["totalPages"], first["count"]) == (1, 2, 12)
    assert first["hasNext"] and not first["hasPrevious"]
    assert len(first["results"]) == 10
    assert second["page"] == 2
    assert not second["hasNext"] and second["hasPrevious"]
    assert [row["name"] for row in second["results"]] == ["feed 10", "feed 11"]


@ALL_TYPES
def test_list_out_of_range_page_clamps_like_django_tables2(
    client_factory, dataset_type
):
    organisation = OrganisationFactory()
    user = OrgAdminFactory(organisations=(organisation,))
    _live(organisation, dataset_type, name="only")

    response = _get(client_factory, user, dataset_type, organisation.id, "?page=9")

    assert response.status_code == 200
    assert response.json()["page"] == 1


def test_row_link_follows_django_feed_name_linkify(client_factory):
    organisation = OrganisationFactory()
    user = OrgAdminFactory(organisations=(organisation,))
    live = _live(organisation, TimetableType, name="Live")
    draft = DraftDatasetFactory(organisation=organisation, dataset_type=TimetableType)

    active = _get(client_factory, user, TimetableType, organisation.id).json()
    drafts = _get(
        client_factory, user, TimetableType, organisation.id, "?tab=draft"
    ).json()

    assert active["results"][0]["link"] == (
        f"/org/{organisation.id}/dataset/timetable/{live.id}/"
    )
    assert drafts["results"][0]["link"] == (
        f"/org/{organisation.id}/dataset/timetable/{draft.id}/review/"
    )


def test_timetable_banner_has_all_three_stats(client_factory):
    organisation = OrganisationFactory()
    user = OrgAdminFactory(organisations=(organisation,))
    ConsumerFeedbackFactory(organisation=organisation)
    SeasonalServiceFactory(licence__organisation=organisation)

    with override_flag("is_operator_prefetch_sra_active", active=False):
        payload = _get(client_factory, user, TimetableType, organisation.id).json()

    assert set(payload["banner"]) == {
        "servicesRequiringAttention",
        "applicableServices",
        "feedbackCount",
        "seasonalServicesCounter",
    }
    assert payload["banner"]["feedbackCount"] == 1
    assert payload["banner"]["seasonalServicesCounter"] == 1


@pytest.mark.parametrize("active", [True, False])
def test_avl_banner_reports_pending_score_and_attention_flag(client_factory, active):
    organisation = OrganisationFactory()
    user = OrgAdminFactory(organisations=(organisation,))

    with override_flag("is_avl_require_attention_active", active=active):
        payload = _get(client_factory, user, AVLType, organisation.id).json()

    banner = payload["banner"]
    assert banner["overallPpcScore"] is None
    assert banner["isAvlRequireAttentionActive"] is active
    assert banner["totalConsumerInteractions"] == 0
    assert {"servicesRequiringAttention", "applicableServices"} <= set(banner)


@pytest.mark.parametrize("active", [True, False])
def test_fares_banner_reports_attention_flag(client_factory, active):
    organisation = OrganisationFactory()
    user = OrgAdminFactory(organisations=(organisation,))

    with override_flag("is_fares_require_attention_active", active=active):
        payload = _get(client_factory, user, FaresType, organisation.id).json()

    banner = payload["banner"]
    assert banner["isFaresRequireAttentionActive"] is active
    assert banner["totalConsumerInteractions"] == 0
    assert {"servicesRequiringAttention", "applicableServices"} <= set(banner)


def test_avl_rows_carry_matching_and_last_checked(client_factory):
    organisation = OrganisationFactory()
    user = OrgAdminFactory(organisations=(organisation,))
    _live(organisation, AVLType, name="Feed")

    payload = _get(client_factory, user, AVLType, organisation.id).json()

    row = payload["results"][0]
    assert row["percentMatching"] == "Pending"
    assert "avlFeedLastChecked" in row
