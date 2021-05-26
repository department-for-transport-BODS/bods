import csv
import datetime
import io
from unittest.mock import Mock, patch

import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.management import call_command
from django.test import RequestFactory
from django.utils import timezone
from django_hosts import reverse
from freezegun import freeze_time

from config.hosts import DATA_HOST
from transit_odp.browse.forms import UserFeedbackForm
from transit_odp.browse.serializers import DatasetCatalogueSerializer
from transit_odp.browse.views.timetable_views import (
    DatasetChangeLogView,
    DatasetDetailView,
)
from transit_odp.common.downloaders import GTFSFile
from transit_odp.common.forms import ConfirmationForm
from transit_odp.naptan.factories import AdminAreaFactory
from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetRevisionFactory,
    DatasetSubscriptionFactory,
    OrganisationFactory,
)
from transit_odp.organisation.models import Dataset, DatasetSubscription, Organisation
from transit_odp.pipelines.factories import (
    BulkDataArchiveFactory,
    ChangeDataArchiveFactory,
    DatasetETLTaskResultFactory,
)
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import (
    AgentUserFactory,
    AgentUserInviteFactory,
    UserFactory,
)
from transit_odp.users.models import AgentUserInvite
from transit_odp.users.utils import create_verified_org_user

pytestmark = pytest.mark.django_db


class TestFeedDetailsView:
    def test_no_login_view(
        self, user: settings.AUTH_USER_MODEL, request_factory: RequestFactory
    ):
        org = OrganisationFactory.create()
        admin_areas = AdminAreaFactory.create_batch(2)

        dataset = DatasetFactory(organisation=org)
        revision = DatasetRevisionFactory(
            dataset=dataset,
            status=FeedStatus.live.value,
            admin_areas=(admin_areas[0], admin_areas[1]),
        )
        DatasetETLTaskResultFactory(revision=revision)

        request = request_factory.get("/feed/")
        request.user = AnonymousUser()

        response = DatasetDetailView.as_view()(request, pk=dataset.id)

        assert response.status_code == 200
        assert (
            response.context_data["view"].template_name
            == "browse/timetables/dataset_detail/index.html"
        )
        assert not response.context_data[
            "notification"
        ]  # notification option turned off for unauthenticated users
        assert response.context_data["object"].id == dataset.id
        assert response.context_data["object"].name == revision.name

        admin_area_names = ", ".join(
            sorted([admin_area.name for admin_area in admin_areas])
        )
        assert response.context_data["admin_areas"] == admin_area_names

    def test_login_view(
        self, user: settings.AUTH_USER_MODEL, request_factory: RequestFactory
    ):
        org_user = create_verified_org_user()
        dataset = DatasetFactory.create(organisation=org_user.organisation)
        revision = DatasetRevisionFactory.create(
            dataset=dataset, status=FeedStatus.live.value
        )
        DatasetETLTaskResultFactory(revision=revision)

        DatasetSubscriptionFactory.create(dataset=dataset, user=org_user)

        request = request_factory.get("/feed/")
        request.user = org_user

        response = DatasetDetailView.as_view()(request, pk=dataset.id)

        assert response.status_code == 200
        assert (
            response.context_data["view"].template_name
            == "browse/timetables/dataset_detail/index.html"
        )
        assert response.context_data[
            "notification"
        ]  # notification option turned on for authenticated users
        assert response.context_data["object"].id == dataset.id
        assert response.context_data["object"].live_revision.name == revision.name


