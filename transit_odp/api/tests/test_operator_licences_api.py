import datetime
from unittest import mock

import pytest
from waffle.testutils import override_flag

from transit_odp.common.constants import FeatureFlags
from transit_odp.organisation.constants import TimetableType
from transit_odp.organisation.factories import (
    DatasetFactory,
    LicenceFactory,
    OrganisationFactory,
)
from transit_odp.organisation.models.report import ComplianceReport
from transit_odp.otc.factories import LicenceModelFactory, UILtaFactory
from transit_odp.timetables.tests.test_line_detail_api import (
    LINE_NAME,
    SERVICE_CODE,
    build_line,
)
from transit_odp.transmodel.models import BookingArrangements

pytestmark = pytest.mark.django_db

TODAY = datetime.date.today()
PREFETCH = FeatureFlags.PREFETCH_DATABASE_COMPLIANCE_REPORT.value
COMPLETE_PAGES = FeatureFlags.COMPLETE_SERVICE_PAGES.value
REAL_TIME = FeatureFlags.COMPLETE_SERVICE_PAGES_REAL_TIME_DATA.value
AVL_RA = FeatureFlags.AVL_REQUIRES_ATTENTION.value
FARES_RA = FeatureFlags.FARES_REQUIRE_ATTENTION.value
VISUALISER = "is_timetable_visualiser_active"
SPECIFIC_FEEDBACK = "is_specific_feedback"
LICENCE = "PD0000042"


def detail_url(number):
    return f"/api/browser/operators/licence/{number}/"


def line_url(number):
    return f"/api/browser/operators/licence/{number}/line/details/"


def report(**overrides):
    values = {
        "registration_number": f"{LICENCE}/1",
        "service_number": "1",
        "otc_licence_number": LICENCE,
        "scope_status": "In Scope",
        "seasonal_status": "In Season",
        "overall_requires_attention": "No",
        "requires_attention": "No",
        "avl_requires_attention": "No",
        "fares_requires_attention": "No",
        "local_authorities_ids": [],
        "licence_organisation_id": None,
        "licence_organisation_name": None,
    }
    values.update(overrides)
    return ComplianceReport.objects.create(**values)


class TestLicenceDetail:
    def test_unknown_licence_is_404(self, data_client):
        response = data_client.get(detail_url("PD9999999"))

        assert response.status_code == 404
        assert response.json() == {"error": "Licence not found"}

    def test_post_is_not_allowed(self, data_client):
        LicenceModelFactory(number=LICENCE)

        assert data_client.post(detail_url(LICENCE)).status_code == 405

    @override_flag(PREFETCH, active=True)
    def test_prefetched_services_and_filters(self, data_client):
        LicenceModelFactory(number=LICENCE)
        organisation = OrganisationFactory(name="Alpha Travel")
        LicenceFactory(number=LICENCE, organisation=organisation)
        lta_a = UILtaFactory(name="Alpha LTA")
        lta_b = UILtaFactory(name="Beta LTA")
        report(
            registration_number=f"{LICENCE}/2",
            service_number="20",
            local_authorities_ids=[str(lta_b.id)],
            requires_attention="Yes",
            overall_requires_attention="Yes",
            licence_organisation_id=organisation.id,
        )
        report(
            service_number="10",
            local_authorities_ids=[str(lta_a.id), str(lta_b.id)],
            scope_status="Out of Scope",
            seasonal_status="Out of Season",
            avl_requires_attention="Yes",
            fares_requires_attention="Yes",
            licence_organisation_id=organisation.id,
        )
        # A different licence is not listed.
        report(otc_licence_number="PD0000999", registration_number="PD0000999/1")

        response = data_client.get(detail_url(LICENCE))

        assert response.status_code == 200
        payload = response.json()
        assert payload["licenceNumber"] == LICENCE
        assert payload["organisationId"] == organisation.id
        assert payload["organisationName"] == "Alpha Travel"
        assert payload["isPrefetchComplianceReportActive"] is True
        assert payload["hasFranchise"] is False
        assert payload["hasNullLocalAuthority"] is False
        assert {item["id"]: item["name"] for item in payload["localAuthorities"]} == {
            lta_a.id: "Alpha LTA",
            lta_b.id: "Beta LTA",
        }
        assert payload["operators"] == [{"id": organisation.id, "name": "Alpha Travel"}]
        # Sorted by "<service number> - <registration number>", slash kept for display.
        assert [s["fullRegistrationNumber"] for s in payload["services"]] == [
            f"10 - {LICENCE}/1",
            f"20 - {LICENCE}/2",
        ]
        first, second = payload["services"]
        # ...but the registration number used in links has "/" replaced by ":".
        assert first["registrationNumber"] == f"{LICENCE}:1"
        assert first["serviceNumber"] == "10"
        assert first["localAuthorityIds"] == f"{lta_a.id},{lta_b.id}"
        assert first["licenceOrganisationId"] == organisation.id
        assert first["isInScope"] is False
        assert first["isInSeason"] is False
        assert first["requiresAttention"] is False
        assert first["avlRequiresAttention"] is True
        assert first["faresRequiresAttention"] is True
        assert second["isInScope"] is True
        assert second["isInSeason"] is True
        assert second["requiresAttention"] is True

    @override_flag(PREFETCH, active=True)
    def test_licence_without_organisation(self, data_client):
        LicenceModelFactory(number=LICENCE)
        report()

        payload = data_client.get(detail_url(LICENCE)).json()

        assert payload["organisationId"] is None
        assert payload["organisationName"] == "Organisation not yet created"

    @override_flag(PREFETCH, active=True)
    def test_service_without_local_authority_is_flagged(self, data_client):
        LicenceModelFactory(number=LICENCE)
        report(local_authorities_ids=None)

        payload = data_client.get(detail_url(LICENCE)).json()

        assert payload["hasNullLocalAuthority"] is True
        assert payload["localAuthorities"] == []
        assert payload["services"][0]["localAuthorityIds"] == ""

    @override_flag(PREFETCH, active=True)
    def test_org_id_query_parameter_is_ignored_like_django(self, data_client):
        LicenceModelFactory(number=LICENCE)
        owner = OrganisationFactory(name="Owner")
        LicenceFactory(number=LICENCE, organisation=owner)
        other = OrganisationFactory(name="Other", is_franchise=True)
        report(licence_organisation_id=other.id)
        report(registration_number=f"{LICENCE}/2", service_number="2")

        payload = data_client.get(detail_url(LICENCE), {"org_id": other.id}).json()

        # The HTML view reads org_id from URL kwargs, never the query string.
        assert payload["organisationId"] == owner.id
        assert len(payload["services"]) == 2

    @override_flag(PREFETCH, active=False)
    def test_legacy_services_without_prefetched_report(self, data_client):
        LicenceModelFactory(number=LICENCE)

        payload = data_client.get(detail_url(LICENCE)).json()

        assert payload["isPrefetchComplianceReportActive"] is False
        assert payload["services"] == []
        assert payload["localAuthorities"] == []
        assert payload["franchises"] == []
        assert payload["operators"] == []


