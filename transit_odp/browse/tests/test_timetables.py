import pytest
from django_hosts import reverse

from config.hosts import DATA_HOST
from transit_odp.browse.tests.test_fares import TestFaresSearchView
from transit_odp.organisation.constants import TimetableType

pytestmark = pytest.mark.django_db


class TestTimeTableSearchView(TestFaresSearchView):
    host = DATA_HOST
    url = reverse("search", host=host)
    dataset_type = TimetableType
    template_path = "browse/timetables/search.html"

    @pytest.mark.parametrize(
        "dateformat",
        ["2030", "2030/12/25", "25th Dec 2030", "12/25/2030", "12-25-2030"],
    )
    def test_search_filters_start(self, client_factory, dateformat):
        self.setup_feeds()
        client = client_factory(host=self.host)
        response = client.get(
            self.url,
            data={
                "q": "",
                "area": "",
                "organisation": "",
                "status": "",
                "start": dateformat,
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
            },
        )

        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        error_message = response.context_data["filter"].errors["start"][0]
        assert error_message == "Timetable start date not in correct format"

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
                "start": "13 oct 2019",
            },
        )

        translated_query_params = response.context_data["query_params"]

        assert response.status_code == 200
        assert translated_query_params["start"] == "13/10/19"
        assert translated_query_params["area"] == admin_area.name
        assert translated_query_params["status"] == "Published"
        assert translated_query_params["organisation"] == self.organisation1.name
