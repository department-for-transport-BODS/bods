import pytest
from django_hosts import reverse
from freezegun import freeze_time

from config.hosts import DATA_HOST
from transit_odp.browse.tests.test_avls import TestUserAVLFeedbackView
from transit_odp.browse.tests.test_fares import TestFaresSearchView
from transit_odp.data_quality.factories.report import PTIObservationFactory
from transit_odp.organisation.constants import FeedStatus, TimetableType
from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetRevisionFactory,
    OrganisationFactory,
)
from transit_odp.users.constants import OrgAdminType, SiteAdminType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestTimeTableSearchView(TestFaresSearchView):
    host = DATA_HOST
    url = reverse("search", host=host)
    dataset_type = TimetableType
    template_path = "browse/timetables/search.html"

    def test_search_filters_start(self, client_factory):
        self.setup_feeds()
        client = client_factory(host=self.host)
        response = client.get(
            self.url,
            data={
                "q": "",
                "area": "",
                "organisation": "",
                "status": "",
                "start": "2030-12-25",
            },
        )

        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        assert response.context_data["object_list"].count() == 2

    def test_bad_start_time(self, client_factory):
        self.setup_feeds()
        client = client_factory(host=self.host)
        response = client.get(
            self.url,
            data={
                "q": "",
                "area": "",
                "organisation": "",
                "status": "",
                "start": "silly rabbit, this isnt a time",
                "published_at": "",
            },
        )

        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        error_message = response.context_data["filter"].errors["start"][0]
        assert error_message == "Timetable start date not in correct format"

    def test_bad_published_at_time(self, client_factory):
        self.setup_feeds()
        client = client_factory(host=self.host)
        response = client.get(
            self.url,
            data={
                "q": "",
                "area": "",
                "organisation": "",
                "status": "",
                "start": "",
                "published_at": "silly rabbit, this isnt a time",
            },
        )

        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        error_message = response.context_data["filter"].errors["published_at"][0]
        assert error_message == "Timetable last updated not in correct format"

    def test_query_params_are_human_readable_in_context(self, client_factory):
        self.setup_feeds()
        admin_area = self.admin_areas[0]
        client = client_factory(host=self.host)
        response = client.get(
            self.url,
            data={
                "q": "ignore me",
                "area": str(admin_area.id),
                "organisation": str(self.organisation1.id),
                "status": "live",
                "start": "2019-10-13",
                "published_at": "3019-10-13",
            },
        )

        translated_query_params = response.context_data["query_params"]

        assert response.status_code == 200
        assert translated_query_params["start"] == "13/10/19"
        assert translated_query_params["published_at"] == "13/10/19"
        assert translated_query_params["area"] == admin_area.name
        assert translated_query_params["status"] == "Published"
        assert translated_query_params["organisation"] == self.organisation1.name

    @pytest.mark.parametrize(
        "is_pti_compliant,expected_results", (("True", 5), ("False", 4), ("", 9))
    )
    def test_can_search_using_bods_compliance(
        self, client_factory, is_pti_compliant, expected_results
    ):
        self.setup_feeds()
        for dataset in DatasetFactory.create_batch(4):
            PTIObservationFactory(revision=dataset.live_revision)

        client = client_factory(host=self.host)
        response = client.get(
            self.url,
            data={
                "q": "",
                "area": "",
                "organisation": "",
                "status": "",
                "start": "",
                "published_at": "",
                "is_pti_compliant": is_pti_compliant,
            },
        )
        assert response.context_data["object_list"].count() == expected_results

    @freeze_time("19-11-2021")
    def test_search_filters_published_at(self, client_factory):
        self.setup_feeds()
        client = client_factory(host=self.host)
        response = client.get(
            self.url,
            data={
                "q": "",
                "area": "",
                "organisation": "",
                "status": "",
                "start": "",
                "published_at": "2021-11-19",
            },
        )

        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        assert response.context_data["object_list"].count() == 5


class TestUserTimetableFeedbackView(TestUserAVLFeedbackView):
    view_name = "feed-feedback"

    @pytest.fixture()
    def revision(self):
        org = OrganisationFactory()
        UserFactory(account_type=SiteAdminType)
        publisher = UserFactory(account_type=OrgAdminType, organisations=(org,))
        return DatasetRevisionFactory(
            dataset__contact=publisher,
            status=FeedStatus.live.value,
            last_modified_user=publisher,
            published_by=publisher,
            dataset__organisation=org,
        )
