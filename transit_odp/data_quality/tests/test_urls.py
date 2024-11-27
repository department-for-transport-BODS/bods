import pytest
from typing import NamedTuple

from django.conf import settings
from django.urls import resolve
from django.views import View
from django_hosts.resolvers import reverse

import config.hosts
from transit_odp.data_quality import views


# define named tuples for clarity about scenario format required by each test method
class UrlNameScenario(NamedTuple):
    url_path: str
    url_name: str
    view_kwargs: dict


class UrlResolvesViewScenario(NamedTuple):
    url_path: str
    view: View


# TODO: ideally use built in pytest functionality like parametrize -- didn't initially
# have much success combining
# class inheritance and parametrize, leading to the "scenarios" loop in the test methods
class DqUrlsTestBase:
    """
    Base class for testing Data Quality urls.

    Don't prefix with "Test" (e.g. TestDqUrlsBase) to ensure that pytest doesn't run
    this base class.

    Override the get_url_name_scenarios() and
    get_url_resolves_to_correct_view_scenarios() methods as needed. See
    WarningUrlsTestBase for an example.
    """

    # all DQ pages hang off /dataset/<pk>/
    dataset_id = 1
    org_id = 1
    report_id = 1
    url_segment = ""

    def test_url_name(self):
        """Test that the specified url name(s) correspond to the expected url path"""
        scenarios = self.get_url_name_scenarios()

        for scenario in scenarios:
            assert scenario.url_path in reverse(
                scenario.url_name,
                kwargs=scenario.view_kwargs,
                host=config.hosts.PUBLISH_HOST,
            )

    def test_url_resolves_to_correct_view(self):
        """Test that list and detail url paths resolve to the expected views"""
        scenarios = self.get_url_resolves_to_correct_view_scenarios()

        for scenario in scenarios:
            resolver = resolve(scenario.url_path, urlconf=settings.PUBLISH_URLCONF)
            # "class-based views need to be compared by name, as the functions
            # generated by as_view() won't be equal"
            # https://docs.djangoproject.com/en/2.2/topics/testing/tools/
            # #django.test.Response.resolver_match
            assert resolver.func.__name__ == scenario.view.as_view().__name__

    def get_url_name_scenarios(self):
        raise NotImplementedError(
            "Method must be overriden with scenarios for your test"
        )

    def get_url_resolves_to_correct_view_scenarios(self):
        raise NotImplementedError(
            "Method must be overriden with scenarios for your test"
        )

    def generate_dq_base_url_path(self):
        return (
            f"/org/{self.org_id}/dataset/timetable/{self.dataset_id}"
            f"/report/{self.report_id}/"
        )


class WarningUrlsTestBase(DqUrlsTestBase):
    """
    Base class for testing warnings that have a list and detail page.

    Don't prefix with "Test" (e.g. TestWarningUrlsBase) to ensure that pytest doesn't
    run this base class
    """

    warning_id = "90f6f112-14d6-4a8f-bca0-8ae891f9d184"  # generated using uuid.uuid4()
    list_url_name = ""
    list_view = None
    detail_url_name = ""
    detail_view = None

    def get_url_name_scenarios(self):
        return (
            UrlNameScenario(
                self.generate_list_url_path(),
                self.list_url_name,
                {
                    "pk": self.dataset_id,
                    "pk1": self.org_id,
                    "report_id": self.report_id,
                },
            ),
            UrlNameScenario(
                self.generate_detail_url_path(),
                self.detail_url_name,
                {
                    "pk": self.dataset_id,
                    "warning_pk": self.warning_id,
                    "pk1": self.org_id,
                    "report_id": self.report_id,
                },
            ),
        )

    def get_url_resolves_to_correct_view_scenarios(self):
        return (
            UrlResolvesViewScenario(self.generate_list_url_path(), self.list_view),
            UrlResolvesViewScenario(self.generate_detail_url_path(), self.detail_view),
        )

    # helper functions
    def generate_list_url_path(self):
        return f"{self.generate_dq_base_url_path()}{self.url_segment}/"

    def generate_detail_url_path(self):
        return f"{self.generate_list_url_path()}{self.warning_id}/"


@pytest.mark.django_db
class TestReportOverviewUrl(DqUrlsTestBase):
    url_segment = ""
    url_name = "dq:overview"
    view = views.ReportOverviewView

    def get_url_name_scenarios(self):
        return (
            UrlNameScenario(
                self.generate_dq_base_url_path(),
                self.url_name,
                {
                    "pk": self.dataset_id,
                    "pk1": self.org_id,
                    "report_id": self.report_id,
                },
            ),
        )

    def get_url_resolves_to_correct_view_scenarios(self):
        return (UrlResolvesViewScenario(self.generate_dq_base_url_path(), self.view),)


