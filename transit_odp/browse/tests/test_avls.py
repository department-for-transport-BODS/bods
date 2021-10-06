import datetime

import pytest
from django.conf import settings
from django_hosts import reverse

from config.hosts import DATA_HOST
from transit_odp.browse.forms import UserFeedbackForm
from transit_odp.fares.factories import FaresMetadataFactory
from transit_odp.naptan.factories import AdminAreaFactory, StopPointFactory
from transit_odp.organisation.constants import AVLType, FeedStatus
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    DatasetRevisionFactory,
    OrganisationFactory,
)
from transit_odp.organisation.models import Dataset
from transit_odp.users.constants import OrgAdminType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestAVLSearchView:
    host = DATA_HOST
    url = reverse("avl-search", host=host)
    dataset_type = AVLType
    template_path = "browse/avl/search.html"

    def setup_feeds(self):

        self.organisation1 = OrganisationFactory(name="Alpha")
        self.organisation2 = OrganisationFactory(name="Beta")
        self.admin_areas = [AdminAreaFactory(name=name) for name in "ABCDE"]
        a, b, c, d, e = self.admin_areas

        # create feeds for each of the organisation
        revision = DatasetRevisionFactory(
            dataset__organisation=self.organisation1,
            dataset__dataset_type=self.dataset_type,
            status=FeedStatus.live.value,
            is_published=True,
            admin_areas=(a,),
            first_service_start=datetime.datetime(2030, 12, 25),
        )
        FaresMetadataFactory(revision=revision, stops=(StopPointFactory(admin_area=a),))

        DatasetRevisionFactory(
            dataset__organisation=self.organisation1,
            dataset__dataset_type=self.dataset_type,
            status=FeedStatus.live.value,
            is_published=True,
            admin_areas=(b,),
        )

        DatasetRevisionFactory(
            dataset__organisation=self.organisation1,
            dataset__dataset_type=self.dataset_type,
            status=FeedStatus.expired.value,
            is_published=True,
            admin_areas=(c,),
        )

        revision = DatasetRevisionFactory(
            dataset__organisation=self.organisation2,
            dataset__dataset_type=self.dataset_type,
            status=FeedStatus.live.value,
            is_published=True,
            admin_areas=(d,),
            first_service_start=datetime.datetime(2030, 12, 25),
        )

        FaresMetadataFactory(revision=revision, stops=(StopPointFactory(admin_area=d),))

        DatasetRevisionFactory(
            dataset__organisation=self.organisation2,
            dataset__dataset_type=self.dataset_type,
            status=FeedStatus.error.value,
            is_published=True,
            admin_areas=(e,),
        )

        revision = DatasetRevisionFactory(
            dataset__organisation=self.organisation2,
            dataset__dataset_type=self.dataset_type,
            status=FeedStatus.live.value,
            is_published=True,
            admin_areas=self.admin_areas,
        )
        stops = [
            StopPointFactory(admin_area=admin_area) for admin_area in self.admin_areas
        ]
        FaresMetadataFactory(revision=revision, stops=stops)

    def test_get_success_page(self, client_factory):

        client = client_factory(host=self.host)
        response = client.get(self.url)
        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path

    def test_search_no_filters(self, client_factory):
        self.setup_feeds()
        client = client_factory(host=self.host)
        response = client.get(self.url)
        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        # no filtering; so display all published live, expired, error feeds
        assert response.context_data["object_list"].count() == 6

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
        assert response.context_data["object_list"].count() == 6

    def test_search_filters_status(self, client_factory):
        self.setup_feeds()
        client = client_factory(host=self.host)
        response = client.get(
            self.url,
            data={
                "q": "",
                "area": "",
                "organisation": "",
                "status": FeedStatus.live.value,
                "start": "",
            },
        )

        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        assert response.context_data["object_list"].count() == 4

    def test_search_filters_operator(self, client_factory):
        self.setup_feeds()
        client = client_factory(host=self.host)
        response = client.get(
            self.url,
            data={
                "q": "",
                "area": "",
                "organisation": str(self.organisation1.id),
                "status": "",
                "start": "",
            },
        )
        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        assert response.context_data["object_list"].count() == 3

    def test_ordering(self, client_factory):
        self.setup_feeds()
        qs = Dataset.objects.add_live_data().order_by("-name")
        client = client_factory(host=self.host)
        response = client.get(
            self.url,
            data={"ordering": "-name", "publisher": self.organisation1.id},
        )

        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        assert list(response.context_data["object_list"]) == list(qs)

    def test_search_query(self, client_factory):
        self.setup_feeds()

        expected = (
            Dataset.objects.add_live_data()
            .filter(
                organisation=self.organisation1, live_revision__admin_areas__name="A"
            )
            .first()
        )

        client = client_factory(host=self.host)
        response = client.get(
            self.url, data={"publisher": self.organisation1.id, "q": expected.name}
        )

        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path

        actual = response.context_data["object_list"]
        assert len(actual) == 1
        assert actual[0] == expected


class TestUserAVLFeedbackView:
    view_name = "avl-feed-feedback"

    @pytest.fixture()
    def revision(self):
        org = OrganisationFactory()
        publisher = UserFactory(account_type=OrgAdminType, organisations=(org,))
        return AVLDatasetRevisionFactory(
            dataset__contact=publisher,
            status=FeedStatus.live.value,
            last_modified_user=publisher,
            published_by=publisher,
            dataset__organisation=org,
        )

    def test_feedback_form_is_rendered(
        self, user: settings.AUTH_USER_MODEL, data_client, revision
    ):
        data_client.force_login(user=user)

        url = reverse(
            self.view_name, kwargs={"pk": revision.dataset.id}, host=DATA_HOST
        )
        response = data_client.get(url)

        assert response.status_code == 200
        assert "browse/timetables/user_feedback.html" in response.template_name

        assert isinstance(response.context_data["form"], UserFeedbackForm)

    def test_feedback_is_sent_to_pubished_by_user(
        self, mailoutbox, user, revision, data_client
    ):
        data_client.force_login(user=user)

        url = reverse(self.view_name, args=[revision.dataset.id], host=DATA_HOST)

        response = data_client.post(
            url,
            data={
                "feedback": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                "anonymous": False,
            },
            follow=True,
        )

        assert response.status_code == 200
        assert len(mailoutbox) == 1
        m = mailoutbox[0]
        assert f"User: {user.email}" in m.body
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [revision.published_by.email]

    def test_feedback_is_sent_anonymously(
        self, mailoutbox, user, data_client, revision
    ):
        data_client.force_login(user=user)

        url = reverse(self.view_name, args=[revision.dataset.id], host=DATA_HOST)

        response = data_client.post(
            url,
            data={
                "feedback": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                "anonymous": True,
            },
            follow=True,
        )

        assert response.status_code == 200
        assert len(mailoutbox) == 1
        m = mailoutbox[0]
        assert m.subject == "You have feedback on your data"
        assert f"User: {user.email}" not in m.body
        assert "User: Anonymous" in m.body
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [revision.published_by.email]
