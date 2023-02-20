import csv
import io
import math
import zipfile
from datetime import date, timedelta

import factory
import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import QueryDict
from django.test import TestCase
from django.urls import set_urlconf
from django.utils.timezone import now
from django_hosts import reverse, reverse_host
from django_hosts.resolvers import get_host
from freezegun import freeze_time

from config.hosts import DATA_HOST, PUBLISH_HOST
from transit_odp.common.utils import reverse_path
from transit_odp.data_quality.factories.transmodel import DataQualityReportFactory
from transit_odp.naptan.factories import AdminAreaFactory
from transit_odp.organisation.constants import INACTIVE, DatasetType, FeedStatus
from transit_odp.organisation.csv.consumer_interactions import CSV_HEADERS
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    DatasetFactory,
    DatasetRevisionFactory,
    DatasetSubscriptionFactory,
    DraftDatasetFactory,
    FaresDatasetRevisionFactory,
)
from transit_odp.organisation.factories import LicenceFactory as BODSLicenceFactory
from transit_odp.organisation.factories import (
    OrganisationFactory,
    SeasonalServiceFactory,
    TXCFileAttributesFactory,
)
from transit_odp.organisation.models import Dataset, DatasetRevision
from transit_odp.otc.factories import LicenceModelFactory, ServiceModelFactory
from transit_odp.pipelines.factories import DatasetETLTaskResultFactory
from transit_odp.publish.forms import FeedUploadForm
from transit_odp.publish.tasks import task_generate_consumer_interaction_stats
from transit_odp.publish.views.timetable.create import FeedUploadWizard
from transit_odp.publish.views.timetable.update import FeedUpdateWizard
from transit_odp.site_admin.factories import (
    APIRequestFactory,
    ResourceRequestCounterFactory,
)
from transit_odp.users.constants import AccountType, OrgAdminType, OrgStaffType
from transit_odp.users.factories import (
    AgentUserFactory,
    AgentUserInviteFactory,
    OrgStaffFactory,
    UserFactory,
)
from transit_odp.users.models import AgentUserInvite
from transit_odp.users.utils import create_verified_org_user

ETL_TEST_DATA_DIR = "transit_odp/pipelines/tests/test_dataset_etl/data/"

pytestmark = pytest.mark.django_db


def test_publish_home_view_for_developer_user(client_factory):
    host = PUBLISH_HOST
    client = client_factory(host=host)
    set_urlconf(get_host(host))
    user = UserFactory(account_type=AccountType.developer.value)
    client.force_login(user=user)

    url = reverse("home", host=host)
    response = client.get(url, follow=True)
    assert response.status_code == 200
    assert response.context.get("start_view") == reverse(
        "gatekeeper", host=PUBLISH_HOST
    )


def test_publish_home_view_for_anonymous_user(client_factory):
    host = PUBLISH_HOST
    client = client_factory(host=host)
    set_urlconf(get_host(host))
    AnonymousUser()

    url = reverse("home", host=host)
    response = client.get(url, follow=True)

    assert response.status_code == 200
    assert response.context.get("start_view") is None


@pytest.mark.parametrize(
    "account_type",
    (AccountType.org_staff, AccountType.org_admin, AccountType.agent_user),
)
def test_publish_home_view(client_factory, account_type):
    host = PUBLISH_HOST
    client = client_factory(host=host)
    set_urlconf(get_host(host))
    org = OrganisationFactory()
    user = UserFactory(account_type=account_type.value, organisations=(org,))
    client.force_login(user=user)

    url = reverse("home", host=host)
    response = client.get(url, follow=True)

    if user.is_agent_user:
        assert response.status_code == 200
        assert response.context.get("start_view") == reverse(
            "select-org",
            host=PUBLISH_HOST,
        )
    else:
        assert response.status_code == 200
        assert response.context.get("start_view") == reverse(
            "select-data",
            host=PUBLISH_HOST,
            kwargs={
                "pk1": user.organisation.id,
            },
        )


@pytest.mark.parametrize(
    "dataset_type,view_name",
    (
        (DatasetType.TIMETABLE.value, "feed-list"),
        (DatasetType.AVL.value, "avl:feed-list"),
        (DatasetType.FARES.value, "fares:feed-list"),
    ),
    ids=("Test timetables feed-list", "Test AVL feed-list", "Test fares feed-list"),
)
def test_busy_agent_publish_home_view(client_factory, dataset_type, view_name):
    host = PUBLISH_HOST
    client = client_factory(host=host)
    set_urlconf(get_host(host))
    orgs = OrganisationFactory.create_batch(5)
    user = UserFactory(account_type=AccountType.agent_user.value, organisations=orgs)
    client.force_login(user=user)
    for org in orgs:
        ds = DatasetFactory.create(
            organisation=org, contact=user, dataset_type=dataset_type
        )
        ds.live_revision.published_by = user
        ds.save()

        response = client.get(reverse(view_name, kwargs={"pk1": org.id}, host=host))
        assert response.status_code == 200, "agent can view the feed-list page"
        assert (
            response.context_data["organisation"].name == org.name
        ), "we return the correct organisation"
        assert (
            response.context_data["active_feeds"].count() == 1
        ), "agent can access the organisations dataset."


@pytest.mark.parametrize(
    "dataset_type,expected_view, pathargs, pathkwargs",
    [
        (DatasetType.TIMETABLE.value, "new-feed", [], {"pk1": 1}),
        (DatasetType.AVL.value, "avl:new-feed", [], {"pk1": 1}),
        (DatasetType.FARES.value, "fares:new-feed", [], {"pk1": 1}),
    ],
)
def test_publish_select_data_type_view(
    dataset_type, expected_view, pathargs, pathkwargs, client_factory
):
    host = PUBLISH_HOST
    client = client_factory(host=host)
    org = OrganisationFactory(id=1)
    user = UserFactory(account_type=AccountType.org_admin.value, organisations=(org,))
    client.force_login(user=user)

    url = reverse("select-data", kwargs={"pk1": org.id}, host=host)
    response = client.post(url, data={"dataset_type": str(dataset_type)}, follow=True)
    expected_url, status_code = response.redirect_chain[-1]
    assert expected_url == reverse(expected_view, host=host, kwargs=pathkwargs)
    assert status_code == 302


@pytest.mark.parametrize(
    "pathname,pathargs,pathkwargs",
    [
        ("feed-list", [], {"pk1": 1}),
        ("new-feed", [], {"pk1": 1}),
        ("feed-detail", [], {"pk": 1, "pk1": 1}),
        ("revision-publish-success", [], {"pk": 1, "pk1": 1}),
        ("feed-update", [], {"pk": 1, "pk1": 1}),
        ("revision-update-success", [], {"pk": 1, "pk1": 1}),
        ("feed-download", [], {"pk": 1, "pk1": 1}),
        ("feed-archive", [], {"pk": 1, "pk1": 1}),
        ("feed-archive-success", [], {"pk": 1, "pk1": 1}),
        ("feed-changelog", [], {"pk": 1, "pk1": 1}),
    ],
)
def test_user_gets_403_if_not_orguser(pathname, pathargs, pathkwargs, client_factory):
    # Setup
    host = PUBLISH_HOST
    client = client_factory(host=host)

    # create non-organisation user and sign in.
    user = UserFactory.create(account_type=AccountType.developer.value)
    client.force_login(user=user)

    url = reverse(pathname, args=pathargs, kwargs=pathkwargs, host=host)

    # Test
    response = client.get(url, follow=True)

    # Assert
    assert response.status_code == 403
    assert "403.html" in [t.name for t in response.templates]


