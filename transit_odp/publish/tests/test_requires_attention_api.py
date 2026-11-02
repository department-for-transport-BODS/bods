from unittest.mock import patch

import pytest
from waffle.testutils import override_flag

from config import hosts
from transit_odp.common.constants import FeatureFlags
from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.organisation.models.report import ComplianceReport
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import (
    AgentUserFactory,
    OrgAdminFactory,
    OrgStaffFactory,
    UserFactory,
)

pytestmark = pytest.mark.django_db

TIMETABLE = "timetables"
FARES = "fares"
PREFETCH_COMPLIANCE_FLAG = FeatureFlags.PREFETCH_DATABASE_COMPLIANCE_REPORT.value
PREFETCH_SRA_FLAG = FeatureFlags.OPERATOR_PREFETCH_SRA.value

VIEW_MODULES = {
    TIMETABLE: "transit_odp.publish.views.timetable.requires_attention",
    FARES: "transit_odp.fares.views.requires_attention",
}
ATTENTION_COLUMNS = {
    TIMETABLE: "requires_attention",
    FARES: "fares_requires_attention",
}
SRA_COLUMNS = {TIMETABLE: "timetable_sra", FARES: "fares_sra"}
ANCESTORS = {
    TIMETABLE: "Review My Timetables Data",
    FARES: "Review My Fares Data",
}
EXPORT_PATH = "/org/{org_id}/dataset/timetable/{name}/"


def _url(kind, org_id):
    return f"/api/{kind}/requires-attention/{org_id}/"


def _client(client_factory, user):
    client = client_factory(host=hosts.PUBLISH_HOST)
    client.force_login(user=user)
    return client


def _report(org, kind, n, **kwargs):
    values = {
        "registration_number": f"PD000{n:04d}:{n}",
        "service_number": f"L{n:02d}",
        "otc_licence_number": f"PD000{n:04d}",
        "licence_organisation_id": org.id,
        ATTENTION_COLUMNS[kind]: "Yes",
    }
    values.update(kwargs)
    return ComplianceReport.objects.create(**values)


@pytest.fixture
def org():
    return OrganisationFactory(total_inscope=20)


@pytest.fixture
def staff_client(client_factory, org):
    return _client(client_factory, OrgStaffFactory(organisations=(org,)))