class TestFeedSubscriptionView:
    def test_anonymous_access_returns_gatekeeper(self, client_factory):
        # Setup
        host = DATA_HOST
        client = client_factory(host=host)

        # create an organisation and feed
        org = OrganisationFactory.create()
        dataset = DatasetFactory.create(organisation=org)

        # Test
        url = reverse("feed-subscription", kwargs={"pk": dataset.id}, host=host)
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert "browse/timetables/feed_subscription_gatekeeper.html" in [
            t.name for t in response.templates
        ]

    def test_asks_to_confirm_subscription(
        self, user: settings.AUTH_USER_MODEL, client_factory
    ):
        # Setup
        host = DATA_HOST
        client = client_factory(host=host)
        client.force_login(user=user)

        # create data
        org = OrganisationFactory.create()
        dataset = DatasetFactory.create(organisation=org)

        # Test
        url = reverse("feed-subscription", kwargs={"pk": dataset.id}, host=host)
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert "browse/timetables/feed_subscription.html" in [
            t.name for t in response.templates
        ]
        assert response.context["is_subscribed"] is False
        assert isinstance(response.context_data["form"], ConfirmationForm)

    def test_asks_to_confirm_unsubscription(
        self, user: settings.AUTH_USER_MODEL, client_factory
    ):
        # Setup
        host = DATA_HOST
        client = client_factory(host=host)
        client.force_login(user=user)

        # create an organisation
        org = OrganisationFactory.create()
        dataset = DatasetFactory.create(organisation=org, subscribers=(user,))

        # Test
        url = reverse("feed-subscription", kwargs={"pk": dataset.id}, host=host)
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert "browse/timetables/feed_subscription.html" in [
            t.name for t in response.templates
        ]
        assert response.context["is_subscribed"] is True
        assert isinstance(response.context_data["form"], ConfirmationForm)

    def test_user_is_unsubscribed(self, user: settings.AUTH_USER_MODEL, client_factory):
        host = DATA_HOST
        client = client_factory(host=host)
        client.force_login(user=user)

        org = OrganisationFactory.create()
        dataset = DatasetFactory.create(organisation=org, subscribers=(user,))

        url = reverse("feed-subscription", kwargs={"pk": dataset.id}, host=host)

        response = client.post(url)

        assert response.status_code == 302
        # TODO - with follow redirects turned on we should be able to test the
        # final template
        assert not DatasetSubscription.objects.filter(
            dataset=dataset, user=user
        ).exists()

    def test_user_is_subscribed(self, user: settings.AUTH_USER_MODEL, client_factory):
        host = DATA_HOST
        client = client_factory(host=host)
        client.force_login(user=user)

        org = OrganisationFactory.create()
        dataset = DatasetFactory.create(organisation=org)

        url = reverse("feed-subscription", kwargs={"pk": dataset.id}, host=host)

        response = client.post(url)

        assert response.status_code == 302
        # TODO - with follow redirects turned on we should be able to test the
        # final template
        assert DatasetSubscription.objects.filter(dataset=dataset, user=user).exists()

    def test_success_page_back_url(
        self, user: settings.AUTH_USER_MODEL, client_factory
    ):
        """
        Subscription flow:
        (1) feed-detail page or feeds-manage page
        (2) confirm subscribe / unsubscribe page
        (3) success page
        On the success page, the back_url should be feed-detail or feeds-manage
        page -- however the user reached the confirmation page.
        """
        host = DATA_HOST
        client = client_factory(host=host)
        client.force_login(user=user)

        org = OrganisationFactory.create()
        dataset = DatasetFactory.create(organisation=org)

        success_page_url = reverse(
            "feed-subscription-success", kwargs={"pk": dataset.id}, host=host
        )
        back_urls = [
            reverse("feed-detail", kwargs={"pk": dataset.id}, host=host),
            reverse("users:feeds-manage", host=host),
        ]

        for back_url in back_urls:
            # Store supposed user origin in session (i.e. where they were before
            # dataset subscription confirmation page)
            session = client.session
            session["back_url"] = back_url
            session.save()

            response = client.get(success_page_url)

            assert response.status_code == 200
            assert (
                response.context_data["view"].template_name
                == "browse/timetables/feed_subscription_success.html"
            )
            assert response.context["back_url"] == back_url

    def test_success_page_back_url_is_feed_detail_when_no_stashed_url(
        self, user: settings.AUTH_USER_MODEL, client_factory
    ):
        """
        If we can't get the correct back_url from the session, the back_url should
        default to the feed-detail page.
        (Users are more likely to have come from feed-detail than feeds-manage
        because subscriptions can only be done from the feed-detail pages.)
        """
        host = DATA_HOST
        client = client_factory(host=host)
        client.force_login(user=user)

        org = OrganisationFactory.create()
        dataset = DatasetFactory.create(organisation=org)

        success_page_url = reverse(
            "feed-subscription-success", kwargs={"pk": dataset.id}, host=host
        )
        back_url = reverse("feed-detail", kwargs={"pk": dataset.id}, host=host)

        response = client.get(success_page_url)

        assert response.status_code == 200

        expected_name = "browse/timetables/feed_subscription_success.html"
        actual_name = response.context_data["view"].template_name

        assert actual_name == expected_name
        assert response.context["back_url"] == back_url