@pytest.mark.parametrize(
    "pathname,pathargs,pathkwargs",
    [
        ("feed-detail", [], {}),
        ("feed-update", [], {}),
        ("feed-download", [], {}),
        ("feed-archive", [], {}),
        ("feed-archive-success", [], {}),
        ("feed-changelog", [], {}),
    ],
)
def test_404_returned_if_feed_doesnt_belong_to_orguser(
    pathname, pathargs, pathkwargs, publish_client
):
    """Tests that feeds are not accessible if they do not belong to the
    user's organisation"""
    # Setup
    host = PUBLISH_HOST

    # create organisation user and sign in.
    org = OrganisationFactory()
    user = UserFactory(account_type=AccountType.org_admin.value, organisations=(org,))
    publish_client.force_login(user=user)

    # create a feed which does not belong to the user's org
    another_org = OrganisationFactory()
    feed = DatasetFactory(organisation=another_org)

    url = reverse(
        pathname, args=pathargs, kwargs={"pk": feed.id, "pk1": org.id}, host=host
    )

    response = publish_client.get(url, follow=True)
    assert response.status_code == 404


def test_publish_data_activity_view(client_factory):
    host = PUBLISH_HOST
    client = client_factory(host=host)
    org = OrganisationFactory(id=1)
    user = UserFactory(account_type=AccountType.agent_user.value, organisations=(org,))
    client.force_login(user=user)
    url = reverse("data-activity", kwargs={"pk1": org.id}, host=host)
    response = client.get(url, follow=True)

    assert response.status_code == 200


def test_monthly_breakdown_empty(client_factory, user_factory):
    today = now().date()
    client = client_factory(host=PUBLISH_HOST)
    org = OrganisationFactory()
    user = user_factory(account_type=OrgAdminType, organisations=(org,))
    url = reverse("consumer-interactions", args=[org.id], host=PUBLISH_HOST)
    client.force_login(user=user)
    expected_filename = f"Consumer_metrics_{org.name}_{today:%d%m%y}"
    expected_disposition = f"attachment; filename={expected_filename}.zip"
    expected_files = [
        expected_filename + ".csv",
        "consumermetricsoperatorbreakdown.txt",
    ]

    response = client.get(url)
    response_file = io.BytesIO(b"".join(response.streaming_content))
    assert response.status_code == 200
    assert response.get("Content-Disposition") == expected_disposition
    with zipfile.ZipFile(response_file, "r") as zout:
        assert sorted(zout.namelist()) == expected_files
        with zout.open(expected_filename + ".csv", "r") as fp:
            reader = csv.reader(io.TextIOWrapper(fp, "utf-8"))
            columns, *_ = reader
            assert columns == CSV_HEADERS


def test_present_monthly_breakdown_view(client_factory):
    host = PUBLISH_HOST
    client = client_factory(host=host)
    org = OrganisationFactory()
    org.stats.monthly_breakdown.save("filename", io.StringIO("this is a csv file"))
    org.stats.save()
    user = UserFactory(account_type=AccountType.agent_user.value, organisations=(org,))
    client.force_login(user=user)
    url = reverse("consumer-interactions", kwargs={"pk1": org.id}, host=host)
    response = client.get(url)
    assert response.status_code == 200


class UploadFeedViewTest(TestCase):
    def setUp(self):
        # Set HTTP_HOST on client
        host = get_host(PUBLISH_HOST)
        HTTP_HOST = reverse_host(PUBLISH_HOST)
        settings.DEFAULT_HOST = PUBLISH_HOST
        set_urlconf(host.urlconf)

        self.client.defaults.setdefault("HTTP_HOST", HTTP_HOST)

        # Create organisation user
        self.user = create_verified_org_user()

        # Login into browser session
        self.assertTrue(
            self.client.login(username=self.user.username, password="password")
        )

        self.dataset_unpublished = DatasetFactory.create(
            organisation=self.user.organisation, live_revision=None
        )
        self.dataset_revision = DatasetRevisionFactory.create(
            is_published=False, dataset=self.dataset_unpublished
        )

        # Convenient data
        self.WIZARD_NAME = "feed_upload_wizard"
        self.WIZARD_CURRENT_STEP = f"{self.WIZARD_NAME}-current_step"
        self.WIZARD_GOTO_STEP = "wizard_goto_step"
        self.WIZARD_URL = reverse(
            "new-feed",
            kwargs={"pk1": self.dataset_unpublished.organisation_id},
            host=PUBLISH_HOST,
        )
        self.SELECTED_ITEM = "selected_item"
        self.ITEM_UPLOAD_FILE = FeedUploadForm.UPLOAD_FILE_ITEM_ID
        self.ITEM_URL_LINK = FeedUploadForm.URL_LINK_ITEM_ID

    def go_to_step(self, to_step, from_step=FeedUploadWizard.DESCRIPTION_STEP):
        data = {self.WIZARD_CURRENT_STEP: from_step, self.WIZARD_GOTO_STEP: to_step}
        response = self.client.post(self.WIZARD_URL, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["wizard"]["steps"].current, to_step)

    def test_template(self):
        """
        Test the form wizard is returned to upload the feed using the correct template
        """
        # Setup
        # Test
        response = self.client.get(self.WIZARD_URL)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "publish/feed_form.html")

    def test_upload_step__cancel(self):
        """
        Test 'Cancel' step is rendered user clicks on 'Cancel'
        """
        # Set Up
        self.go_to_step(FeedUpdateWizard.UPLOAD_STEP)

        # Test
        response = self.client.post(
            self.WIZARD_URL,
            {
                self.WIZARD_CURRENT_STEP: FeedUpdateWizard.UPLOAD_STEP,
                "cancel": "cancel",
            },
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        response.context_data["wizard"]["form"].errors.get_json_data()
        assert "publish/feed_publish_cancel.html" in [
            t.name for t in response.templates
        ]

    def test_publish_review_modify(self):
        """
        Test the form wizard is returned to update the revision using the
        correct step
        """
        # Setup
        request_url = reverse(
            "upload-modify",
            host=PUBLISH_HOST,
            kwargs={
                "pk": self.dataset_revision.dataset_id,
                "pk1": self.dataset_unpublished.organisation_id,
            },
        )
        # Test
        response = self.client.get(request_url)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "publish/feed_form.html")
        self.assertEqual(
            response.context["wizard"]["steps"].current, FeedUpdateWizard.UPLOAD_STEP
        )


