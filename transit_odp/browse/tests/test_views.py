import csv
import datetime
import io
import zipfile
from unittest.mock import Mock, patch

import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.utils import timezone
from django_hosts import reverse
from freezegun import freeze_time

from config.hosts import DATA_HOST
from transit_odp.avl.factories import AVLValidationReportFactory
from transit_odp.browse.tasks import task_create_data_catalogue_archive
from transit_odp.browse.views.operators import OperatorDetailView, OperatorsView
from transit_odp.browse.views.timetable_views import (
    DatasetChangeLogView,
    DatasetDetailView,
)
from transit_odp.common.downloaders import GTFSFile
from transit_odp.common.forms import ConfirmationForm
from transit_odp.data_quality.factories.report import PTIObservationFactory
from transit_odp.fares.factories import FaresMetadataFactory
from transit_odp.naptan.factories import AdminAreaFactory
from transit_odp.organisation.constants import DatasetType, FeedStatus
from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetRevisionFactory,
    DatasetSubscriptionFactory,
    OrganisationFactory,
)
from transit_odp.organisation.models import DatasetSubscription, Organisation
from transit_odp.pipelines.factories import (
    BulkDataArchiveFactory,
    ChangeDataArchiveFactory,
    DatasetETLTaskResultFactory,
)
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
        user = UserFactory()
        now = timezone.now()
        yesterday = now - datetime.timedelta(days=1)

        with freeze_time(now):
            BulkDataArchiveFactory(
                data__data=b"latest bulk content",
                data__filename="bulk_archive_test.zip",
            )

        with freeze_time(yesterday):
            BulkDataArchiveFactory(
                data__data=b"bulk content",
                data__filename="bulk_archive_yesterday_test.zip",
            )

        host = DATA_HOST
        client = client_factory(host=host)
        client.force_login(user)
        url = reverse("downloads-bulk", host=host)
        response = client.get(url)

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


class TestDataDownloadCatalogueView:
    host = DATA_HOST

    operator_noc_headers = ["operator", "noc"]

    def extract_csv_content_from_zip_file(self, infile):
        csv_reader = csv.reader(io.TextIOWrapper(infile, "utf-8"))
        body = list(csv_reader)
        headers = body.pop(0)
        return headers, body

    def test_data_catalogue_download_zip_file(self, client_factory):
        task_create_data_catalogue_archive()
        client = client_factory(host=self.host)
        url = reverse("download-catalogue", host=self.host)

        response = client.get(url)

        expected_disposition = "attachment; filename=bodsdatacatalogue.zip"
        assert response.status_code == 200
        assert response.get("Content-Disposition") == expected_disposition

        expected_files = [
            "operator_noc_data_catalogue.csv",
            "organisation.csv",
            "data_catalogue_guidance.txt",
        ]

        with zipfile.ZipFile(io.BytesIO(b"".join(response.streaming_content))) as zf:
            for zf in zf.infolist():
                assert zf.filename in expected_files

    def test_operator_noc_download(self, client_factory):
        OrganisationFactory.create()
        OrganisationFactory.create(nocs=4)

        orgs = Organisation.objects.values_list("name", "nocs__noc").order_by(
            "name", "nocs__noc"
        )

        task_create_data_catalogue_archive()
        client = client_factory(host=self.host)
        url = reverse("download-catalogue", host=self.host)

        response = client.get(url)

        assert response.status_code == 200
        expected_disposition = "attachment; filename=bodsdatacatalogue.zip"
        assert response.get("Content-Disposition") == expected_disposition

        noc_csv_title = "operator_noc_data_catalogue.csv"
        with zipfile.ZipFile(io.BytesIO(b"".join(response.streaming_content))) as zf:
            with zf.open(noc_csv_title, "r") as infile:
                headers, body = self.extract_csv_content_from_zip_file(infile)

        assert headers == self.operator_noc_headers

        expected = [list(elem) for elem in orgs]
        expected.sort(key=lambda n: n[1])
        body.sort(key=lambda n: n[1])
        assert body == expected

    def test_operator_noc_download_exclude_inactive_orgs(self, client_factory):
        OrganisationFactory.create()
        OrganisationFactory.create(is_active=False)
        OrganisationFactory.create(nocs=4)

        orgs = (
            Organisation.objects.filter(is_active=True)
            .values_list("name", "nocs__noc")
            .order_by("name", "nocs__noc")
        )

        task_create_data_catalogue_archive()
        client = client_factory(host=self.host)
        url = reverse("download-catalogue", host=self.host)

        response = client.get(url)

        assert response.status_code == 200
        expected_disposition = "attachment; filename=bodsdatacatalogue.zip"
        assert response.get("Content-Disposition") == expected_disposition

        noc_csv_title = "operator_noc_data_catalogue.csv"
        with zipfile.ZipFile(io.BytesIO(b"".join(response.streaming_content))) as zf:
            with zf.open(noc_csv_title, "r") as infile:
                headers, body = self.extract_csv_content_from_zip_file(infile)
        assert headers == self.operator_noc_headers

        expected = [list(elem) for elem in orgs]
        expected.sort(key=lambda n: n[1])
        body.sort(key=lambda n: n[1])
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