class TestFeedChangeLogView:
    def test_success_view(self, request_factory: RequestFactory):
        # create a user
        user = UserFactory()

        # create dataset
        revision = DatasetRevisionFactory(
            is_published=True, status=FeedStatus.live.value
        )

        request = request_factory.get("/feed/")
        request.user = user

        response = DatasetChangeLogView.as_view()(request, pk=revision.dataset.id)

        assert response.status_code == 200
        assert (
            response.context_data["view"].template_name
            == "browse/timetables/feed_change_log.html"
        )
        assert response.context_data["object_list"].count() == 1

    def test_404(self, request_factory: RequestFactory):
        user = UserFactory.create()

        DatasetRevisionFactory(is_published=True, status=FeedStatus.live.value)

        request = request_factory.get("/feed/")
        request.user = user

        with pytest.raises(Exception) as excinfo:
            DatasetChangeLogView.as_view()(request, pk=5000)

        assert str(excinfo.value) == "No dataset found matching the query"


class TestFeedDownloadView:
    def test_download_view(self, client_factory):
        # Setup
        revision = DatasetRevisionFactory(
            status=FeedStatus.live.value,
            is_published=True,
            upload_file__filename="myfile.txt",
            upload_file__data=b"content",
        )

        host = DATA_HOST
        client = client_factory(host=host)

        url = reverse("feed-download", kwargs={"pk": revision.dataset.id}, host=host)

        # Test
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert response.getvalue() == b"content"

    def test_download_details(self, client_factory):
        dataset = DatasetFactory()
        revision1 = DatasetRevisionFactory(
            status=FeedStatus.live.value,
            dataset=dataset,
            is_published=True,
            upload_file__filename="myfile.txt",
            upload_file__data=b"content1",
        )
        dataset.live_revision = revision1
        DatasetRevisionFactory(
            status=FeedStatus.success.value,
            dataset=dataset,
            is_published=False,
            upload_file__filename="myfile.txt",
            upload_file__data=b"content2",
        )

        host = DATA_HOST
        client = client_factory(host=host)

        url = reverse("feed-download", kwargs={"pk": revision1.dataset.id}, host=host)

        response = client.get(url)

        assert response.status_code == 200
        assert response.getvalue() == b"content1"

    def test_download_get_latest_live_revision(self, client_factory):
        dataset = DatasetFactory()
        revision1 = DatasetRevisionFactory(
            status=FeedStatus.live.value,
            dataset=dataset,
            is_published=True,
            upload_file__filename="myfile.txt",
            upload_file__data=b"content1",
        )
        dataset.live_revision = revision1
        DatasetRevisionFactory(
            status=FeedStatus.live.value,
            dataset=dataset,
            is_published=True,
            upload_file__filename="myfile.txt",
            upload_file__data=b"content2",
        )

        host = DATA_HOST
        client = client_factory(host=host)

        url = (
            reverse("feed-download", kwargs={"pk": revision1.dataset.id}, host=host)
            + "?get_working=true"
        )

        # Test
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert response.getvalue() == b"content2"

    def test_download_get_previous_live_revision(self, client_factory):
        # Setup
        dataset = DatasetFactory()
        revision1 = DatasetRevisionFactory(
            status=FeedStatus.live.value,
            dataset=dataset,
            is_published=True,
            upload_file__filename="myfile.txt",
            upload_file__data=b"content1",
        )
        dataset.live_revision = revision1
        DatasetRevisionFactory(
            status=FeedStatus.error.value,
            dataset=dataset,
            is_published=True,
            upload_file__filename="myfile.txt",
            upload_file__data=b"content2",
        )

        host = DATA_HOST
        client = client_factory(host=host)

        url = (
            reverse("feed-download", kwargs={"pk": revision1.dataset.id}, host=host)
            + "?get_working=true"
        )

        # Test
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert response.getvalue() == b"content1"