class UpdateFeedViewTest(TestCase):
    def setUp(self):
        # Set HTTP_HOST on client
        host = get_host(PUBLISH_HOST)
        HTTP_HOST = reverse_host(PUBLISH_HOST)
        settings.DEFAULT_HOST = PUBLISH_HOST
        set_urlconf(host.urlconf)

        self.client.defaults.setdefault("HTTP_HOST", HTTP_HOST)

        # Create organisation user
        self.user = create_verified_org_user()

        # Login into browser session
        self.assertTrue(
            self.client.login(username=self.user.username, password="password")
        )

        # Create a Feed
        file_path = f"{ETL_TEST_DATA_DIR}ea_20-1A-A-y08-1.xml"
        self.dataset = DatasetFactory.create(
            organisation=self.user.organisation,
            live_revision__upload_file__from_path=file_path,
        )
        self.dataset_unpublished = DatasetFactory.create(
            organisation=self.user.organisation, live_revision=None
        )
        self.dataset_revision = DatasetRevisionFactory.create(
            is_published=False, dataset=self.dataset_unpublished
        )
        self.assertTrue(Dataset.objects.exists())

        # Convenient data
        self.WIZARD_NAME = "feed_update_wizard"
        self.WIZARD_CURRENT_STEP = f"{self.WIZARD_NAME}-current_step"
        self.WIZARD_GOTO_STEP = "wizard_goto_step"
        self.WIZARD_URL = reverse(
            "feed-update",
            host=PUBLISH_HOST,
            kwargs={"pk": self.dataset.id, "pk1": self.dataset.organisation_id},
        )
        self.SELECTED_ITEM = "selected_item"
        self.ITEM_UPLOAD_FILE = FeedUploadForm.UPLOAD_FILE_ITEM_ID
        self.ITEM_URL_LINK = FeedUploadForm.URL_LINK_ITEM_ID

    def go_to_step(self, to_step, from_step=FeedUpdateWizard.COMMENT_STEP):
        response = self.client.post(
            self.WIZARD_URL,
            {self.WIZARD_CURRENT_STEP: from_step, self.WIZARD_GOTO_STEP: to_step},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["wizard"]["steps"].current, to_step)

    def test_template(self):
        """
        Test the form wizard is returned to update the feed using the correct template
        """
        # Setup
        # Test
        response = self.client.get(self.WIZARD_URL)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "publish/feed_form.html")

    def test_upload_step__no_change(self):
        """
        Test an error is produced when user submits the form step without
        choosing an option.
        """
        # Set Up
        self.go_to_step(FeedUpdateWizard.UPLOAD_STEP)

        # Test
        response = self.client.post(
            self.WIZARD_URL,
            {
                self.WIZARD_CURRENT_STEP: FeedUpdateWizard.UPLOAD_STEP,
                "submit": "submit",
            },
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        error_data = response.context_data["wizard"]["form"].errors.get_json_data()
        self.assertEqual(
            response.context["wizard"]["steps"].current, FeedUpdateWizard.UPLOAD_STEP
        )
        self.assertEqual(
            error_data,
            {"url_link": [{"message": "Please provide a file or url", "code": "all"}]},
        )

    def test_upload_step__missing_file(self):
        """
        Test an error is produced when user submits the form step without
        uploading a file (but upload_file option is
        selected).

        This test is particularly important in the update wizard to test the form
        has received a newly uploaded file
        """
        # Set Up
        self.go_to_step(FeedUpdateWizard.UPLOAD_STEP)

        # Test
        response = self.client.post(
            self.WIZARD_URL,
            {
                self.WIZARD_CURRENT_STEP: FeedUpdateWizard.UPLOAD_STEP,
                self.SELECTED_ITEM: self.ITEM_UPLOAD_FILE,
                "submit": "submit",
            },
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        error_data = response.context_data["wizard"]["form"].errors.get_json_data()
        self.assertEqual(
            response.context["wizard"]["steps"].current, FeedUpdateWizard.UPLOAD_STEP
        )
        self.assertEqual(
            error_data,
            {"upload_file": [{"message": "Please provide a file", "code": "required"}]},
        )

    def test_upload_step__invalid_file(self):
        """
        Test an error is produced when user submits an invalid file
        (incorrect file extension)
        """
        # Set Up
        self.go_to_step(FeedUpdateWizard.UPLOAD_STEP)

        # Test
        with open(f"{ETL_TEST_DATA_DIR}invalid_extension.txt", "r") as fp:
            response = self.client.post(
                self.WIZARD_URL,
                {
                    self.WIZARD_CURRENT_STEP: FeedUpdateWizard.UPLOAD_STEP,
                    self.SELECTED_ITEM: self.ITEM_UPLOAD_FILE,
                    "upload_file": fp,
                    "submit": "submit",
                },
            )

        # Assert
        self.assertEqual(response.status_code, 200)
        error_data = response.context_data["wizard"]["form"].errors.get_json_data()
        self.assertEqual(
            response.context["wizard"]["steps"].current, FeedUpdateWizard.UPLOAD_STEP
        )
        self.assertEqual(
            error_data,
            {
                "upload_file": [
                    {
                        "code": "invalid",
                        "message": "The file is not in a correct format",
                    }
                ]
            },
        )

    def test_upload_step__valid_file(self):
        """
        Test form submits correctly when provided a valid file.
        """
        # Set Up
        self.go_to_step(FeedUpdateWizard.UPLOAD_STEP)

        # Test
        # Re-uploading the same file, this should be irrelevant
        with open(f"{ETL_TEST_DATA_DIR}ea_20-1A-A-y08-1.xml", "r") as fp:
            response = self.client.post(
                self.WIZARD_URL,
                {
                    self.WIZARD_CURRENT_STEP: FeedUpdateWizard.UPLOAD_STEP,
                    self.SELECTED_ITEM: self.ITEM_UPLOAD_FILE,
                    "upload_file": fp,
                    "submit": "submit",
                },
            )

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["wizard"]["steps"].current, FeedUpdateWizard.COMMENT_STEP
        )

    def test_upload_step__missing_url(self):
        """
        Test an error is produced when user submits the form step
        without providing a url (but url_link option is selected).
        """
        # Set Up
        self.go_to_step(FeedUpdateWizard.UPLOAD_STEP)

        # Test
        response = self.client.post(
            self.WIZARD_URL,
            {
                self.WIZARD_CURRENT_STEP: FeedUpdateWizard.UPLOAD_STEP,
                self.SELECTED_ITEM: self.ITEM_URL_LINK,
                "submit": "submit",
            },
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        error_data = response.context_data["wizard"]["form"].errors.get_json_data()
        self.assertEqual(
            response.context["wizard"]["steps"].current, FeedUpdateWizard.UPLOAD_STEP
        )
        self.assertEqual(
            error_data,
            {
                "url_link": [
                    {"message": "Please provide a URL link", "code": "required"}
                ]
            },
        )

    def test_upload_step__invalid_url(self):
        """
        Test an error is produced when user submits the form step with an invalid a url
        """
        # Set Up
        self.go_to_step(FeedUpdateWizard.UPLOAD_STEP)

        # Test
        response = self.client.post(
            self.WIZARD_URL,
            {
                self.WIZARD_CURRENT_STEP: FeedUpdateWizard.UPLOAD_STEP,
                self.SELECTED_ITEM: self.ITEM_URL_LINK,
                "url_link": "incorrect-url",
                "submit": "submit",
            },
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        error_data = response.context_data["wizard"]["form"].errors.get_json_data()
        self.assertEqual(
            response.context["wizard"]["steps"].current, FeedUpdateWizard.UPLOAD_STEP
        )
        self.assertEqual(
            error_data,
            {
                "url_link": [
                    {"message": "Enter a valid URL to your data set", "code": "invalid"}
                ]
            },
        )

    def test_upload_step__valid_url(self):
        """
        Test form submits correctly when provided a valid url.
        """
        # Set Up
        self.go_to_step(FeedUpdateWizard.UPLOAD_STEP)

        # Test
        url_link = (
            "http://product.itoworld.com/product/data/files/"
            "ea_20-204-_-y08-1.xml?t=file&g=test_txc&p=:ea_20-204-_-y08-1.xml"
            "&u=144&key=4e9207c6cb0f7157ef85c657dddad3bd"
        )

        response = self.client.post(
            self.WIZARD_URL,
            {
                self.WIZARD_CURRENT_STEP: FeedUpdateWizard.UPLOAD_STEP,
                self.SELECTED_ITEM: self.ITEM_URL_LINK,
                "url_link": url_link,
                "submit": "submit",
            },
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["wizard"]["steps"].current, FeedUpdateWizard.COMMENT_STEP
        )

    def test_upload_step__empty_comment(self):
        """
        Test form complains on empty comment
        """
        # Set Up
        self.go_to_step(FeedUpdateWizard.COMMENT_STEP)

        # Test
        response = self.client.post(
            self.WIZARD_URL,
            {
                self.WIZARD_CURRENT_STEP: FeedUpdateWizard.COMMENT_STEP,
                "comment": "",
                "submit": "submit",
            },
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["form"].errors["comment"][0],
            "Enter a comment in the box below",
        )

    def test_update_review_modify(self):
        """
        Test the form wizard is returned to update the revision using the correct step
        """
        # Setup
        request_url = reverse(
            "update-modify",
            host=PUBLISH_HOST,
            kwargs={
                "pk": self.dataset_revision.dataset_id,
                "pk1": self.dataset_unpublished.organisation_id,
            },
        )
        # Test
        response = self.client.get(request_url)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "publish/feed_form.html")
        self.assertEqual(
            response.context["wizard"]["steps"].current, FeedUpdateWizard.UPLOAD_STEP
        )


class TestPublishView:
    # TODO Need to fix this unit test
    # def test_no_permission(self, client_factory):
    #     # Setup
    #     host = PUBLISH_HOST
    #     client = client_factory(host=host)
    #     user = UserFactory.create()  # default developer account created in factory
    #     client.force_login(user=user)
    #
    #     url = reverse('feed-list', host=host)
    #
    #     # Test
    #     response = client.get(url)
    #
    #     # Assert
    #     assert response.status_code == 403

    def test_active_feeds(self, client_factory):
        # Setup
        host = PUBLISH_HOST
        client = client_factory(host=host)

        # create an organisationq
        org = OrganisationFactory.create()

        # create feeds
        DatasetFactory(organisation=org, live_revision__status=FeedStatus.live.value)
        DatasetFactory(organisation=org, live_revision__status=FeedStatus.warning.value)
        DatasetFactory(
            organisation=org, live_revision__status=FeedStatus.expiring.value
        )
        DatasetFactory(organisation=org, live_revision__status=FeedStatus.expired.value)

        # create revision with error
        DatasetRevisionFactory(
            dataset__organisation=org, status=FeedStatus.error.value, is_published=False
        )

        user = UserFactory(
            account_type=AccountType.org_staff.value, organisations=(org,)
        )
        client.force_login(user=user)

        url = reverse("feed-list", kwargs={"pk1": org.id}, host=host)

        # Test
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert "publish/feed_list.html" in [t.name for t in response.templates]
        assert (
            response.context_data["active_feeds_table"].rows.data._length == 3
        )  # excludes expired feeds
        assert response.context_data["tab"] == "active"  # default tab is active

    def test_context_data_on_list_view(self, client_factory):
        host = PUBLISH_HOST
        client = client_factory(host=host)

        org = OrganisationFactory.create()

        live_ds = DatasetRevisionFactory(
            dataset__organisation=org, status=FeedStatus.live.value, is_published=True
        )

        DatasetRevisionFactory(
            dataset__organisation=org, status=FeedStatus.error.value, is_published=False
        )

        user = OrgStaffFactory(organisations=[org])
        client.force_login(user=user)

        valid_api_hits = 5
        APIRequestFactory.create_batch(valid_api_hits, requestor=user)

        valid_bulk_downloads = 3
        ResourceRequestCounterFactory.create(
            counter=valid_bulk_downloads,
            requestor=user,
            path_info=reverse_path("downloads-bulk", host=DATA_HOST),
        )
        valid_dataset_downloads = 2
        ResourceRequestCounterFactory.create(
            counter=valid_dataset_downloads,
            requestor=user,
            path_info=reverse_path(
                "feed-download", kwargs={"pk": live_ds.dataset.id}, host=DATA_HOST
            ),
        )

        valid_active_subs = 2
        DatasetSubscriptionFactory.create_batch(
            valid_active_subs, dataset=live_ds.dataset
        )

        url = reverse("feed-list", kwargs={"pk1": org.id}, host=host)
        task_generate_consumer_interaction_stats()
        response = client.get(url)
        organisation = response.context["organisation"]

        assert organisation.stats.weekly_api_hits == valid_api_hits
        assert organisation.total_subscriptions == valid_active_subs
        assert (
            organisation.stats.weekly_downloads
            == valid_bulk_downloads + valid_dataset_downloads
        )

    # Skipping because active feeds shouldn't include feeds with status indexing.
    @pytest.mark.skip
    def test_has_pending_feeds_respects_pagination(self, client_factory):
        # Setup
        host = PUBLISH_HOST
        client = client_factory(host=host)

        # create an organisationq
        org = OrganisationFactory.create()
        # create an indexing feed with name that will be on first page
        DatasetFactory(
            organisation=org,
            live_revision__status=FeedStatus.indexing.value,
            live_revision__name="__",
        )
        # create a whole bunch more
        DatasetFactory.create_batch(
            12,
            organisation=org,
            live_revision__status=FeedStatus.live.value,
            name=factory.sequence(lambda n: f"feed{n}"),
        )

        user = UserFactory(
            account_type=AccountType.org_staff.value, organisations=(org,)
        )
        client.force_login(user=user)

        url = reverse("feed-list", host=host)

        # Test
        response1 = client.get(url)
        response2 = client.get(url + "?page=2")

        # Assert
        assert response1.context_data["has_pending_feeds"] is True
        assert response2.context_data["has_pending_feeds"] is False

    def test_archive_feeds(self, client_factory):
        host = PUBLISH_HOST
        client = client_factory(host=host)
        org = OrganisationFactory.create()

        statuses = [
            FeedStatus.live,
            FeedStatus.warning,
            FeedStatus.expiring,
            FeedStatus.expired,
            FeedStatus.expired,  # N.B. 2 expired feeds
            FeedStatus.error,
        ]
        for status in statuses:
            DatasetFactory(organisation=org, live_revision__status=status.value)

        user = UserFactory(
            account_type=AccountType.org_staff.value, organisations=(org,)
        )
        client.force_login(user=user)

        url = reverse("feed-list", kwargs={"pk1": org.id}, host=host)

        response = client.get(url, data={"tab": "archive"})
        assert response.status_code == 200
        assert "publish/feed_list.html" in [t.name for t in response.templates]
        assert (
            response.context_data["active_feeds_table"].rows.data._length == 2
        )  # includes only expired feeds
        assert (
            response.context_data["tab"] == "archive"
        )  # archived tab is passed in request

    @pytest.mark.parametrize(
        "dataset_revision_factory, url_name",
        [
            (DatasetRevisionFactory, "feed-list"),
            (AVLDatasetRevisionFactory, "avl:feed-list"),
            (FaresDatasetRevisionFactory, "fares:feed-list"),
        ],
    )
    def test_consistent_pagination(
        self, client_factory, dataset_revision_factory, url_name
    ):
        """
        Upload lots of datasets and navigate to the list page. Then collect the
        dataset ids one page at a time. The ids should not be repeated or dropped and
        therefore there should be the same unique ids as datasets.
        This test protects against:
        https://itoworld.atlassian.net/browse/BODP-5116
        """
        number_of_files = 201
        results_per_page = 10
        number_of_pages = math.ceil(number_of_files / results_per_page)

        host = PUBLISH_HOST
        client = client_factory(host=host)
        org = OrganisationFactory.create()
        user = UserFactory(
            account_type=AccountType.org_staff.value, organisations=(org,)
        )

        dataset_revision_factory.create_batch(
            number_of_files,
            dataset__organisation=org,
            dataset__contact=user,
            status=INACTIVE,
        )

        client.force_login(user=user)
        url = reverse(
            url_name,
            args=[org.id],
            host=host,
        )
        ids = []
        for page in range(1, number_of_pages + 1):
            response = client.get(url, data={"tab": "archive", "page": page})
            data = response.context_data["active_feeds_table"].page.object_list.data
            ids += list(data.values_list("id", flat=True))

        assert len(set(ids)) == len(ids) == number_of_files

    def test_seasonal_services_counter(self, client_factory):
        # Setup
        host = PUBLISH_HOST
        client = client_factory(host=host)

        # create an organisation
        org = OrganisationFactory.create()

        # create seasonal services
        SeasonalServiceFactory(licence__organisation=org)
        SeasonalServiceFactory(licence__organisation=org)
        SeasonalServiceFactory(licence__organisation=org)
        SeasonalServiceFactory(licence__organisation=org)

        user = UserFactory(
            account_type=AccountType.org_staff.value, organisations=(org,)
        )
        client.force_login(user=user)

        url = reverse("feed-list", kwargs={"pk1": org.id}, host=host)

        # Test
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert response.context_data["seasonal_services_counter"] == 4


class TestFeedArchiveView:
    host = PUBLISH_HOST

    def setup(self):
        self.org = OrganisationFactory()
        self.agent = AgentUserFactory(
            email="ms_agent@test.test", organisations=(self.org,)
        )
        self.staff = OrgStaffFactory(
            email="mr_staff@test.test", organisations=(self.org,)
        )
        AgentUserInviteFactory(
            agent=self.agent,
            organisation=self.org,
            inviter=self.staff,
            status=AgentUserInvite.ACCEPTED,
        )
        self.dev = UserFactory(email="dr_dev@test.test")

        revision = DatasetRevisionFactory(
            dataset__organisation=self.org,
            dataset__contact=self.staff,
            dataset__subscribers=(self.dev,),
        )
        self.feed = revision.dataset
        self.url = reverse(
            "feed-archive",
            host=self.host,
            kwargs={"pk": self.feed.id, "pk1": self.org.id},
        )

    def test_archive_view_archives_dataset(self, publish_client):
        publish_client.force_login(user=self.staff)
        response = publish_client.post(self.url, data={"submit": "submit"}, follow=True)
        fished_out_feed = Dataset.objects.get(pk=self.feed.id)

        assert response.status_code == 200
        assert fished_out_feed.live_revision.status == "inactive"
        assert response.context["back_to_data_sets"] == reverse(
            "feed-list", host=self.host, kwargs={"pk1": self.org.id}
        )

    def test_archive_dataset_with_drafts(self, publish_client):
        current_time = now()
        host = PUBLISH_HOST

        org = OrganisationFactory.create()

        with freeze_time(current_time - timedelta(seconds=1)):
            draft_revision = DatasetRevisionFactory.create(
                is_published=False, status=FeedStatus.draft.value, published_at=None
            )

        with freeze_time(current_time):
            feed1 = DatasetFactory(
                organisation=org, live_revision__status=FeedStatus.live.value
            )
        # for some reason when the whole test suite runs the draft revision
        # and the revision associated with the dataset factory have the same
        # created time which violates a unique constraint
        feed1.revisions.add(draft_revision)

        user = UserFactory.create(
            account_type=AccountType.org_staff.value, organisations=(org,)
        )
        publish_client.force_login(user=user)

        assert feed1.revisions.count() == 2  # 1 published, 1 draft
        assert feed1.live_revision.status == "live"

        url = reverse("feed-archive", host=host, kwargs={"pk": feed1.id, "pk1": org.id})

        response = publish_client.post(url, data={"submit": "submit"}, follow=True)
        fished_out_feed = Dataset.objects.get(pk=feed1.id)

        assert (
            fished_out_feed.revisions.count() == 1
        )  # 1 published; draft revisions deleted
        assert response.status_code == 200
        assert fished_out_feed.live_revision.status == "inactive"
        assert response.context["back_to_data_sets"] == reverse(
            "feed-list", host=host, kwargs={"pk1": org.id}
        )

    @freeze_time("2020-02-29 18:00:00")
    def test_archive_datasets_sends_notification_emails(
        self, publish_client, bods_mailoutbox
    ):
        publish_client.force_login(user=self.staff)
        publish_client.post(self.url, data={"submit": "submit"})

        staff, agent, dev = bods_mailoutbox
        expected_subject = "Published data set has been deactivated"

        assert staff.to[0] == self.staff.email
        assert staff.subject == expected_subject

        assert agent.to[0] == self.agent.email
        assert agent.subject == expected_subject

        assert dev.to[0] == self.dev.email
        assert agent.subject == expected_subject

        for email in bods_mailoutbox:
            line_of_interest = email.body.splitlines()[-4]
            expired_on = line_of_interest[13:]
            assert expired_on == "29-02-2020 18:00"

    def test_archive_datasets_sends_one_email_when_contact_is_agent(
        self, publish_client, mailoutbox
    ):
        self.feed.contact = self.agent
        self.feed.subscribers.set([])
        self.feed.save()

        publish_client.force_login(user=self.staff)
        publish_client.post(self.url, data={"submit": "submit"})

        assert len(mailoutbox) == 1
        mail = mailoutbox[0]

        assert mail.subject == "Published data set has been deactivated"
        assert mail.to[0] == self.agent.email
        assert self.org.name in mail.body


def test_report_dq_and_score_report_id_are_none_no_summary(client_factory):
    org_user = create_verified_org_user()
    dataset = DatasetFactory.create(organisation=org_user.organisation)
    revision = DatasetRevisionFactory.create(
        dataset=dataset, status=FeedStatus.live.value
    )
    DatasetETLTaskResultFactory(revision=revision)
    DataQualityReportFactory(revision=revision, summary=None, score=0)
    client = client_factory(host=PUBLISH_HOST)
    client.force_login(org_user)
    url = reverse(
        "feed-detail",
        kwargs={"pk1": org_user.organisation.id, "pk": dataset.id},
        host=PUBLISH_HOST,
    )

    response = client.get(url)

    assert response.status_code == 200
    assert response.context_data["dq_score"] is None
    assert response.context_data["report_id"] is None


class TestFeedDeleteView:
    host = PUBLISH_HOST

    def setup(self):
        self.org = OrganisationFactory.create()
        self.updater = UserFactory(
            account_type=AccountType.org_staff.value,
            organisations=(self.org,),
            email="mr_updater@test.test",
        )
        self.deleter = UserFactory(
            account_type=AccountType.org_staff.value,
            organisations=(self.org,),
            email="ms_deleter@test.test",
        )
        self.feed = DraftDatasetFactory(organisation=self.org, contact=self.updater)

    def test_one_email_is_sent_if_deleter_is_updated(self, publish_client, mailoutbox):
        publish_client.force_login(user=self.deleter)

        feed = DraftDatasetFactory(organisation=self.org, contact=self.deleter)
        url = reverse(
            "revision-delete",
            host=self.host,
            kwargs={"pk": feed.id, "pk1": self.org.id},
        )

        response = publish_client.post(url, data={"submit": "submit"})
        assert response.status_code == 302
        assert len(mailoutbox) == 1
        assert mailoutbox[0].to[0] == "ms_deleter@test.test"
        assert (
            mailoutbox[0].subject
            == "You deleted an unpublished data set – no action required"
        )

    def test_confirmation_displays_correct_name(self, publish_client):
        publish_client.force_login(user=self.deleter)

        url = reverse(
            "revision-delete",
            host=self.host,
            kwargs={"pk": self.feed.id, "pk1": self.org.id},
        )

        response = publish_client.get(url)
        assert self.feed.revisions.last().name in response.content.decode("utf-8")

    def test_feed_is_successfully_deleted(self, publish_client, mailoutbox):
        publish_client.force_login(user=self.deleter)

        url = reverse(
            "revision-delete",
            host=self.host,
            kwargs={"pk": self.feed.id, "pk1": self.org.id},
        )
        response = publish_client.post(url, data={"submit": "submit"})
        assert response.status_code == 302
        deleter, updater = mailoutbox
        assert deleter.to[0] == "ms_deleter@test.test"
        assert (
            deleter.subject
            == "You deleted an unpublished data set – no action required"
        )
        assert updater.to[0] == "mr_updater@test.test"
        assert updater.subject == (
            ""
            "A data set you updated has been deleted from the Bus Open Data Service"
            " – no action required"
        )


class TestPublishRevisionView:
    def test_admin_areas_for_revision(self, publish_client):
        host = PUBLISH_HOST
        org = OrganisationFactory.create()
        admin_areas = [
            AdminAreaFactory(name=name) for name in ["Cambridge", "London", "Leeds"]
        ]
        feed1 = DatasetFactory(organisation=org, live_revision=None)

        revision = DatasetRevisionFactory(
            dataset=feed1, is_published=False, admin_areas=admin_areas
        )

        DatasetETLTaskResultFactory(revision=revision)
        user = UserFactory.create(
            account_type=AccountType.org_staff.value, organisations=(org,)
        )
        publish_client.force_login(user=user)

        url = reverse(
            "revision-publish", host=host, kwargs={"pk": feed1.id, "pk1": org.id}
        )
        response = publish_client.get(url)

        assert response.status_code == 200
        assert response.context_data["admin_areas"] == "Cambridge, Leeds, London"

    def test_unsafe_get_doesnt_publish_feed(self, publish_client):
        host = PUBLISH_HOST
        org = OrganisationFactory.create()
        feed1 = DatasetFactory(organisation=org, live_revision=None)
        revision1 = DatasetRevisionFactory(dataset=feed1, is_published=False)
        DatasetETLTaskResultFactory(revision=revision1)

        user = UserFactory.create(
            account_type=AccountType.org_staff.value, organisations=(org,)
        )
        publish_client.force_login(user=user)

        url = reverse(
            "revision-publish", host=host, kwargs={"pk": feed1.id, "pk1": org.id}
        )

        # Test
        response = publish_client.get(url)
        fished_out_revision = DatasetRevision.objects.get(dataset_id=feed1.id)

        # Assert
        assert response.status_code == 200
        assert fished_out_revision.is_published is False


class TestFeedDownloadView:
    def test_download_for_review(self, client_factory):
        # Setup
        then = now() - timedelta(days=1)
        dataset = DatasetFactory(live_revision=None)
        revision1 = DatasetRevisionFactory(
            status=FeedStatus.live.value,
            dataset=dataset,
            created=then,
            is_published=True,
            published_at=then,
            upload_file__filename="myfile.txt",
            upload_file__data=b"content1",
        )
        DatasetRevisionFactory(
            status=FeedStatus.success.value,
            dataset=dataset,
            is_published=False,
            upload_file__filename="myfile.txt",
            upload_file__data=b"content2",
        )

        host = DATA_HOST
        client = client_factory(host=host)
        query = QueryDict("", mutable=True)
        query.update({"is_review": "true"})

        url = "{base_url}?{querystring}".format(
            base_url=reverse(
                "feed-download",
                kwargs={"pk": revision1.dataset.id},
                host=host,
            ),
            querystring=query.urlencode(),
        )

        # Test
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert (
            response.getvalue() == b"content2"
        )  # is_review=true, so take the latest dataset revision


class TestEditLiveRevisionDescriptionView:
    def test_edit_live_revision_desc_success(self, publish_client):
        host = PUBLISH_HOST

        # create an organisation
        org = OrganisationFactory.create()

        # create feeds
        feed1 = DatasetFactory(
            organisation=org,
            live_revision__status=FeedStatus.live.value,
            live_revision__description="Old description",
            live_revision__short_description="Old short description",
        )
        DataQualityReportFactory(revision=feed1.live_revision)

        user = UserFactory.create(
            account_type=AccountType.org_staff.value, organisations=(org,)
        )
        publish_client.force_login(user=user)

        url = reverse("dataset-edit", host=host, kwargs={"pk": feed1.id, "pk1": org.id})

        data = {
            "submit": "submit",
            "description": "New description",
            "short_description": "New Short Description",
        }

        response = publish_client.post(
            url,
            data=data,
            follow=True,
        )
        fished_out_feed = Dataset.objects.get(pk=feed1.id)
        assert response.status_code == 200
        assert "publish/dataset_detail/index.html" in [
            t.name for t in response.templates
        ]
        assert fished_out_feed.live_revision.description == data["description"]
        assert (
            fished_out_feed.live_revision.short_description == data["short_description"]
        )

    def test_edit_live_revision_desc_cancel(self, publish_client):
        host = PUBLISH_HOST

        # create an organisation
        org = OrganisationFactory.create()

        # create feeds
        feed1 = DatasetFactory(
            organisation=org,
            live_revision__status=FeedStatus.live.value,
            live_revision__description="Old description",
            live_revision__short_description="Old short description",
        )
        DataQualityReportFactory(revision=feed1.live_revision)

        user = UserFactory.create(
            account_type=AccountType.org_staff.value, organisations=(org,)
        )
        publish_client.force_login(user=user)

        url = reverse("dataset-edit", host=host, kwargs={"pk": feed1.id, "pk1": org.id})

        data = {
            "cancel": "cancel",
            "description": "New description",
            "short_description": "New Short Description",
        }

        response = publish_client.post(
            url,
            data=data,
            follow=True,
        )
        fished_out_feed = Dataset.objects.get(pk=feed1.id)
        assert response.status_code == 200
        assert "publish/dataset_detail/index.html" in [
            t.name for t in response.templates
        ]
        assert (
            fished_out_feed.live_revision.description == feed1.live_revision.description
        )
        assert (
            fished_out_feed.live_revision.short_description
            == feed1.live_revision.short_description
        )


class TestEditDraftRevisionDescriptionView:
    def test_edit_draft_revision_desc_success(self, publish_client):
        host = PUBLISH_HOST

        # create an organisation
        org = OrganisationFactory.create()

        # create feeds
        feed1 = DatasetFactory(organisation=org, live_revision=None)

        DatasetRevisionFactory(
            status=FeedStatus.draft.value,
            description="Old description",
            short_description="Old short description",
            is_published=False,
            dataset=feed1,
        )

        user = UserFactory.create(
            account_type=AccountType.org_staff.value, organisations=(org,)
        )
        publish_client.force_login(user=user)

        url = reverse(
            "revision-edit", host=host, kwargs={"pk": feed1.id, "pk1": org.id}
        )

        data = {
            "submit": "submit",
            "description": "New description",
            "short_description": "New Short Description",
        }

        response = publish_client.post(
            url,
            data=data,
            follow=True,
        )
        fished_out_feed = Dataset.objects.get(pk=feed1.id)
        assert response.status_code == 200
        assert "publish/revision_review/index.html" in [
            t.name for t in response.templates
        ]
        assert fished_out_feed.revisions.latest().description == data["description"]
        assert (
            fished_out_feed.revisions.latest().short_description
            == data["short_description"]
        )

    def test_edit_draft_revision_desc_cancel(self, publish_client):
        host = PUBLISH_HOST

        # create an organisation
        org = OrganisationFactory.create()

        # create feeds
        feed1 = DatasetFactory(organisation=org, live_revision=None)

        revision = DatasetRevisionFactory(
            status=FeedStatus.draft.value,
            description="Old description",
            short_description="Old short description",
            is_published=False,
            dataset=feed1,
        )

        user = UserFactory.create(
            account_type=AccountType.org_staff.value, organisations=(org,)
        )
        publish_client.force_login(user=user)

        url = reverse(
            "revision-edit", host=host, kwargs={"pk": feed1.id, "pk1": org.id}
        )

        data = {
            "cancel": "cancel",
            "description": "New description",
            "short_description": "New Short Description",
        }

        response = publish_client.post(
            url,
            data=data,
            follow=True,
        )
        fished_out_feed = Dataset.objects.get(pk=feed1.id)
        assert response.status_code == 200
        assert "publish/revision_review/index.html" in [
            t.name for t in response.templates
        ]
        assert fished_out_feed.revisions.latest().description == revision.description
        assert (
            fished_out_feed.revisions.latest().short_description
            == revision.short_description
        )

    def test_edit_draft_revision_desc_cancel_has_correct_previous_step(
        self, publish_client
    ):
        host = PUBLISH_HOST
        org = OrganisationFactory.create()
        feed1 = DatasetFactory(organisation=org, live_revision=None)
        DatasetRevisionFactory(
            status=FeedStatus.draft.value,
            description="Old description",
            short_description="Old short description",
            is_published=False,
            dataset=feed1,
        )
        user = UserFactory.create(
            account_type=AccountType.org_staff.value, organisations=(org,)
        )
        publish_client.force_login(user=user)

        url = reverse(
            "upload-modify", host=host, kwargs={"pk": feed1.id, "pk1": org.id}
        )
        response = publish_client.post(
            url,
            data={
                "cancel": "cancel",
                "timetable_upload_modify-current_step": "upload",
            },
            follow=True,
        )
        assert response.context["previous_step"] == "upload"

    @pytest.mark.skip
    def test_edit_draft_revision_for_published_dataset_desc_success(
        self, publish_client
    ):
        host = PUBLISH_HOST

        # create an organisation
        org = OrganisationFactory.create()

        # create feeds
        feed1 = DatasetFactory(organisation=org)

        DatasetRevisionFactory(
            status=FeedStatus.draft.value,
            description="Old description",
            short_description="Old short description",
            is_published=False,
            dataset=feed1,
        )

        user = UserFactory.create(
            account_type=AccountType.org_staff.value, organisations=(org,)
        )
        publish_client.force_login(user=user)

        url = reverse(
            "revision-edit", host=host, kwargs={"pk": feed1.id, "pk1": org.id}
        )

        data = {
            "submit": "submit",
            "description": "New description",
            "short_description": "New Short Description",
        }

        response = publish_client.post(
            url,
            data=data,
            follow=True,
        )
        fished_out_feed = Dataset.objects.get(pk=feed1.id)
        assert response.status_code == 200
        assert "publish/revision_review/index.html" in [
            t.name for t in response.templates
        ]
        assert fished_out_feed.revisions.latest().description == data["description"]
        assert (
            fished_out_feed.revisions.latest().short_description
            == data["short_description"]
        )


def test_require_attention_empty_search_box(publish_client):
    # Setup
    host = PUBLISH_HOST
    org1 = OrganisationFactory(id=1)
    user = UserFactory(account_type=OrgStaffType, organisations=(org1,))

    total_services = 7
    licence_number = "PD5000229"
    all_service_codes = [f"{licence_number}:{n:03}" for n in range(total_services)]
    BODSLicenceFactory(organisation=org1, number=licence_number)
    dataset1 = DatasetFactory(organisation=org1)
    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[0],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
    )
    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[1],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
    )
    dataset2 = DraftDatasetFactory(organisation=org1)
    TXCFileAttributesFactory(
        revision=dataset2.revisions.last(), service_code=all_service_codes[2]
    )
    live_revision = DatasetRevisionFactory(dataset=dataset2)
    TXCFileAttributesFactory(
        revision=live_revision,
        service_code=all_service_codes[3],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
    )
    otc_lic1 = LicenceModelFactory(number=licence_number)
    for code in all_service_codes:
        ServiceModelFactory(
            licence=otc_lic1, registration_number=code.replace(":", "/")
        )

    publish_client.force_login(user=user)
    url = reverse("requires-attention", host=host, kwargs={"pk1": org1.id})
    response = publish_client.get(url, data={"q": ""}, follow=True)

    assert response.status_code == 200
    assert len(response.context["view"].object_list) == 4
    assert response.context["services_require_attention_percentage"] == 58


