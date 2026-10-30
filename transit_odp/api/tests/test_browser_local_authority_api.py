import pytest
from django_hosts import reverse
from waffle.testutils import override_flag

from config.hosts import DATA_HOST
from transit_odp.browse.tests.test_views import (
    get_lta_complaint_data_queryset,
    get_lta_list_data,
)
from transit_odp.common.constants import FeatureFlags
from transit_odp.otc.factories import LocalAuthorityFactory, UILtaFactory

pytestmark = pytest.mark.django_db

LIST_URL = "api:browser-local-authority"
DETAIL_URL = "api:browser-local-authority-detail"


def _list_url():
    return reverse(LIST_URL, host=DATA_HOST)


def _detail_url():
    return reverse(DETAIL_URL, host=DATA_HOST)


def test_urls_resolve_on_data_host():
    assert _list_url().endswith("/api/browser/local-authority/")
    assert _detail_url().endswith("/api/browser/local-authority/detail/")


class TestLocalAuthorityListApi:
    def test_is_public_and_returns_first_page(self, data_client):
        get_lta_list_data()

        response = data_client.get(_list_url())

        assert response.status_code == 200
        body = response.json()
        assert body["count"] == 11
        assert body["page"] == 1
        assert body["pageSize"] == 10
        assert body["numPages"] == 2
        assert body["pageRange"] == [1, 2]
        assert len(body["results"]) == 10
        assert body["ordering"] == "ui_lta_name_trimmed"
        assert body["q"] == ""
        names = [item["name"] for item in body["results"]]
        assert names[0] == "Aberdeen City Council"
        assert set(body["results"][0]) == {
            "name",
            "authIds",
            "servicesRequireAttentionPercentage",
        }
        # autocomplete names cover every UI LTA, not only the current page
        assert len(body["names"]) == body["count"]

    def test_second_page(self, data_client):
        get_lta_list_data()

        body = data_client.get(_list_url(), {"page": 2}).json()

        assert body["page"] == 2
        assert len(body["results"]) == body["count"] - 10

    def test_page_out_of_range_is_404(self, data_client):
        get_lta_list_data()

        response = data_client.get(_list_url(), {"page": 99})

        assert response.status_code == 404
        assert "error" in response.json()

    def test_descending_order(self, data_client):
        get_lta_list_data()

        body = data_client.get(_list_url(), {"ordering": "-ui_lta_name_trimmed"}).json()

        names = [item["name"] for item in body["results"]]
        assert names[0] == "Dorset Council"
        # Aberdeen sorts first ascending, so it falls off the first descending page
        assert "Aberdeen City Council" not in names

    def test_invalid_ordering_is_400(self, data_client):
        response = data_client.get(_list_url(), {"ordering": "name"})

        assert response.status_code == 400

    def test_search_filters_by_name(self, data_client):
        get_lta_list_data()

        body = data_client.get(_list_url(), {"q": "christchurch"}).json()

        assert body["q"] == "christchurch"
        assert body["count"] == 1
        assert [item["name"] for item in body["results"]] == [
            "Bournemouth, Christchurch and Poole Council"
        ]
        # Both LocalAuthority rows behind the UI LTA are exposed for the detail link
        assert len(body["results"][0]["authIds"]) == 2

    def test_no_results(self, data_client):
        get_lta_list_data()

        body = data_client.get(_list_url(), {"q": "does not exist"}).json()

        assert body["count"] == 0
        assert body["results"] == []
        assert body["numPages"] == 1

    def test_ltas_without_ui_lta_are_excluded(self, data_client):
        LocalAuthorityFactory(id=1, name="No UI LTA", ui_lta=None)

        body = data_client.get(_list_url()).json()

        assert body["count"] == 0

    @override_flag(FeatureFlags.UILTA_PREFETCH_SRA.value, active=False)
    @override_flag(FeatureFlags.COMPLETE_SERVICE_PAGES.value, active=False)
    def test_percentage_calculated_when_prefetch_flag_off(self, data_client):
        get_lta_complaint_data_queryset()

        body = data_client.get(_list_url()).json()

        assert body["results"][0]["servicesRequireAttentionPercentage"] == 75

    @pytest.mark.parametrize("complete_pages", [True, False])
    @override_flag(FeatureFlags.UILTA_PREFETCH_SRA.value, active=True)
    def test_percentage_uses_prefetched_ui_lta_numbers(
        self, data_client, complete_pages
    ):
        ui_lta = UILtaFactory(
            name="Prefetched Council",
            total_inscope=10,
            timetable_sra=2,
            overall_sra=5,
        )
        LocalAuthorityFactory(id=1, name="Prefetched", ui_lta=ui_lta)

        with override_flag(
            FeatureFlags.COMPLETE_SERVICE_PAGES.value, active=complete_pages
        ):
            body = data_client.get(_list_url()).json()

        expected = 50 if complete_pages else 20
        assert body["results"][0]["servicesRequireAttentionPercentage"] == expected