class TestDownloadBulkDataArchiveView:
    def test_download(self, client_factory):
        # Setup
        now = timezone.now()
        yesterday = now - datetime.timedelta(days=1)

        with freeze_time(now):
            BulkDataArchiveFactory(
                data__data=b"latest bulk content",
                data__filename="bulk_archive_test.zip",
            )

        # Create an older archive
        with freeze_time(yesterday):
            BulkDataArchiveFactory(
                data__data=b"bulk content",
                data__filename="bulk_archive_yesterday_test.zip",
            )

        host = DATA_HOST
        client = client_factory(host=host)

        url = reverse("downloads-bulk", host=host)

        # Test
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert response.as_attachment is True
        assert response.filename == "bulk_archive_test.zip"
        assert response.getvalue() == b"latest bulk content"


class TestDownloadChangeDataArchiveView:
    def test_download(self, client_factory):
        # Setup
        archive = ChangeDataArchiveFactory(
            data__data=b"change content", data__filename="bulk_change_test.zip"
        )

        host = DATA_HOST
        client = client_factory(host=host)

        url = reverse(
            "downloads-change", host=host, kwargs={"published_at": archive.published_at}
        )

        # Test
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert response.as_attachment is True
        assert response.filename == "bulk_change_test.zip"
        assert response.getvalue() == b"change content"

    def test_returns_404_if_slug_invalid(self, client_factory):
        ChangeDataArchiveFactory(
            data__data=b"change content", data__filename="bulk_change_test.zip"
        )

        host = DATA_HOST
        client = client_factory(host=host)

        url = reverse(
            "downloads-change", host=host, kwargs={"published_at": "2019-10-"}
        )

        response = client.get(url)
        assert response.status_code == 404

    def test_returns_404_for_archives_older_than_7_days(self, client_factory):
        now = timezone.now().date()
        archive = ChangeDataArchiveFactory(
            data__data=b"old content",
            data__filename="bulk_change_test.zip",
            published_at=now - datetime.timedelta(days=10),
        )

        host = DATA_HOST
        client = client_factory(host=host)

        url = reverse(
            "downloads-change", host=host, kwargs={"published_at": archive.published_at}
        )

        response = client.get(url)

        assert response.status_code == 404