def test_require_attention_field_in_search_box(publish_client):
    # Setup
    host = PUBLISH_HOST
    org1 = OrganisationFactory(id=1)
    user = UserFactory(account_type=OrgStaffType, organisations=(org1,))

    total_services = 7
    licence_number = "PD5000229"
    all_service_codes = [f"{licence_number}:{n:03}" for n in range(total_services)]
    BODSLicenceFactory(organisation=org1, number=licence_number)
    dataset1 = DatasetFactory(organisation=org1)
    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[0],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
    )
    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[1],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
    )
    dataset2 = DraftDatasetFactory(organisation=org1)
    TXCFileAttributesFactory(
        revision=dataset2.revisions.last(), service_code=all_service_codes[2]
    )
    live_revision = DatasetRevisionFactory(dataset=dataset2)
    TXCFileAttributesFactory(
        revision=live_revision,
        service_code=all_service_codes[3],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
    )
    otc_lic1 = LicenceModelFactory(number=licence_number)
    for code in all_service_codes:
        ServiceModelFactory(
            licence=otc_lic1, registration_number=code.replace(":", "/")
        )

    publish_client.force_login(user=user)
    url = reverse("requires-attention", host=host, kwargs={"pk1": org1.id})
    response = publish_client.get(url, data={"q": "006"}, follow=True)

    assert response.status_code == 200
    assert len(response.context["table"].data) == 1
    assert response.context["services_require_attention_percentage"] == 58


