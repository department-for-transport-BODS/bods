import pytest
from django_hosts import reverse

from config.hosts import DATA_HOST
from transit_odp.browse.tests.test_avls import TestAVLSearchView
from transit_odp.naptan.models import AdminArea
from transit_odp.organisation.constants import FaresType

pytestmark = pytest.mark.django_db


class TestFaresSearchView(TestAVLSearchView):
    host = DATA_HOST
    url = reverse("search-fares", host=host)
    dataset_type = FaresType
    template_path = "browse/fares/search.html"

    def test_search_filters_admin_area(self, client_factory):
        self.setup_feeds()
        fished_out_admin_area = AdminArea.objects.get(name="A")
        client = client_factory(host=self.host)
        response = client.get(
            self.url,
            data={
                "q": "",
                "area": str(fished_out_admin_area.id),
                "organisation": "",
                "status": "",
                "start": "",
            },
        )

        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        assert response.context_data["object_list"].count() == 2

    def test_multiple_admin_areas_with_lots_of_search_terms(self, client_factory):
        """This test is to protect against regression BODP-1199, geographic
        search misses datasets with multiple admin areas"""

        self.setup_feeds()
        client = client_factory(host=self.host)
        response = client.get(
            self.url,
            data={
                "q": "",
                "area": str(self.admin_areas[3].id),
                "organisation": str(self.organisation2.id),
                "status": "live",
                "start": "2019",
            },
        )

        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        assert response.context_data["object_list"].count() == 2