class TestOperatorsView:
    def test_operators_view_basic(self, request_factory: RequestFactory):
        num_orgs = 3
        orgs = OrganisationFactory.create_batch(num_orgs)
        orgs[0].is_active = False
        orgs[0].save()

        request = request_factory.get("/operators/")
        request.user = AnonymousUser()

        response = OperatorsView.as_view()(request)

        assert response.status_code == 200
        assert response.context_data["view"].template_name == "browse/operators.html"
        assert response.context_data["q"] == ""
        assert response.context_data["ordering"] == "name"

        operators = response.context_data["operators"]
        assert "names" in operators
        assert len(operators["names"]) == num_orgs - 1
        for n in operators["names"]:
            assert n in [org.name for org in orgs[1:]]

    def test_operators_view_order_by_name(self, request_factory: RequestFactory):
        orgs = OrganisationFactory.create_batch(3)
        request = request_factory.get("/operators/?ordering=name")
        request.user = AnonymousUser()

        response = OperatorsView.as_view()(request)
        assert response.status_code == 200
        expected_order = sorted([o.name for o in orgs])
        operators = response.context_data["operators"]
        assert operators["names"] == expected_order

        object_names = [obj.name for obj in response.context_data["object_list"]]
        assert object_names == expected_order

    def test_operators_view_order_by_name_reverse(
        self, request_factory: RequestFactory
    ):
        orgs = OrganisationFactory.create_batch(3)
        request = request_factory.get("/operators/?ordering=-name")
        request.user = AnonymousUser()

        response = OperatorsView.as_view()(request)
        assert response.status_code == 200
        expected_order = sorted([o.name for o in orgs], reverse=True)
        object_names = [obj.name for obj in response.context_data["object_list"]]
        assert object_names == expected_order

    def test_operators_view_order_by_date(self, request_factory: RequestFactory):
        orgs = OrganisationFactory.create_batch(3)
        orgs[1].created -= datetime.timedelta(days=1)
        orgs[1].save()
        orgs[2].created += datetime.timedelta(days=1)
        orgs[2].save()
        request = request_factory.get("/operators/?ordering=created")
        request.user = AnonymousUser()

        response = OperatorsView.as_view()(request)
        assert response.status_code == 200
        expected_order = [orgs[1].name, orgs[0].name, orgs[2].name]
        object_names = [obj.name for obj in response.context_data["object_list"]]
        assert object_names == expected_order

    def test_operators_view_order_by_date_reversed(
        self, request_factory: RequestFactory
    ):
        orgs = OrganisationFactory.create_batch(3)
        orgs[1].created -= datetime.timedelta(days=1)
        orgs[1].save()
        orgs[2].created += datetime.timedelta(days=1)
        orgs[2].save()
        request = request_factory.get("/operators/?ordering=-created")
        request.user = UserFactory(organisations=orgs)

        response = OperatorsView.as_view()(request)
        assert response.status_code == 200
        expected_order = [orgs[2].name, orgs[0].name, orgs[1].name]
        object_names = [obj.name for obj in response.context_data["object_list"]]
        assert object_names == expected_order

    def test_operators_view_search(self, request_factory: RequestFactory):
        orgs = [
            OrganisationFactory(name="Sonny & Coach"),
            OrganisationFactory(name="BusOnWheels"),
            OrganisationFactory(name="Coach Bronson"),
            OrganisationFactory(name="Coachella"),
        ]
        request = request_factory.get("/operators/?q=son")
        request.user = UserFactory(organisations=orgs)

        response = OperatorsView.as_view()(request)
        assert response.status_code == 200
        object_names = [obj.name for obj in response.context_data["object_list"]]
        assert orgs[0].name in object_names
        assert orgs[1].name in object_names
        assert orgs[2].name in object_names
        assert orgs[3].name not in object_names