def test_require_attention_search_no_results(publish_client):
    # Setup
    host = PUBLISH_HOST
    org1 = OrganisationFactory(id=1)
    user = UserFactory(account_type=OrgStaffType, organisations=(org1,))

    total_services = 3
    licence_number = "PD5000229"
    all_service_codes = [f"{licence_number}:{n:03}" for n in range(total_services)]
    BODSLicenceFactory(organisation=org1, number=licence_number)
    dataset1 = DatasetFactory(organisation=org1)
    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[0],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
    )
    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[1],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
    )
    otc_lic1 = LicenceModelFactory(number=licence_number)
    for code in all_service_codes:
        ServiceModelFactory(
            licence=otc_lic1, registration_number=code.replace(":", "/")
        )

    publish_client.force_login(user=user)
    url = reverse("requires-attention", host=host, kwargs={"pk1": org1.id})
    response = publish_client.get(url, data={"q": "xxxYYyzz123"}, follow=True)

    assert response.status_code == 200
    assert len(response.context["table"].data) == 0
    assert response.context["services_require_attention_percentage"] == 34


def test_require_attention_seasonal_services(publish_client):
    # Setup
    host = PUBLISH_HOST
    org1 = OrganisationFactory(id=1)
    user = UserFactory(account_type=OrgStaffType, organisations=(org1,))
    today = now().date()
    month = now().date() + timedelta(weeks=4)
    two_months = now().date() + timedelta(weeks=8)

    total_services = 5
    licence_number = "PD5000229"
    all_service_codes = [f"{licence_number}:{n}" for n in range(total_services)]
    bods_licence = BODSLicenceFactory(organisation=org1, number=licence_number)
    dataset1 = DatasetFactory(organisation=org1)
    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[0],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
    )
    dataset2 = DraftDatasetFactory(organisation=org1)
    TXCFileAttributesFactory(
        revision=dataset2.revisions.last(),
        service_code=all_service_codes[1],
    )
    otc_lic1 = LicenceModelFactory(number=licence_number)
    for code in all_service_codes:
        ServiceModelFactory(
            licence=otc_lic1, registration_number=code.replace(":", "/")
        )

    # Create Seasonal Services - one in season, one out of season
    SeasonalServiceFactory(
        licence=bods_licence,
        start=today,
        end=month,
        registration_code=int(all_service_codes[2][-1:]),
    )
    SeasonalServiceFactory(
        licence=bods_licence,
        start=month,
        end=two_months,
        registration_code=int(all_service_codes[3][-1:]),
    )

    publish_client.force_login(user=user)
    url = reverse("requires-attention", host=host, kwargs={"pk1": org1.id})
    response = publish_client.get(url, data={"q": ""}, follow=True)

    assert response.status_code == 200
    assert len(response.context["view"].object_list) == 3
    # One out of season seasonal service reduces in scope services to 4
    assert response.context["services_require_attention_percentage"] == 75


