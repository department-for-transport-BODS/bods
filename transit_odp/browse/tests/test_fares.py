import pytest
from django_hosts import reverse

from config.hosts import DATA_HOST
from transit_odp.browse.tests.test_avls import (
    BaseAVLSearchView,
    TestUserAVLFeedbackView,
)
from transit_odp.naptan.models import AdminArea
from transit_odp.organisation.constants import FaresType, FeedStatus
from transit_odp.organisation.factories import (
    DatasetRevisionFactory,
    FaresDatasetRevisionFactory,
    OrganisationFactory,
)
from transit_odp.organisation.models import Dataset
from transit_odp.users.constants import OrgAdminType, SiteAdminType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestFaresSearchView(BaseAVLSearchView):
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

    def test_search_no_filters(self, client_factory):
        """
        This is overriding the base AVL test as error is a "viewable" avl status but
        not valid for Fares/Timetables
        """
        self.setup_feeds()
        client = client_factory(host=self.host)
        response = client.get(self.url)
        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        # no filtering; so display all published live
        assert response.context_data["object_list"].count() == 4

    def test_search_no_filters_inactive_org(self, client_factory):
        self.setup_feeds()
        inactive_organisation = OrganisationFactory(is_active=False)
        DatasetRevisionFactory.create_batch(
            4,
            dataset__organisation=inactive_organisation,
            status=FeedStatus.live.value,
            is_published=True,
        )
        client = client_factory(host=self.host)
        response = client.get(self.url)

        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        assert response.context_data["object_list"].count() == 4

    def test_ordering(self, client_factory):
        self.setup_feeds()
        qs = Dataset.objects.get_viewable_statuses().add_live_data().order_by("-name")
        client = client_factory(host=self.host)
        response = client.get(
            self.url,
            data={"ordering": "-name", "publisher": self.organisation1.id},
        )

        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        assert list(response.context_data["object_list"]) == list(qs)


class TestUserFaresFeedbackView(TestUserAVLFeedbackView):
    view_name = "fares-feed-feedback"

    @pytest.fixture()
    def revision(self):
        org = OrganisationFactory()
        UserFactory(account_type=SiteAdminType)
        publisher = UserFactory(account_type=OrgAdminType, organisations=(org,))
        return FaresDatasetRevisionFactory(
            dataset__contact=publisher,
            status=FeedStatus.live.value,
            last_modified_user=publisher,
            published_by=publisher,
            dataset__organisation=org,
        )