def build_live_line(**dataset_kwargs):
    dataset = DatasetFactory(dataset_type=TimetableType, **dataset_kwargs)
    build_line(dataset.live_revision)
    return dataset


class TestLicenceLineDetail:
    def params(self, **overrides):
        params = {"line": LINE_NAME, "service": SERVICE_CODE}
        params.update(overrides)
        return params

    def test_is_public_and_post_is_not_allowed(self, data_client):
        assert data_client.get(line_url(LICENCE), self.params()).status_code == 200
        assert data_client.post(line_url(LICENCE)).status_code == 405

    def test_unknown_service_renders_empty_state_like_django(self, data_client):
        payload = data_client.get(line_url("PD9999999"), self.params()).json()

        assert payload["licenceNumber"] == "PD9999999"
        assert payload["lineName"] == LINE_NAME
        assert payload["serviceCode"] == SERVICE_CODE
        assert payload["organisation"] is None
        assert payload["datasetId"] is None
        assert payload["revisionId"] is None
        assert payload["serviceType"] == "N/A"
        assert payload["isLicencePage"] is True
        assert payload["timetable"] is None
        # Compliance values are only computed with a live revision.
        assert payload["serviceInScope"] is None
        assert payload["isAvlCompliant"] is None

    def test_organisation_comes_from_the_licence(self, data_client):
        organisation = OrganisationFactory(name="Alpha Travel")
        LicenceFactory(number=LICENCE, organisation=organisation)

        payload = data_client.get(line_url(LICENCE), self.params()).json()

        assert payload["organisation"] == {
            "id": organisation.id,
            "name": "Alpha Travel",
        }

    @pytest.mark.parametrize("pf", ["1", "0", "anything"])
    def test_passenger_facing_flag_hides_licence_page_content(self, data_client, pf):
        payload = data_client.get(line_url(LICENCE), self.params(pf=pf)).json()

        # Django uses bool(GET.get("pf", 0)) so even "0" is passenger facing.
        assert payload["isLicencePage"] is False

    @override_flag(COMPLETE_PAGES, active=False)
    @override_flag(REAL_TIME, active=False)
    @override_flag(AVL_RA, active=False)
    @override_flag(FARES_RA, active=False)
    @override_flag(VISUALISER, active=False)
    @override_flag(SPECIFIC_FEEDBACK, active=False)
    def test_live_dataset_returns_service_type_and_dataset(self, data_client):
        dataset = build_live_line()

        payload = data_client.get(line_url(LICENCE), self.params()).json()

        assert payload["datasetId"] == dataset.id
        assert payload["revisionId"] == dataset.live_revision_id
        assert payload["serviceType"] == "Standard"
        assert payload["bookingArrangements"] is None
        assert payload["bookingMethods"] is None
        assert payload["flags"] == {
            "isCompleteServicePagesActive": False,
            "isCompleteServicePagesRealTimeDataActive": False,
            "isAvlRequireAttentionActive": False,
            "isFaresRequireAttentionActive": False,
            "isTimetableVisualiserActive": False,
            "isSpecificFeedback": False,
        }
        assert payload["timetable"] is None

    def test_flexible_booking_methods_follow_django_template_mapping(self, data_client):
        dataset = DatasetFactory(dataset_type=TimetableType)
        service, _, _ = build_line(dataset.live_revision, service_type="flexible")
        BookingArrangements.objects.create(
            service=service,
            description="Call ahead",
            email=None,
            phone_number="0123",
            web_address="https://book.example.com",
        )

        payload = data_client.get(line_url(LICENCE), self.params()).json()

        assert payload["serviceType"] == "Flexible"
        assert payload["bookingArrangements"] == "Call ahead"
        assert payload["bookingMethods"] == {
            "phone": "0123",
            "email": "None",
            "url": None,
        }

    @override_flag(VISUALISER, active=True)
    @override_flag(SPECIFIC_FEEDBACK, active=True)
    def test_timetable_visualiser_is_serialised_from_the_view_context(
        self, data_client
    ):
        build_live_line()

        payload = data_client.get(
            line_url(LICENCE), self.params(date=TODAY.isoformat())
        ).json()

        assert payload["flags"]["isTimetableVisualiserActive"] is True
        assert payload["flags"]["isSpecificFeedback"] is True
        timetable = payload["timetable"]
        assert timetable["currDate"] == TODAY.isoformat()
        assert timetable["isTimetableInfoAvailable"] is True
        outbound, inbound = timetable["directions"]
        assert outbound["direction"] == "outbound"
        assert outbound["journeyName"] == "Outbound - Town - Station"
        assert outbound["isEmpty"] is False
        assert len(outbound["rows"]) == 3
        assert len(outbound["columns"]) == 3  # stop column + two journeys
        assert inbound["isEmpty"] is True
        assert payload["outboundStartAndEnd"] == "Town - Station"
        assert payload["realTime"]["vehicleJourneyCodes"]

    @override_flag(VISUALISER, active=True)
    def test_timetable_visualiser_without_live_revision_has_no_timetable(
        self, data_client
    ):
        payload = data_client.get(line_url(LICENCE), self.params()).json()

        assert payload["flags"]["isTimetableVisualiserActive"] is True
        assert payload["timetable"] is None
        assert payload["outboundStartAndEnd"] is None

    @override_flag(COMPLETE_PAGES, active=True)
    @override_flag(REAL_TIME, active=True)
    @override_flag(AVL_RA, active=True)
    @override_flag(FARES_RA, active=True)
    def test_complete_service_pages_compliance(self, data_client):
        dataset = build_live_line()
        activity_path = (
            "transit_odp.browse.views.operators."
            "get_vehicle_activity_operatorref_linename"
        )
        with mock.patch(activity_path) as activity, mock.patch(
            "transit_odp.browse.views.operators.AbodsRegistery"
        ) as registry:
            import pandas as pd

            activity.return_value = pd.DataFrame(columns=["OperatorRef", "LineRef"])
            registry.return_value.records.return_value = []

            payload = data_client.get(line_url(LICENCE), self.params()).json()

        flags = payload["flags"]
        assert flags["isCompleteServicePagesActive"] is True
        assert flags["isCompleteServicePagesRealTimeDataActive"] is True
        assert flags["isAvlRequireAttentionActive"] is True
        assert flags["isFaresRequireAttentionActive"] is True
        # No OTC service is registered, so the service counts as in scope/season.
        assert payload["serviceInScope"] is True
        assert payload["serviceInSeason"] is True
        # The synced-in-last-month AVL list is empty, so AVL is not compliant.
        assert payload["isAvlCompliant"] is False
        assert payload["isFaresCompliant"] is False
        assert payload["isTimetableCompliant"] is False
        assert payload["fares"]["datasetId"] is None
        assert payload["fares"]["validFiles"] == []
        assert payload["timetableFiles"]["datasetId"] == dataset.id
        files = payload["timetableFiles"]["validFiles"]
        assert [file["filename"] for file in files] == ["line-42.xml"]
        assert files[0]["startDate"] and files[0]["endDate"]
        assert payload["timetableFiles"]["futureDatedFiles"] == []
        assert payload["timetableFiles"]["expiredFiles"] == []
        assert payload["realTime"]["nationalOperatorCode"]