def test_require_attention_stale_otc_effective_date(publish_client):
    # Setup
    host = PUBLISH_HOST
    org1 = OrganisationFactory(id=1)
    user = UserFactory(account_type=OrgStaffType, organisations=(org1,))

    total_services = 7
    licence_number = "PD5000229"
    all_service_codes = [f"{licence_number}:{n:03}" for n in range(total_services)]
    BODSLicenceFactory(organisation=org1, number=licence_number)
    dataset1 = DatasetFactory(organisation=org1)

    # Setup two TXCFileAttributes that will be 'Not Stale'
    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[0],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
    )

    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[1],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
    )

    dataset2 = DraftDatasetFactory(organisation=org1)
    TXCFileAttributesFactory(
        revision=dataset2.revisions.last(), service_code=all_service_codes[2]
    )
    live_revision = DatasetRevisionFactory(dataset=dataset2)

    # Setup a TXCFileAttributes that will be 'Stale - OTC Variation'
    TXCFileAttributesFactory(
        revision=live_revision,
        service_code=all_service_codes[3],
        operating_period_end_date=date.today() + timedelta(days=50),
    )

    otc_lic1 = LicenceModelFactory(number=licence_number)
    for code in all_service_codes:
        ServiceModelFactory(
            licence=otc_lic1, registration_number=code.replace(":", "/")
        )

    publish_client.force_login(user=user)
    url = reverse("requires-attention", host=host, kwargs={"pk1": org1.id})
    response = publish_client.get(url, data={"q": ""}, follow=True)

    assert response.status_code == 200
    assert len(response.context["view"].object_list) == 5
    assert response.context["services_require_attention_percentage"] == 72


