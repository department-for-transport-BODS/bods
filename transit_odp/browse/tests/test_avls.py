import datetime

import pytest
from django.conf import settings
from django_hosts import reverse

from config.hosts import DATA_HOST
from transit_odp.avl.constants import UPPER_THRESHOLD
from transit_odp.avl.factories import AVLValidationReportFactory
from transit_odp.browse.forms import ConsumerFeedbackForm
from transit_odp.fares.factories import FaresMetadataFactory
from transit_odp.naptan.factories import AdminAreaFactory, StopPointFactory
from transit_odp.organisation.constants import AVLType, FeedStatus
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    DatasetRevisionFactory,
    OrganisationFactory,
)
from transit_odp.organisation.models import ConsumerFeedback, Dataset
from transit_odp.users.constants import OrgAdminType, SiteAdminType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


class BaseAVLSearchView:
    host = DATA_HOST
    url = reverse("avl-search", host=host)
    dataset_type = AVLType
    template_path = "browse/avl/search.html"

    def setup_feeds(self):

        self.organisation1 = OrganisationFactory(name="Alpha")
        self.organisation2 = OrganisationFactory(name="Beta")
        self.admin_areas = [AdminAreaFactory(name=name) for name in "ABCDE"]
        a, b, _, d, e = self.admin_areas

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
        assert response.context_data["object_list"].count() == 5

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
        assert response.context_data["object_list"].count() == 5

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
        assert response.context_data["object_list"].count() == 2

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
            self.url,
            data={"publisher": self.organisation1.id, "q": expected.description},
        )

        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path

        actual = response.context_data["object_list"]
        assert len(actual) == 1
        assert actual[0] == expected


class TestAVLSearchView(BaseAVLSearchView):
    def test_avl_compliance_filter(self, client_factory):
        self.setup_feeds()
        revision = AVLDatasetRevisionFactory()
        today = datetime.datetime.now().date()
        total_reports = 8
        for n in range(0, total_reports):
            date = today - datetime.timedelta(days=n)
            AVLValidationReportFactory(
                revision=revision,
                created=date,
                critical_score=UPPER_THRESHOLD - 0.1,
                non_critical_score=UPPER_THRESHOLD + 0.1,
            )

        client = client_factory(host=self.host)
        response = client.get(
            self.url,
            data={
                "q": "",
                "area": "",
                "organisation": "",
                "avl_compliance": "Non-compliant",
                "status": "",
                "start": "",
            },
        )
        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        assert response.context_data["object_list"].count() == 1


class TestUserAVLFeedbackView:
    view_name = "avl-feed-feedback"
    feedback_text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."

    @pytest.fixture()
    def revision(self):
        org = OrganisationFactory()
        UserFactory(account_type=SiteAdminType)
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

        assert isinstance(response.context_data["form"], ConsumerFeedbackForm)

    def test_feedback_is_sent_to_admin_by_user(
        self, mailoutbox, user, revision, data_client
    ):
        data_client.force_login(user=user)

        url = reverse(self.view_name, args=[revision.dataset.id], host=DATA_HOST)

        response = data_client.post(
            url,
            data={
                "feedback": self.feedback_text,
                "anonymous": False,
            },
            follow=True,
        )

        feedback = ConsumerFeedback.objects.filter(dataset=revision.dataset).first()
        assert feedback.consumer == user
        assert feedback.feedback == self.feedback_text
        assert response.status_code == 200
        assert len(mailoutbox) == 3
        m = mailoutbox[0]
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) != [revision.published_by.email]

    def test_feedback_is_sent_to_publisher_by_user(
        self, mailoutbox, user, revision, data_client
    ):
        data_client.force_login(user=user)

        url = reverse(self.view_name, args=[revision.dataset.id], host=DATA_HOST)

        response = data_client.post(
            url,
            data={
                "feedback": self.feedback_text,
                "anonymous": False,
            },
            follow=True,
        )
        feedback = ConsumerFeedback.objects.filter(dataset=revision.dataset).first()
        assert feedback.consumer == user
        assert feedback.feedback == self.feedback_text
        assert response.status_code == 200
        assert len(mailoutbox) == 3
        m = mailoutbox[2]
        assert f"User: {user.email}" in m.body
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [revision.published_by.email]

    def test_copy_feedback_to_consumer_by_consumer(
        self, mailoutbox, user, revision, data_client
    ):
        data_client.force_login(user=user)

        url = reverse(self.view_name, args=[revision.dataset.id], host=DATA_HOST)

        response = data_client.post(
            url,
            data={
                "feedback": self.feedback_text,
            },
            follow=True,
        )
        feedback = ConsumerFeedback.objects.filter(dataset=revision.dataset).first()
        assert feedback.consumer == user
        assert feedback.feedback == self.feedback_text
        assert response.status_code == 200
        assert len(mailoutbox) == 3
        m = mailoutbox[1]
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [user.email]

    def test_feedback_is_sent_to_admin_anonymously(
        self, mailoutbox, user, data_client, revision
    ):
        data_client.force_login(user=user)

        url = reverse(self.view_name, args=[revision.dataset.id], host=DATA_HOST)

        response = data_client.post(
            url,
            data={
                "feedback": self.feedback_text,
                "anonymous": True,
            },
            follow=True,
        )
        feedback = ConsumerFeedback.objects.filter(dataset=revision.dataset).first()
        assert feedback.consumer is None
        assert feedback.feedback == self.feedback_text
        assert response.status_code == 200
        assert len(mailoutbox) == 3
        m = mailoutbox[0]
        assert m.subject == "Bus Open Data feedback: Your email copy (do not reply)"
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) != [revision.published_by.email]

    def test_feedback_is_sent_to_publisher_anonymously(
        self, mailoutbox, user, data_client, revision
    ):
        data_client.force_login(user=user)

        url = reverse(self.view_name, args=[revision.dataset.id], host=DATA_HOST)

        response = data_client.post(
            url,
            data={
                "feedback": self.feedback_text,
                "anonymous": True,
            },
            follow=True,
        )
        feedback = ConsumerFeedback.objects.filter(dataset=revision.dataset).first()
        assert feedback.consumer is None
        assert feedback.feedback == self.feedback_text
        assert response.status_code == 200
        assert len(mailoutbox) == 3
        m = mailoutbox[2]
        assert m.subject == "You have feedback on your data"
        assert f"User: {user.email}" not in m.body
        assert "User: Anonymous" in m.body
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [revision.published_by.email]