@pytest.mark.parametrize("kind", [TIMETABLE, FARES])
class TestRequiresAttentionApi:
    def test_anonymous_user_gets_401(self, client_factory, org, kind):
        client = client_factory(host=hosts.PUBLISH_HOST)

        response = client.get(_url(kind, org.id))

        assert response.status_code == 401
        assert response.json() == {"error": "Authentication required"}

    def test_non_org_user_gets_403(self, client_factory, org, kind):
        user = UserFactory(account_type=AccountType.developer.value)

        response = _client(client_factory, user).get(_url(kind, org.id))

        assert response.status_code == 403

    def test_abods_user_gets_403_like_the_html_view(self, client_factory, org, kind):
        user = UserFactory(account_type=AccountType.abods_user.value)

        response = _client(client_factory, user).get(_url(kind, org.id))

        assert response.status_code == 403

    def test_another_organisation_gets_403(self, client_factory, org, kind):
        other_user = OrgAdminFactory(organisations=(OrganisationFactory(),))

        response = _client(client_factory, other_user).get(_url(kind, org.id))

        assert response.status_code == 403

    def test_post_is_not_allowed(self, staff_client, org, kind):
        assert staff_client.post(_url(kind, org.id)).status_code == 405

    @override_flag(PREFETCH_COMPLIANCE_FLAG, active=True)
    @override_flag(PREFETCH_SRA_FLAG, active=True)
    def test_payload_shape_with_prefetched_data(self, staff_client, org, kind):
        org.timetable_sra = 2
        org.fares_sra = 2
        org.save()
        _report(org, kind, 1)
        _report(org, kind, 2)
        # Not requiring attention, or belonging to another organisation.
        _report(org, kind, 3, **{ATTENTION_COLUMNS[kind]: "No"})
        _report(OrganisationFactory(), kind, 4)

        response = staff_client.get(_url(kind, org.id))

        assert response.status_code == 200
        payload = response.json()
        assert payload["ancestor"] == ANCESTORS[kind]
        assert payload["summary"] == {
            "servicesRequiringAttention": 2,
            "totalInScopeInSeasonServices": 20,
            "percentage": 10,
        }
        assert payload["rows"] == [
            {
                "licenceNumber": "PD0000001",
                "serviceCode": "PD0000001:1",
                "lineNumber": "L01",
            },
            {
                "licenceNumber": "PD0000002",
                "serviceCode": "PD0000002:2",
                "lineNumber": "L02",
            },
        ]
        assert payload["pagination"] == {"currentPage": 1, "totalPages": 1}
        assert payload["query"] == ""
        assert payload["noResults"] is False
        assert "error" not in payload

    @override_flag(PREFETCH_COMPLIANCE_FLAG, active=True)
    @override_flag(PREFETCH_SRA_FLAG, active=True)
    def test_paginates_ten_rows_per_page(self, staff_client, org, kind):
        org.timetable_sra = org.fares_sra = 12
        org.save()
        for n in range(1, 13):
            _report(org, kind, n)

        page_one = staff_client.get(_url(kind, org.id)).json()
        page_two = staff_client.get(_url(kind, org.id), {"page": 2}).json()

        assert len(page_one["rows"]) == 10
        assert page_one["pagination"] == {"currentPage": 1, "totalPages": 2}
        assert [r["lineNumber"] for r in page_two["rows"]] == ["L11", "L12"]
        assert page_two["pagination"] == {"currentPage": 2, "totalPages": 2}

    @override_flag(PREFETCH_COMPLIANCE_FLAG, active=True)
    @override_flag(PREFETCH_SRA_FLAG, active=True)
    @pytest.mark.parametrize("page", ["3", "abc", "0"])
    def test_invalid_page_is_404_like_the_html_view(
        self, staff_client, org, kind, page
    ):
        org.timetable_sra = org.fares_sra = 12
        org.save()
        for n in range(1, 13):
            _report(org, kind, n)

        response = staff_client.get(_url(kind, org.id), {"page": page})

        assert response.status_code == 404
        assert response.json() == {"error": "Invalid page"}

    @override_flag(PREFETCH_COMPLIANCE_FLAG, active=True)
    @override_flag(PREFETCH_SRA_FLAG, active=True)
    @pytest.mark.parametrize("query", ["pd0000002", "PD0000002:2", "l02", "  L02  "])
    def test_search_matches_licence_service_code_and_line(
        self, staff_client, org, kind, query
    ):
        org.timetable_sra = org.fares_sra = 3
        org.save()
        for n in range(1, 4):
            _report(org, kind, n)

        payload = staff_client.get(_url(kind, org.id), {"q": query}).json()

        assert [r["serviceCode"] for r in payload["rows"]] == ["PD0000002:2"]
        assert payload["query"] == query.strip()
        assert payload["noResults"] is False

    @override_flag(PREFETCH_COMPLIANCE_FLAG, active=True)
    @override_flag(PREFETCH_SRA_FLAG, active=True)
    def test_search_without_match_reports_no_results(self, staff_client, org, kind):
        org.timetable_sra = org.fares_sra = 1
        org.save()
        _report(org, kind, 1)

        payload = staff_client.get(_url(kind, org.id), {"q": "nothing"}).json()

        assert payload["rows"] == []
        assert payload["noResults"] is True
        assert payload["pagination"] == {"currentPage": 1, "totalPages": 1}
        assert payload["summary"]["servicesRequiringAttention"] == 1

    @override_flag(PREFETCH_COMPLIANCE_FLAG, active=True)
    @override_flag(PREFETCH_SRA_FLAG, active=True)
    def test_empty_state_when_nothing_requires_attention(self, staff_client, org, kind):
        payload = staff_client.get(_url(kind, org.id)).json()

        assert payload["rows"] == []
        assert payload["noResults"] is True
        assert payload["summary"] == {
            "servicesRequiringAttention": 0,
            "totalInScopeInSeasonServices": 20,
            "percentage": 0,
        }

    @override_flag(PREFETCH_COMPLIANCE_FLAG, active=True)
    @override_flag(PREFETCH_SRA_FLAG, active=True)
    def test_zero_in_scope_services_gives_zero_percent(self, client_factory, kind):
        org = OrganisationFactory(total_inscope=0)
        client = _client(client_factory, OrgStaffFactory(organisations=(org,)))

        payload = client.get(_url(kind, org.id)).json()

        assert payload["summary"]["percentage"] == 0

    @override_flag(PREFETCH_COMPLIANCE_FLAG, active=False)
    @override_flag(PREFETCH_SRA_FLAG, active=False)
    def test_live_calculation_when_prefetch_flags_are_off(
        self, staff_client, org, kind
    ):
        rows = [
            {
                "licence_number": "PD0000009",
                "service_code": "PD0000009:9",
                "line_number": "9A",
            },
            {
                "licence_number": "PD0000010",
                "service_code": "PD0000010:10",
                "line_number": "10",
            },
        ]
        getter = (
            "get_requires_attention_line_level_data"
            if kind == TIMETABLE
            else "FaresRequiresAttention"
        )
        module = VIEW_MODULES[kind]

        with patch(f"{module}.{getter}") as source, patch(
            f"{module}.get_in_scope_in_season_services_line_level",
            return_value=[object()] * 8,
        ):
            if kind == TIMETABLE:
                source.return_value = rows
            else:
                source.return_value.get_fares_requires_attention_line_level_data.return_value = (  # noqa: E501
                    rows
                )
            payload = staff_client.get(_url(kind, org.id)).json()

        assert payload["summary"] == {
            "servicesRequiringAttention": 2,
            "totalInScopeInSeasonServices": 8,
            "percentage": 25,
        }
        assert [r["lineNumber"] for r in payload["rows"]] == ["9A", "10"]
        assert payload["noResults"] is False

    @override_flag("is_avl_require_attention_active", active=True)
    def test_agent_user_sees_organisation_name_in_ancestor(
        self, client_factory, org, kind
    ):
        agent = AgentUserFactory(organisations=(org,))

        payload = _client(client_factory, agent).get(_url(kind, org.id)).json()

        data_type = "Timetables" if kind == TIMETABLE else "Fares"
        assert payload["ancestor"] == f"Review {org.name} {data_type} Data"


@pytest.mark.parametrize(
    ("avl_flag", "expected"),
    [(True, "compliance-report"), (False, "service-codes")],
)
def test_timetable_export_path_depends_on_avl_attention_flag(
    staff_client, org, avl_flag, expected
):
    with override_flag("is_avl_require_attention_active", active=avl_flag):
        payload = staff_client.get(_url(TIMETABLE, org.id)).json()

    assert payload["exportPath"] == EXPORT_PATH.format(org_id=org.id, name=expected)


@pytest.mark.parametrize("avl_flag", [True, False])
def test_fares_export_path_is_always_the_compliance_report(staff_client, org, avl_flag):
    with override_flag("is_avl_require_attention_active", active=avl_flag):
        payload = staff_client.get(_url(FARES, org.id)).json()

    assert payload["exportPath"] == EXPORT_PATH.format(
        org_id=org.id, name="compliance-report"
    )