def test_require_attention_stale_end_date(publish_client):
    # Setup
    host = PUBLISH_HOST
    org1 = OrganisationFactory(id=1)
    user = UserFactory(account_type=OrgStaffType, organisations=(org1,))

    total_services = 7
    licence_number = "PD5000229"
    all_service_codes = [f"{licence_number}:{n:03}" for n in range(total_services)]
    BODSLicenceFactory(organisation=org1, number=licence_number)
    dataset1 = DatasetFactory(organisation=org1)

    # Setup a TXCFileAttributes that will be 'Not Stale'
    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[0],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
    )

    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[1],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
    )

    dataset2 = DraftDatasetFactory(organisation=org1)
    TXCFileAttributesFactory(
        revision=dataset2.revisions.last(), service_code=all_service_codes[2]
    )
    live_revision = DatasetRevisionFactory(dataset=dataset2)

    # Setup a TXCFileAttributes that will be 'Stale - End Date Passed'
    TXCFileAttributesFactory(
        revision=live_revision,
        service_code=all_service_codes[3],
        operating_period_end_date=date.today() - timedelta(weeks=105),
        modification_datetime=now() - timedelta(weeks=100),
    )
    otc_lic1 = LicenceModelFactory(number=licence_number)
    for code in all_service_codes:
        ServiceModelFactory(
            licence=otc_lic1,
            registration_number=code.replace(":", "/"),
            effective_date=date(year=2020, month=1, day=1),
        )

    publish_client.force_login(user=user)
    url = reverse("requires-attention", host=host, kwargs={"pk1": org1.id})
    response = publish_client.get(url, data={"q": ""}, follow=True)

    assert response.status_code == 200
    assert len(response.context["view"].object_list) == 5
    assert response.context["services_require_attention_percentage"] == 72