class TestLocalAuthorityDetailApi:
    @pytest.mark.parametrize("auth_ids", [None, "", "abc", "1,x"])
    def test_missing_or_malformed_auth_ids_is_404(self, data_client, auth_ids):
        params = {} if auth_ids is None else {"auth_ids": auth_ids}

        response = data_client.get(_detail_url(), params)

        assert response.status_code == 404
        assert "error" in response.json()

    def test_unknown_id_is_404(self, data_client):
        response = data_client.get(_detail_url(), {"auth_ids": "9999"})

        assert response.status_code == 404

    def test_is_public(self, data_client):
        get_lta_complaint_data_queryset()

        response = data_client.get(_detail_url(), {"auth_ids": "[1]"})

        assert response.status_code == 200

    @override_flag(FeatureFlags.AVL_REQUIRES_ATTENTION.value, active=False)
    @override_flag(FeatureFlags.FARES_REQUIRE_ATTENTION.value, active=False)
    @override_flag(FeatureFlags.COMPLETE_SERVICE_PAGES.value, active=False)
    @override_flag(FeatureFlags.UILTA_PREFETCH_SRA.value, active=False)
    def test_payload_without_flags(self, data_client):
        get_lta_complaint_data_queryset()

        body = data_client.get(_detail_url(), {"auth_ids": "1"}).json()

        assert body["name"] == "Dorset County Council"
        assert body["authIds"] == "1"
        assert body["isCompleteServicePagesActive"] is False
        assert body["isAvlRequireAttentionActive"] is False
        assert body["isFaresRequireAttentionActive"] is False
        assert body["totalInScopeInSeasonServices"] == 8
        assert body["totalTimetableRecordsRequiringAttention"] == 6
        assert body["servicesRequireAttentionPercentage"] == 75
        assert body["totalServicesRequiringAttention"] is None
        assert body["licences"] == []

    @override_flag(FeatureFlags.AVL_REQUIRES_ATTENTION.value, active=False)
    @override_flag(FeatureFlags.FARES_REQUIRE_ATTENTION.value, active=False)
    @override_flag(FeatureFlags.COMPLETE_SERVICE_PAGES.value, active=True)
    @override_flag(FeatureFlags.UILTA_PREFETCH_SRA.value, active=False)
    def test_payload_with_complete_service_pages(self, data_client):
        get_lta_complaint_data_queryset()

        body = data_client.get(_detail_url(), {"auth_ids": "[1]"}).json()

        assert body["authIds"] == "[1]"
        assert body["isCompleteServicePagesActive"] is True
        assert body["totalServicesRequiringAttention"] == 6
        assert body["totalTimetableRecordsRequiringAttention"] == 6
        assert body["totalLocationRecordsRequiringAttention"] == 0
        assert body["totalFaresRecordsRequiringAttention"] == 0
        assert body["licences"]
        assert {x["licenceNumber"] for x in body["licences"]} == {"PD5000229"}
        licence = body["licences"][0]
        assert set(licence) == {
            "licenceNumber",
            "operatorName",
            "licenceOrganisationId",
            "nonCompliant",
        }

    @override_flag(FeatureFlags.UILTA_PREFETCH_SRA.value, active=True)
    @override_flag(FeatureFlags.COMPLETE_SERVICE_PAGES.value, active=True)
    @override_flag(FeatureFlags.AVL_REQUIRES_ATTENTION.value, active=True)
    @override_flag(FeatureFlags.FARES_REQUIRE_ATTENTION.value, active=True)
    def test_payload_uses_prefetched_numbers(self, data_client):
        ui_lta = UILtaFactory(
            name="Prefetched Council",
            total_inscope=20,
            timetable_sra=4,
            overall_sra=7,
            avl_sra=3,
            fares_sra=2,
        )
        LocalAuthorityFactory(id=1, name="Prefetched", ui_lta=ui_lta)

        body = data_client.get(_detail_url(), {"auth_ids": "1"}).json()

        assert body["name"] == "Prefetched Council"
        assert body["totalInScopeInSeasonServices"] == 20
        assert body["servicesRequireAttentionPercentage"] == 20
        assert body["totalServicesRequiringAttention"] == 7
        assert body["totalTimetableRecordsRequiringAttention"] == 4
        assert body["totalLocationRecordsRequiringAttention"] == 3
        assert body["totalFaresRecordsRequiringAttention"] == 2
        assert body["isAvlRequireAttentionActive"] is True
        assert body["isFaresRequireAttentionActive"] is True

    @override_flag(FeatureFlags.UILTA_PREFETCH_SRA.value, active=True)
    def test_zero_in_scope_services_gives_zero_percent(self, data_client):
        ui_lta = UILtaFactory(name="Empty Council", total_inscope=0, timetable_sra=0)
        LocalAuthorityFactory(id=1, name="Empty", ui_lta=ui_lta)

        body = data_client.get(_detail_url(), {"auth_ids": "1"}).json()

        assert body["servicesRequireAttentionPercentage"] == 0

    def test_post_is_not_allowed(self, data_client):
        assert data_client.post(_detail_url()).status_code == 405
        assert data_client.post(_list_url()).status_code == 405