@pytest.mark.django_db(transaction=True)
class TestUserFeedbackView:
    @pytest.fixture()
    def revision(self):
        # Create test data
        org = OrganisationFactory()
        publisher = UserFactory(
            account_type=AccountType.org_admin.value, organisations=(org,)
        )
        return DatasetRevisionFactory(
            dataset__contact=publisher,
            status=FeedStatus.live.value,
            last_modified_user=publisher,
            published_by=publisher,
            dataset__organisation=org,
        )

    def load_sites(self):
        call_command("loaddata", "sites.json")

    def test_feedback_form_is_rendered(
        self, user: settings.AUTH_USER_MODEL, data_client, revision
    ):
        # Setup
        self.load_sites()
        data_client.force_login(user=user)

        # Test
        url = reverse(
            "feed-feedback", kwargs={"pk": revision.dataset.id}, host=DATA_HOST
        )
        response = data_client.get(url)

        # Assert
        assert response.status_code == 200
        assert "browse/timetables/user_feedback.html" in response.template_name

        assert isinstance(response.context_data["form"], UserFeedbackForm)

    def test_feedback_is_sent_to_pubished_by_user(
        self, mailoutbox, user, revision, data_client
    ):
        # Setup
        self.load_sites()
        data_client.force_login(user=user)

        url = reverse("feed-feedback", args=[revision.dataset.id], host=DATA_HOST)

        # Test
        response = data_client.post(
            url,
            data={
                "feedback": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                "anonymous": False,
            },
            follow=True,
        )

        # Assert
        assert response.status_code == 200
        assert len(mailoutbox) == 1
        m = mailoutbox[0]
        # assert m.subject == "New user feedback on your dataset"
        assert f"User: {user.email}" in m.body
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [revision.published_by.email]

    def test_feedback_is_sent_anonymously(
        self, mailoutbox, user, data_client, revision
    ):
        # Setup
        self.load_sites()
        data_client.force_login(user=user)

        url = reverse("feed-feedback", args=[revision.dataset.id], host=DATA_HOST)

        # Test
        response = data_client.post(
            url,
            data={
                "feedback": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                "anonymous": True,
            },
            follow=True,
        )

        # Assert
        assert response.status_code == 200
        assert len(mailoutbox) == 1
        m = mailoutbox[0]
        assert m.subject == "[BODS] Operator Feedback"
        assert f"User: {user.email}" not in m.body
        assert "User: Anonymous" in m.body
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [revision.published_by.email]