@pytest.mark.django_db
class TestGlossaryUrl(DqUrlsTestBase):
    url_segment = "glossary/"
    url_name = "dq:glossary"
    view = views.DataQualityGlossaryView

    def get_url_name_scenarios(self):
        return (
            UrlNameScenario(
                f"{self.generate_dq_base_url_path()}{self.url_segment}",
                self.url_name,
                {
                    "pk": self.dataset_id,
                    "pk1": self.org_id,
                    "report_id": self.report_id,
                },
            ),
        )

    def get_url_resolves_to_correct_view_scenarios(self):
        return (
            UrlResolvesViewScenario(
                f"{self.generate_dq_base_url_path()}{self.url_segment}", self.view
            ),
        )


@pytest.mark.django_db
class TestSlowTimingWarningUrls(WarningUrlsTestBase):
    url_segment = "slow-timings"
    list_url_name = "dq:slow-timings-list"
    list_view = views.SlowTimingsListView
    detail_url_name = "dq:slow-timings-detail"
    detail_view = views.SlowTimingsDetailView


@pytest.mark.django_db
class TestDuplicateJourneyWarningUrls(WarningUrlsTestBase):
    url_segment = "duplicate-journeys"
    list_url_name = "dq:duplicate-journey-list"
    list_view = views.DuplicateJourneyListView
    detail_url_name = "dq:duplicate-journey-detail"
    detail_view = views.DuplicateJourneyDetailView


@pytest.mark.django_db
class TestIncorrectNOCWarningUrls(WarningUrlsTestBase):
    url_segment = "incorrect-noc"
    list_url_name = "dq:incorrect-noc-list"
    list_view = views.IncorrectNOCListView
    detail_url_name = ""
    detail_view = None

    # Incorrect NOC warning only has list page (not detail page), so re-implement the
    # scenario methods
    def get_url_name_scenarios(self):
        return (
            UrlNameScenario(
                self.generate_list_url_path(),
                self.list_url_name,
                {
                    "pk": self.dataset_id,
                    "pk1": self.org_id,
                    "report_id": self.report_id,
                },
            ),
        )

    def get_url_resolves_to_correct_view_scenarios(self):
        return (UrlResolvesViewScenario(self.generate_list_url_path(), self.list_view),)


@pytest.mark.django_db
class TestLastStopPickUpWarningUrls(WarningUrlsTestBase):
    url_segment = "pick-up-only"
    list_url_name = "dq:last-stop-pick-up-only-list"
    list_view = views.LastStopPickUpListView
    detail_url_name = "dq:last-stop-pick-up-only-detail"
    detail_view = views.LastStopPickUpDetailView


@pytest.mark.django_db
class TestFirstStopDropOffWarningUrls(WarningUrlsTestBase):
    url_segment = "drop-off-only"
    list_url_name = "dq:first-stop-set-down-only-list"
    list_view = views.FirstStopDropOffListView
    detail_url_name = "dq:first-stop-set-down-only-detail"
    detail_view = views.FirstStopDropOffDetailView


@pytest.mark.django_db
class TestLastStopNotTimingPointWarningUrls(WarningUrlsTestBase):
    url_segment = "last-stop-not-timing-point"
    list_url_name = "dq:last-stop-not-timing-point-list"
    list_view = views.LastStopNotTimingListView
    detail_url_name = "dq:last-stop-not-timing-point-detail"
    detail_view = views.LastStopNotTimingDetailView


@pytest.mark.django_db
class TestFirstStopNotTimingPointWarningUrls(WarningUrlsTestBase):
    url_segment = "first-stop-not-timing-point"
    list_url_name = "dq:first-stop-not-timing-point-list"
    list_view = views.FirstStopNotTimingListView
    detail_url_name = "dq:first-stop-not-timing-point-detail"
    detail_view = views.FirstStopNotTimingDetailView


@pytest.mark.django_db
class TestStopRepeatedWarningUrls(WarningUrlsTestBase):
    url_segment = "multiple-stops"
    list_url_name = "dq:stop-repeated-list"
    list_view = views.StopRepeatedListView
    detail_url_name = "dq:stop-repeated-detail"
    detail_view = views.StopRepeatedDetailView


@pytest.mark.django_db
class TestMissingStopWarningUrls(WarningUrlsTestBase):
    url_segment = "missing-stops"
    list_url_name = "dq:missing-stops-list"
    list_view = views.MissingStopListView
    detail_url_name = "dq:missing-stops-detail"
    detail_view = views.MissingStopDetailView


@pytest.mark.django_db
class TestBackwardDateRangeWarningUrls(WarningUrlsTestBase):
    url_segment = "backward-date-range"
    list_url_name = "dq:backward-date-range-list"
    list_view = views.BackwardDateRangeListView
    detail_url_name = "dq:backward-date-range-detail"
    detail_view = views.BackwardDateRangeDetailView