class TestOperatorDetailView:
    def test_operator_detail_view_timetable_stats(
        self, request_factory: RequestFactory
    ):
        org = OrganisationFactory()
        num_datasets = 2

        datasets = DatasetFactory.create_batch(
            num_datasets, organisation=org, dataset_type=DatasetType.TIMETABLE.value
        )
        revisions = [
            DatasetRevisionFactory(dataset=datasets[0], num_of_lines=1),
            DatasetRevisionFactory(dataset=datasets[1], num_of_lines=2),
        ]

        PTIObservationFactory(revision=revisions[1])

        request = request_factory.get("/operators/")
        request.user = UserFactory()

        response = OperatorDetailView.as_view()(request, pk=org.id)
        assert response.status_code == 200
        context = response.context_data
        assert context["view"].template_name == "browse/operators/operator_detail.html"

        timetable_stats = context["timetable_stats"]
        assert timetable_stats.total_dataset_count == len(datasets)
        assert timetable_stats.line_count == 3
        assert context["timetable_non_compliant"] == 1

    def test_operator_detail_view_avl_stats(self, request_factory: RequestFactory):
        org = OrganisationFactory()
        num_datasets = 5
        datasets = DatasetFactory.create_batch(
            num_datasets, organisation=org, dataset_type=DatasetType.AVL.value
        )
        revisions = [DatasetRevisionFactory(dataset=d) for d in datasets]
        AVLValidationReportFactory(
            created=datetime.datetime.now().date(),
            revision=revisions[0],
            critical_count=2,
        )

        request = request_factory.get("/operators/")
        request.user = UserFactory()

        response = OperatorDetailView.as_view()(request, pk=org.id)
        assert response.status_code == 200
        context = response.context_data

        assert context["avl_total_datasets"] == num_datasets
        assert context["avl_non_compliant"] == 1

    def test_operator_detail_view_fares_stats(self, request_factory: RequestFactory):
        org = OrganisationFactory()
        num_datasets = 5
        datasets = DatasetFactory.create_batch(
            num_datasets, organisation=org, dataset_type=DatasetType.FARES.value
        )
        revisions = [DatasetRevisionFactory(dataset=d) for d in datasets]
        FaresMetadataFactory(revision=revisions[0], num_of_fare_products=1)
        FaresMetadataFactory(revision=revisions[1], num_of_fare_products=2)

        request = request_factory.get("/operators/")
        request.user = UserFactory()

        response = OperatorDetailView.as_view()(request, pk=org.id)
        assert response.status_code == 200
        context = response.context_data

        timetable_stats = context["fares_stats"]
        assert timetable_stats.total_dataset_count == num_datasets
        assert timetable_stats.total_fare_products == 3
        assert context["fares_non_compliant"] == 0

    def test_operator_detail_view_urls(self, request_factory: RequestFactory):
        nocs = ["NOC1", "NOC2"]
        org = OrganisationFactory(nocs=nocs)
        user = UserFactory()

        request = request_factory.get("/operators/")
        request.user = user

        response = OperatorDetailView.as_view()(request, pk=org.id)
        assert response.status_code == 200
        context = response.context_data

        noc_query_param = "noc=" + ",".join(nocs)
        operator_ref_query_param = "operatorRef=" + ",".join(nocs)
        token_query_param = "api_key=" + user.auth_token.key

        timetable_url = (
            f"{reverse('api:feed-list', host=DATA_HOST)}"
            f"?{noc_query_param}&{token_query_param}"
        )
        assert context["timetable_feed_url"] == timetable_url

        avl_url = (
            f"{reverse('api:avldatafeedapi', host=DATA_HOST)}"
            f"?{operator_ref_query_param}&{token_query_param}"
        )
        assert context["avl_feed_url"] == avl_url

        fares_url = (
            f"{reverse('api:fares-api-list', host=DATA_HOST)}"
            f"?{noc_query_param}&{token_query_param}"
        )
        assert context["fares_feed_url"] == fares_url