class TestDataDownloadCatalogueView:
    host = DATA_HOST

    operator_noc_headers = ["operator", "noc"]
    operator_dataset_headers = [
        "operator",
        "dataType",
        "status",
        "lastUpdated",
        "dataID",
    ]

    def extract_csv_content(self, content):
        content = content.decode("utf-8")
        cvs_reader = csv.reader(io.StringIO(content))
        body = list(cvs_reader)
        headers = body.pop(0)
        return headers, body

    def test_operator_noc_download_for_no_orgs(self, client_factory):
        client = client_factory(host=self.host)
        url = reverse("operator-noc-catalogue", host=self.host)

        # Test
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert (
            response.get("Content-Disposition")
            == 'attachment; filename="operator_noc_mapping.csv"'
        )

        headers, body = self.extract_csv_content(response.content)
        assert headers == self.operator_noc_headers
        assert body == []  # no organisations

    def test_operator_noc_download(self, client_factory):
        # Setup
        OrganisationFactory.create()
        OrganisationFactory.create(nocs=4)

        orgs = Organisation.objects.values_list("name", "nocs__noc")

        client = client_factory(host=self.host)
        url = reverse("operator-noc-catalogue", host=self.host)

        # Test
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert (
            response.get("Content-Disposition")
            == 'attachment; filename="operator_noc_mapping.csv"'
        )

        headers, body = self.extract_csv_content(response.content)
        assert headers == self.operator_noc_headers
        assert body == [list(elem) for elem in orgs]

    def test_operator_noc_download_exclude_inactive_orgs(self, client_factory):
        # Setup
        OrganisationFactory.create()
        OrganisationFactory.create(is_active=False)
        OrganisationFactory.create(nocs=4)

        orgs = Organisation.objects.filter(is_active=True).values_list(
            "name", "nocs__noc"
        )

        client = client_factory(host=self.host)
        url = reverse("operator-noc-catalogue", host=self.host)

        # Test
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert (
            response.get("Content-Disposition")
            == 'attachment; filename="operator_noc_mapping.csv"'
        )

        headers, body = self.extract_csv_content(response.content)
        assert headers == self.operator_noc_headers
        assert body == [list(elem) for elem in orgs]

    def test_operator_dataset_download_for_no_orgs(self, client_factory):
        client = client_factory(host=self.host)
        url = reverse("operator-dataset-catalogue", host=self.host)

        # Test
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert (
            response.get("Content-Disposition")
            == 'attachment; filename="operator_dataID_mapping.csv"'
        )

        headers, body = self.extract_csv_content(response.content)
        assert headers == self.operator_dataset_headers
        assert body == []  # no organisations

    def test_operator_dataset_download(self, client_factory):
        # Setup
        orgs = OrganisationFactory.create_batch(2)
        for org in orgs:
            DatasetFactory.create(
                organisation=org,
            )

        dataset_list = Dataset.objects.add_organisation_name().order_by(
            "organisation_name", "dataset_type"
        )

        serializer = DatasetCatalogueSerializer(dataset_list, many=True)
        serialized_data = serializer.data
        expected = []

        for data in serialized_data:
            test_list = list(data.values())
            test_list[4] = str(test_list[4])
            expected.append(test_list)

        client = client_factory(host=self.host)
        url = reverse("operator-dataset-catalogue", host=self.host)

        # Test
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert (
            response.get("Content-Disposition")
            == 'attachment; filename="operator_dataID_mapping.csv"'
        )

        headers, body = self.extract_csv_content(response.content)
        assert headers == self.operator_dataset_headers
        assert body == expected

    def test_operator_dataset_download_exclude_inactive_org(self, client_factory):
        # Setup
        orgs = OrganisationFactory.create_batch(2)
        orgs.append(OrganisationFactory.create(is_active=False))
        for org in orgs:
            DatasetFactory.create(
                organisation=org,
            )

        dataset_list = (
            Dataset.objects.get_active_org()
            .add_organisation_name()
            .order_by("organisation_name", "dataset_type")
        )

        serializer = DatasetCatalogueSerializer(dataset_list, many=True)
        serialized_data = serializer.data
        expected = []

        for data in serialized_data:
            test_list = list(data.values())
            test_list[4] = str(test_list[4])
            expected.append(test_list)

        client = client_factory(host=self.host)
        url = reverse("operator-dataset-catalogue", host=self.host)

        # Test
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert (
            response.get("Content-Disposition")
            == 'attachment; filename="operator_dataID_mapping.csv"'
        )

        headers, body = self.extract_csv_content(response.content)
        assert headers == self.operator_dataset_headers
        assert body == expected


class TestGTFSStaticDownloads:
    host = DATA_HOST

    @patch("transit_odp.browse.views.timetable_views.GTFSFileDownloader")
    def test_download_gtfs_file_404(self, downloader_cls, client_factory):
        url = reverse("gtfs-file-download", args=["all"], host=self.host)

        downloader_obj = Mock()
        downloader_cls.return_value = downloader_obj
        gtfs_file = GTFSFile(filename="wah")
        downloader_obj.download_file_by_id.return_value = gtfs_file

        client = client_factory(host=self.host)
        response = client.get(url)
        assert response.status_code == 404
        downloader_obj.download_file_by_id.assert_called_once_with("all")


class TestUserAgentMyAccountView:
    def test_correct_template_used(self, client_factory):
        """
        Test for BODP-3299
        """
        organisation = OrganisationFactory.create()
        agent = AgentUserFactory(email="abc@abc.com", organisations=(organisation,))
        AgentUserInviteFactory(
            organisation=organisation, agent=agent, status=AgentUserInvite.ACCEPTED
        )

        data_host = DATA_HOST
        url = reverse(
            "users:home",
            host=data_host,
        )

        client = client_factory(host=data_host)
        client.force_login(user=agent)

        response = client.get(url)

        assert response.status_code == 200
        assert "users/user_account.html" in [t.name for t in response.templates]
        assert response.context["user"].email == agent.email