def test_require_attention_stale_last_modified_date(publish_client):
    # Setup
    host = PUBLISH_HOST
    org1 = OrganisationFactory(id=1)
    user = UserFactory(account_type=OrgStaffType, organisations=(org1,))

    total_services = 7
    licence_number = "PD5000229"
    all_service_codes = [f"{licence_number}:{n:03}" for n in range(total_services)]
    BODSLicenceFactory(organisation=org1, number=licence_number)
    dataset1 = DatasetFactory(organisation=org1)

    # Setup two TXCFileAttributes that will be 'Not Stale'
    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[0],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
    )

    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[1],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
    )

    dataset2 = DraftDatasetFactory(organisation=org1)
    TXCFileAttributesFactory(
        revision=dataset2.revisions.last(), service_code=all_service_codes[2]
    )
    live_revision = DatasetRevisionFactory(dataset=dataset2)

    # Setup a TXCFileAttributes that will be 'Stale - 12 months old'
    TXCFileAttributesFactory(
        revision=live_revision,
        service_code=all_service_codes[3],
        operating_period_end_date=date.today() - timedelta(days=1),
        modification_datetime=now() - timedelta(weeks=100),
    )

    otc_lic1 = LicenceModelFactory(number=licence_number)
    for code in all_service_codes:
        ServiceModelFactory(
            licence=otc_lic1,
            registration_number=code.replace(":", "/"),
            effective_date=date(year=2020, month=1, day=1),
        )

    publish_client.force_login(user=user)
    url = reverse("requires-attention", host=host, kwargs={"pk1": org1.id})
    response = publish_client.get(url, data={"q": ""}, follow=True)

    assert response.status_code == 200
    assert len(response.context["view"].object_list) == 5
    assert response.context["services_require_attention_percentage"] == 72


def test_require_attention_all_variations(publish_client):
    # Setup
    host = PUBLISH_HOST
    org1 = OrganisationFactory(id=1)
    user = UserFactory(account_type=OrgStaffType, organisations=(org1,))
    today = now().date()
    month = now().date() + timedelta(weeks=4)
    two_months = now().date() + timedelta(weeks=8)

    total_services = 9
    licence_number = "PD5000229"
    all_service_codes = [f"{licence_number}:{n}" for n in range(total_services)]
    bods_licence = BODSLicenceFactory(organisation=org1, number=licence_number)
    dataset1 = DatasetFactory(organisation=org1)

    # Setup two TXCFileAttributes that will be 'Not Stale'
    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[0],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
    )

    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[1],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
    )

    dataset2 = DraftDatasetFactory(organisation=org1)
    TXCFileAttributesFactory(
        revision=dataset2.revisions.last(), service_code=all_service_codes[2]
    )
    live_revision = DatasetRevisionFactory(dataset=dataset2)

    # Setup a TXCFileAttributes that will be 'Stale - 12 months old'
    TXCFileAttributesFactory(
        revision=live_revision,
        service_code=all_service_codes[3],
        operating_period_end_date=None,
        modification_datetime=now() - timedelta(weeks=100),
    )

    # Setup a TXCFileAttributes that will be 'Stale - End Date Passed'
    TXCFileAttributesFactory(
        revision=live_revision,
        service_code=all_service_codes[4],
        operating_period_end_date=date.today() - timedelta(weeks=105),
        modification_datetime=now() - timedelta(weeks=100),
    )

    # Setup a TXCFileAttributes that will be 'Stale - OTC Variation'
    TXCFileAttributesFactory(
        revision=live_revision,
        service_code=all_service_codes[5],
        operating_period_end_date=date.today() + timedelta(days=50),
    )

    # Create Seasonal Services - one in season, one out of season
    SeasonalServiceFactory(
        licence=bods_licence,
        start=today,
        end=month,
        registration_code=int(all_service_codes[6][-1:]),
    )
    SeasonalServiceFactory(
        licence=bods_licence,
        start=month,
        end=two_months,
        registration_code=int(all_service_codes[7][-1:]),
    )

    otc_lic1 = LicenceModelFactory(number=licence_number)
    for code in all_service_codes:
        ServiceModelFactory(
            licence=otc_lic1,
            registration_number=code.replace(":", "/"),
            effective_date=date(year=2020, month=1, day=1),
        )

    publish_client.force_login(user=user)
    url = reverse("requires-attention", host=host, kwargs={"pk1": org1.id})
    response = publish_client.get(url, data={"q": ""}, follow=True)

    assert response.status_code == 200
    assert len(response.context["view"].object_list) == 6
    # One out of season seasonal service reduces in scope services to 8
    assert response.context["services_require_attention_percentage"] == 75


def test_require_attention_compliant(publish_client):
    # Setup
    host = PUBLISH_HOST
    org1 = OrganisationFactory(id=1)
    user = UserFactory(account_type=OrgStaffType, organisations=(org1,))
    month = now().date() + timedelta(weeks=4)
    two_months = now().date() + timedelta(weeks=8)

    total_services = 4
    licence_number = "PD5000229"
    all_service_codes = [f"{licence_number}:{n}" for n in range(total_services)]
    bods_licence = BODSLicenceFactory(organisation=org1, number=licence_number)
    dataset1 = DatasetFactory(organisation=org1)
    dataset2 = DatasetFactory(organisation=org1)

    # Setup three TXCFileAttributes that will be 'Not Stale'
    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[0],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
    )
    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        service_code=all_service_codes[1],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
    )
    TXCFileAttributesFactory(
        revision=dataset2.live_revision,
        service_code=all_service_codes[2],
        operating_period_end_date=date.today() + timedelta(days=50),
        modification_datetime=now(),
    )

    # Create Out of Season Seasonal Services
    SeasonalServiceFactory(
        licence=bods_licence,
        start=month,
        end=two_months,
        registration_code=int(all_service_codes[3][-1:]),
    )

    otc_lic1 = LicenceModelFactory(number=licence_number)
    for code in all_service_codes:
        ServiceModelFactory(
            licence=otc_lic1,
            registration_number=code.replace(":", "/"),
            effective_date=date(year=2020, month=1, day=1),
        )

    publish_client.force_login(user=user)
    url = reverse("requires-attention", host=host, kwargs={"pk1": org1.id})
    response = publish_client.get(url, data={"q": ""}, follow=True)

    assert response.status_code == 200
    assert response.context["total_in_scope_in_season_services"] == 3
    assert response.context["services_require_attention_percentage"] == 0
