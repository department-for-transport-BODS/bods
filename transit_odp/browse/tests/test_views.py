import csv
import datetime
import io
import zipfile
from logging import getLogger
from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.utils import timezone
from django_hosts import reverse
from freezegun import freeze_time
from waffle import flag_is_active
from waffle.testutils import override_flag

import transit_odp.publish.requires_attention as publish_attention
from config.hosts import DATA_HOST
from transit_odp.avl.factories import AVLValidationReportFactory
from transit_odp.avl.proxies import AVLDataset
from transit_odp.avl.tasks import cache_avl_compliance_status
from transit_odp.avl.tests.test_abods_registry import (
    REQUEST,
    mocked_requests_post_valid_response,
)
from transit_odp.browse.tasks import task_create_data_catalogue_archive
from transit_odp.browse.tests.comments_test import (
    DATA_LONG_MAXLENGTH_WITH_CARRIAGE_RETURN,
    DATA_LONGER_THAN_MAXLENGTH,
    DATA_LONGER_THAN_MAXLENGTH_WITH_CARRIAGE_RETURN,
    DATA_SHORTER_MAXLENGTH_WITH_CARRIAGE_RETURN,
)
from transit_odp.browse.views.local_authority import (
    LocalAuthorityDetailView,
    LocalAuthorityView,
)
from transit_odp.browse.views.operators import OperatorDetailView, OperatorsView
from transit_odp.browse.views.timetable_views import (
    DatasetChangeLogView,
    DatasetDetailView,
    LineMetadataDetailView,
)
from transit_odp.common.constants import FeatureFlags
from transit_odp.common.downloaders import GTFSFile
from transit_odp.common.forms import ConfirmationForm
from transit_odp.common.loggers import DatafeedPipelineLoggerContext, PipelineAdapter
from transit_odp.data_quality.factories import DataQualityReportFactory
from transit_odp.dqs.constants import Level, TaskResultsStatus
from transit_odp.dqs.factories import (
    ChecksFactory,
    ObservationResultsFactory,
    ReportFactory,
    TaskResultsFactory,
)
from transit_odp.fares.factories import (
    DataCatalogueMetaDataFactory,
    FaresMetadataFactory,
)
from transit_odp.fares_validator.factories import FaresValidationResultFactory
from transit_odp.feedback.models import Feedback
from transit_odp.naptan.factories import AdminAreaFactory
from transit_odp.organisation.constants import DatasetType, FeedStatus
from transit_odp.organisation.factories import (
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
from transit_odp.organisation.models import DatasetSubscription, Organisation
from transit_odp.otc.constants import API_TYPE_WECA
from transit_odp.otc.factories import (
    LicenceFactory,
    LicenceModelFactory,
    LocalAuthorityFactory,
    OperatorFactory,
    OperatorModelFactory,
    ServiceModelFactory,
    UILtaFactory,
)
from transit_odp.pipelines.factories import (
    BulkDataArchiveFactory,
    ChangeDataArchiveFactory,
    DatasetETLTaskResultFactory,
)
from transit_odp.site_admin.models import ResourceRequestCounter
from transit_odp.transmodel.factories import (
    ServiceFactory,
    ServicePatternFactory,
    ServicePatternStopFactory,
)
from transit_odp.users.factories import (
    AgentUserFactory,
    AgentUserInviteFactory,
    UserFactory,
)
from transit_odp.users.models import AgentUserInvite
from transit_odp.users.utils import create_verified_org_user

pytestmark = pytest.mark.django_db
AVL_LINE_LEVEL_REQUIRE_ATTENTION = (
    "transit_odp.browse.views.operators.get_avl_requires_attention_line_level_data"
)


def get_lta_complaint_data_queryset():
    org = OrganisationFactory()
    total_services = 9
    licence_number = "PD5000229"
    service = []
    all_service_codes = [f"{licence_number}:{n}" for n in range(total_services)]
    bods_licence = BODSLicenceFactory(organisation=org, number=licence_number)
    dataset1 = DatasetFactory(organisation=org)

    otc_lic = LicenceModelFactory(number=licence_number)
    for code in all_service_codes:
        service.append(
            ServiceModelFactory(
                licence=otc_lic,
                registration_number=code.replace(":", "/"),
                effective_date=datetime.date(year=2020, month=1, day=1),
                service_number="line1",
            )
        )

    ui_lta = UILtaFactory(name="Dorset County Council")

    local_authority = LocalAuthorityFactory(
        id="1",
        name="Dorset Council",
        ui_lta=ui_lta,
        registration_numbers=service,
    )

    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

    today = timezone.now().date()
    month = timezone.now().date() + datetime.timedelta(weeks=4)
    two_months = timezone.now().date() + datetime.timedelta(weeks=8)

    # Setup two TXCFileAttributes that will be 'Not Stale'
    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        licence_number=otc_lic.number,
        service_code=all_service_codes[0],
        operating_period_end_date=datetime.date.today() + datetime.timedelta(days=50),
        modification_datetime=timezone.now(),
    )

    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        licence_number=otc_lic.number,
        service_code=all_service_codes[1],
        operating_period_end_date=datetime.date.today() + datetime.timedelta(days=75),
        modification_datetime=timezone.now() - datetime.timedelta(days=50),
    )

    # Setup a draft TXCFileAttributes
    dataset2 = DraftDatasetFactory(organisation=org)
    TXCFileAttributesFactory(
        revision=dataset2.revisions.last(),
        licence_number=otc_lic.number,
        service_code=all_service_codes[2],
    )

    live_revision = DatasetRevisionFactory(dataset=dataset2)
    # Setup a TXCFileAttributes that will be 'Stale - 12 months old'
    TXCFileAttributesFactory(
        revision=live_revision,
        licence_number=otc_lic.number,
        service_code=all_service_codes[3],
        operating_period_end_date=None,
        modification_datetime=timezone.now() - datetime.timedelta(weeks=100),
    )

    # Setup a TXCFileAttributes that will be 'Stale - 42 day look ahead'
    TXCFileAttributesFactory(
        revision=live_revision,
        licence_number=otc_lic.number,
        service_code=all_service_codes[4],
        operating_period_end_date=datetime.date.today() - datetime.timedelta(weeks=105),
        modification_datetime=timezone.now() - datetime.timedelta(weeks=100),
    )

    # Setup a TXCFileAttributes that will be 'Stale - OTC Variation'
    TXCFileAttributesFactory(
        revision=live_revision,
        licence_number=otc_lic.number,
        service_code=all_service_codes[5],
        operating_period_end_date=datetime.date.today() + datetime.timedelta(days=50),
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

    return local_authority


def get_lta_complaint_weca_data_queryset():
    org = OrganisationFactory()
    total_services = 9
    licence_number = "PD5000229"
    service = []
    service_code_prefix = "1101000"
    atco_code = "110"
    registration_code_index = -len(service_code_prefix) - 1
    all_service_codes = [
        f"{licence_number}:{service_code_prefix}{n}" for n in range(total_services)
    ]
    bods_licence = BODSLicenceFactory(organisation=org, number=licence_number)
    dataset1 = DatasetFactory(organisation=org)

    otc_lic = LicenceModelFactory(number=licence_number)
    for code in all_service_codes:
        service.append(
            ServiceModelFactory(
                licence=otc_lic,
                registration_number=code.replace(":", "/"),
                effective_date=datetime.date(year=2020, month=1, day=1),
                api_type=API_TYPE_WECA,
                atco_code=atco_code,
                service_number="line1",
            )
        )

    ui_lta = UILtaFactory(name="Dorset County Council")

    local_authority = LocalAuthorityFactory(
        id="1",
        name="Dorset Council",
        ui_lta=ui_lta,
        registration_numbers=service,
    )

    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta, atco_code=atco_code)

    today = timezone.now().date()
    month = timezone.now().date() + datetime.timedelta(weeks=4)
    two_months = timezone.now().date() + datetime.timedelta(weeks=8)

    # Setup two TXCFileAttributes that will be 'Not Stale'
    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        licence_number=otc_lic.number,
        service_code=all_service_codes[0],
        operating_period_end_date=datetime.date.today() + datetime.timedelta(days=50),
        modification_datetime=timezone.now(),
    )

    TXCFileAttributesFactory(
        revision=dataset1.live_revision,
        licence_number=otc_lic.number,
        service_code=all_service_codes[1],
        operating_period_end_date=datetime.date.today() + datetime.timedelta(days=75),
        modification_datetime=timezone.now() - datetime.timedelta(days=50),
    )

    # Setup a draft TXCFileAttributes
    dataset2 = DraftDatasetFactory(organisation=org)
    TXCFileAttributesFactory(
        revision=dataset2.revisions.last(),
        licence_number=otc_lic.number,
        service_code=all_service_codes[2],
    )

    live_revision = DatasetRevisionFactory(dataset=dataset2)
    # Setup a TXCFileAttributes that will be 'Stale - 12 months old'
    TXCFileAttributesFactory(
        revision=live_revision,
        licence_number=otc_lic.number,
        service_code=all_service_codes[3],
        operating_period_end_date=None,
        modification_datetime=timezone.now() - datetime.timedelta(weeks=100),
    )

    # Setup a TXCFileAttributes that will be 'Stale - 42 day look ahead'
    TXCFileAttributesFactory(
        revision=live_revision,
        licence_number=otc_lic.number,
        service_code=all_service_codes[4],
        operating_period_end_date=datetime.date.today() - datetime.timedelta(weeks=105),
        modification_datetime=timezone.now() - datetime.timedelta(weeks=100),
    )

    # Setup a TXCFileAttributes that will be 'Stale - OTC Variation'
    TXCFileAttributesFactory(
        revision=live_revision,
        licence_number=otc_lic.number,
        service_code=all_service_codes[5],
        operating_period_end_date=datetime.date.today() + datetime.timedelta(days=50),
    )

    # Create Seasonal Services - one in season, one out of season
    SeasonalServiceFactory(
        licence=bods_licence,
        start=today,
        end=month,
        registration_code=int(all_service_codes[6][registration_code_index:]),
    )
    SeasonalServiceFactory(
        licence=bods_licence,
        start=month,
        end=two_months,
        registration_code=int(all_service_codes[7][registration_code_index:]),
    )

    return local_authority


def get_lta_list_data():
    test_ltas = [
        {"name": "Derby Council", "ui_lta_name": "Derby City Council"},
        {"name": "Cheshire Council", "ui_lta_name": "Cheshire East Council"},
        {"name": "Aberdeen Council", "ui_lta_name": "Aberdeen City Council"},
        {"name": "Bedford Council", "ui_lta_name": "Bedford Borough Council"},
        {"name": "Blackpool Council", "ui_lta_name": "Blackpool Council"},
        {
            "name": "Bournemouth Council",
            "ui_lta_name": "Bournemouth, Christchurch and Poole Council",
        },
        {
            "name": "Brighton Council",
            "ui_lta_name": "Brighton and Hove City Council",
        },
        {
            "name": "Hove City Council",
            "ui_lta_name": "Brighton and Hove City Council",
        },
        {
            "name": "Central Bedfordshire Council",
            "ui_lta_name": "Central Bedfordshire Council",
        },
        {"name": "Cheshire East Council", "ui_lta_name": "Cheshire East Council"},
        {"name": "Dorset Council", "ui_lta_name": "Dorset Council"},
        {"name": "Cumbria County Council", "ui_lta_name": "Cumbria County Council"},
        {"name": "Bournem Council", "ui_lta_name": "Bournemouth Council"},
        {
            "name": "Poole Council",
            "ui_lta_name": "Bournemouth, Christchurch and Poole Council",
        },
    ]

    ui_ltas = {}
    for id, lta in enumerate(test_ltas, start=1):
        lta_name = lta["ui_lta_name"]
        if lta_name not in ui_ltas:
            ui_ltas[lta_name] = UILtaFactory(name=lta_name)
        LocalAuthorityFactory(id=id, name=lta["name"], ui_lta=ui_ltas[lta_name]),


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

    def test_dq_report_without_summary(
        self, user: settings.AUTH_USER_MODEL, request_factory: RequestFactory
    ):
        org_user = create_verified_org_user()
        dataset = DatasetFactory.create(organisation=org_user.organisation)
        revision = DatasetRevisionFactory.create(
            dataset=dataset, status=FeedStatus.live.value
        )
        DatasetETLTaskResultFactory(revision=revision)
        DatasetSubscriptionFactory(dataset=dataset, user=org_user)
        DataQualityReportFactory(revision=revision, summary=None, score=0)

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
            reverse("users:feeds-manage", host=host) + "?page=1&",
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
        is_direct_s3_url_active = flag_is_active("", "is_direct_s3_url_active")
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
        if is_direct_s3_url_active:
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
        # create an organisation
        org = OrganisationFactory.create()
        DatasetFactory.create(organisation=org)

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
            "disruptions_data_catalogue.csv",
        ]

        with zipfile.ZipFile(io.BytesIO(b"".join(response.streaming_content))) as zf:
            for zf in zf.infolist():
                assert zf.filename in expected_files

    def test_operator_noc_download(self, client_factory):
        org = OrganisationFactory.create()
        OrganisationFactory.create(nocs=4)
        DatasetFactory.create(organisation=org)

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
        org = OrganisationFactory.create()
        OrganisationFactory.create(is_active=False)
        OrganisationFactory.create(nocs=4)
        DatasetFactory.create(organisation=org)

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


@override_flag("is_new_gtfs_api_active", active=True)
class TestGTFSStaticDownloads(TestCase):
    host = DATA_HOST

    @patch("transit_odp.browse.views.timetable_views.GTFSFileDownloader")
    @pytest.mark.skip(reason="to be removed when GTFS feature goes live")
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

    @patch("transit_odp.browse.views.timetable_views.GTFSFileDownloader")
    @pytest.mark.skip(reason="to be removed when GTFS feature goes live")
    def test_download_gtfs_increments_resource_counter(
        self, downloader_cls, client_factory
    ):
        url = reverse("gtfs-file-download", args=["all"], host=self.host)

        downloader_obj = Mock()
        downloader_cls.return_value = downloader_obj
        gtfs_file = GTFSFile.from_id("all")
        gtfs_file.file = io.StringIO("blahblah")
        downloader_obj.download_file_by_id.return_value = gtfs_file

        client = client_factory(host=self.host)
        assert ResourceRequestCounter.objects.count() == 0
        response = client.get(url)
        assert response.status_code == 200
        assert ResourceRequestCounter.objects.count() == 1


@override_flag("is_new_gtfs_api_active", active=True)
class TestNewGTFSStaticDownloads(TestCase):
    host = DATA_HOST

    @patch("transit_odp.browse.views.timetable_views._get_gtfs_file")
    @pytest.mark.skip(reason="to be removed when GTFS feature goes live")
    def test_download_gtfs_file_404(self, mrequests, client_factory):
        url = reverse("gtfs-file-download", host=self.host, args=["all"])
        client = client_factory(host=self.host)

        mrequests.return_value = None
        response = client.get(url)
        assert response.status_code == 404

    @patch("transit_odp.browse.views.timetable_views._get_gtfs_file")
    @pytest.mark.skip(reason="to be removed when GTFS feature goes live")
    def test_download_gtfs_increments_resource_counter(self, mrequests, client_factory):
        url = reverse("gtfs-file-download", host=self.host, args=["all"])
        client = client_factory(host=self.host)

        gtfs_content = "test"
        mrequests.return_value = gtfs_content

        assert ResourceRequestCounter.objects.count() == 0
        response = client.get(url)
        assert response.status_code == 200
        assert ResourceRequestCounter.objects.count() == 1
        assert response.getvalue() == bytes(gtfs_content, encoding="utf-8")


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
    """
    Tests for OperatorDetailView.
    """

    @override_flag(FeatureFlags.AVL_REQUIRES_ATTENTION.value, active=True)
    @override_flag(FeatureFlags.FARES_REQUIRE_ATTENTION.value, active=True)
    @override_flag(FeatureFlags.COMPLETE_SERVICE_PAGES.value, active=True)
    @override_flag(FeatureFlags.OPERATOR_PREFETCH_SRA.value, active=False)
    @patch.object(publish_attention, "AbodsRegistery")
    @patch.object(publish_attention, "get_vehicle_activity_operatorref_linename")
    def test_operator_detail_view_stats_not_compliant(
        self, mock_vehivle_activity, mock_abodsregistry, request_factory: RequestFactory
    ):
        """
        Test for operator profile non compliant stats relating to:
            - Total in scope/in season registered services
            - Overall services requiring attention
            - Timetables data requiring attention
            - Location data requiring attention
            - Fares data requiring attention

        Args:
            request_factory (RequestFactory): Request Factory
        """
        national_operator_code = "BLAC"
        org = OrganisationFactory(nocs=national_operator_code)
        today = timezone.now().date()
        month = timezone.now().date() + datetime.timedelta(weeks=4)
        two_months = timezone.now().date() + datetime.timedelta(weeks=8)
        mock_registry_instance = MagicMock()
        mock_abodsregistry.return_value = mock_registry_instance
        mock_registry_instance.records.return_value = ["line1__SDCU", "line2__SDCU"]
        mock_vehivle_activity.return_value = pd.DataFrame(
            {"OperatorRef": ["SDCU"], "LineRef": ["line2"]}
        )

        total_services = 9
        licence_number = "PD5000229"
        all_service_codes = [f"{licence_number}:{n}" for n in range(total_services)]
        all_line_names = [f"Line:{n}" for n in range(total_services)]
        bods_licence = BODSLicenceFactory(organisation=org, number=licence_number)
        dataset1 = DatasetFactory(organisation=org)
        fares_dataset = DatasetFactory(
            organisation=org, dataset_type=DatasetType.FARES.value
        )
        fares_revision = FaresDatasetRevisionFactory(
            dataset__organisation=org,
            dataset__live_revision=fares_dataset.id,
        )
        fares_dataset_2 = DatasetFactory(
            organisation=org, dataset_type=DatasetType.FARES.value
        )
        fares_revision_2 = FaresDatasetRevisionFactory(
            dataset__organisation=org,
            dataset__live_revision=fares_dataset_2.id,
        )
        fares_dataset_3 = DatasetFactory(
            organisation=org, dataset_type=DatasetType.FARES.value
        )
        fares_revision_3 = FaresDatasetRevisionFactory(
            dataset__organisation=org,
            dataset__live_revision=fares_dataset_3.id,
        )
        fares_dataset_4 = DatasetFactory(
            organisation=org, dataset_type=DatasetType.FARES.value
        )
        fares_revision_4 = FaresDatasetRevisionFactory(
            dataset__organisation=org,
            dataset__live_revision=fares_dataset_4.id,
        )
        fares_dataset_5 = DatasetFactory(
            organisation=org, dataset_type=DatasetType.FARES.value
        )
        fares_revision_5 = FaresDatasetRevisionFactory(
            dataset__organisation=org,
            dataset__live_revision=fares_dataset_5.id,
        )
        fares_dataset_6 = DatasetFactory(
            organisation=org, dataset_type=DatasetType.FARES.value
        )
        fares_revision_6 = FaresDatasetRevisionFactory(
            dataset__organisation=org,
            dataset__live_revision=fares_dataset_6.id,
        )

        # Setup two TXCFileAttributes that will be 'Up to Date'
        TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[0],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[0]],
            national_operator_code=[national_operator_code],
        )
        faresmetadata = FaresMetadataFactory(
            revision=fares_revision,
            valid_from=datetime.datetime(2024, 12, 12),
            valid_to=datetime.datetime(2025, 1, 12),
        )
        DataCatalogueMetaDataFactory(
            fares_metadata=faresmetadata,
            fares_metadata__revision__is_published=True,
            line_name=[f"{all_line_names[0]}"],
            line_id=[f"::{all_line_names[0]}"],
            valid_from=datetime.datetime(2024, 12, 12),
            valid_to=datetime.datetime(2025, 1, 12),
            national_operator_code=[national_operator_code],
        )
        FaresValidationResultFactory(
            revision=fares_revision,
            organisation=org,
            count=5,
        )

        TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[1],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=75),
            modification_datetime=timezone.now() - datetime.timedelta(days=50),
            line_names=[all_line_names[1]],
            national_operator_code=[national_operator_code],
        )
        faresmetadata_1 = FaresMetadataFactory(
            revision=fares_revision_2,
            valid_from=datetime.datetime(2024, 12, 12),
            valid_to=datetime.datetime(2025, 1, 12),
        )
        DataCatalogueMetaDataFactory(
            fares_metadata=faresmetadata_1,
            fares_metadata__revision__is_published=True,
            line_name=[f"{all_line_names[1]}"],
            line_id=[f"::{all_line_names[1]}"],
            valid_from=datetime.datetime(2024, 12, 12),
            valid_to=datetime.datetime(2025, 1, 12),
            national_operator_code=[national_operator_code],
        )
        FaresValidationResultFactory(
            revision=fares_revision_2,
            organisation=org,
            count=0,
        )

        # Setup a draft TXCFileAttributes
        dataset2 = DraftDatasetFactory(organisation=org)
        TXCFileAttributesFactory(
            revision=dataset2.revisions.last(),
            service_code=all_service_codes[2],
            line_names=[all_line_names[2]],
            national_operator_code=[national_operator_code],
        )
        faresmetadata_2 = FaresMetadataFactory(
            revision=fares_revision_3,
            valid_from=datetime.datetime(2024, 12, 12),
            valid_to=datetime.datetime(2025, 1, 12),
        )
        DataCatalogueMetaDataFactory(
            fares_metadata=faresmetadata_2,
            fares_metadata__revision__is_published=True,
            line_name=[f"{all_line_names[2]}"],
            line_id=[f"::{all_line_names[2]}"],
            valid_from=datetime.datetime(2024, 12, 12),
            valid_to=datetime.datetime(2025, 1, 12),
            national_operator_code=[national_operator_code],
        )
        FaresValidationResultFactory(
            revision=fares_revision_3,
            organisation=org,
            count=2,
        )

        live_revision = DatasetRevisionFactory(dataset=dataset2)

        # Setup a TXCFileAttributes that will be 'Stale - 12 months old'
        TXCFileAttributesFactory(
            revision=live_revision,
            service_code=all_service_codes[3],
            operating_period_end_date=None,
            modification_datetime=timezone.now() - datetime.timedelta(weeks=100),
            line_names=[all_line_names[3]],
            national_operator_code=[national_operator_code],
        )
        faresmetadata_3 = FaresMetadataFactory(
            revision=fares_revision_4,
            valid_from=datetime.datetime(2024, 12, 12),
            valid_to=datetime.datetime(2025, 1, 12),
        )
        DataCatalogueMetaDataFactory(
            fares_metadata=faresmetadata_3,
            fares_metadata__revision__is_published=True,
            line_name=[f"{all_line_names[3]}"],
            line_id=[f"::{all_line_names[3]}"],
            valid_from=datetime.datetime(2024, 12, 12),
            valid_to=datetime.datetime(2025, 1, 12),
            national_operator_code=[national_operator_code],
        )
        FaresValidationResultFactory(
            revision=fares_revision_4,
            organisation=org,
            count=1,
        )

        # Setup a TXCFileAttributes that will be 'Stale - 42 day look ahead'
        TXCFileAttributesFactory(
            revision=live_revision,
            service_code=all_service_codes[4],
            operating_period_end_date=datetime.date.today()
            - datetime.timedelta(weeks=105),
            modification_datetime=timezone.now() - datetime.timedelta(weeks=100),
            line_names=[all_line_names[4]],
            national_operator_code=[national_operator_code],
        )
        faresmetadata_4 = FaresMetadataFactory(
            revision=fares_revision_5,
            valid_from=datetime.datetime(2024, 12, 12),
            valid_to=datetime.datetime(2025, 1, 12),
        )
        DataCatalogueMetaDataFactory(
            fares_metadata=faresmetadata_4,
            fares_metadata__revision__is_published=True,
            line_name=[f"{all_line_names[4]}"],
            line_id=[f"::{all_line_names[4]}"],
            valid_from=datetime.datetime(2024, 12, 12),
            valid_to=datetime.datetime(2025, 1, 12),
            national_operator_code=[national_operator_code],
        )
        FaresValidationResultFactory(
            revision=fares_revision_5,
            organisation=org,
            count=0,
        )

        # Setup a TXCFileAttributes that will be 'Stale - OTC Variation'
        TXCFileAttributesFactory(
            revision=live_revision,
            service_code=all_service_codes[5],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            line_names=[all_line_names[5]],
            national_operator_code=[national_operator_code],
        )
        faresmetadata_5 = FaresMetadataFactory(
            revision=fares_revision_6,
            valid_from=datetime.datetime(2024, 12, 12),
            valid_to=datetime.datetime(2025, 1, 12),
        )
        DataCatalogueMetaDataFactory(
            fares_metadata=faresmetadata_5,
            fares_metadata__revision__is_published=True,
            line_name=[f"{all_line_names[5]}"],
            line_id=[f"::{all_line_names[5]}"],
            valid_from=datetime.datetime(2024, 12, 12),
            valid_to=datetime.datetime(2025, 1, 12),
            national_operator_code=[national_operator_code],
        )
        FaresValidationResultFactory(
            revision=fares_revision_6,
            organisation=org,
            count=9,
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
        services = []
        for index, code in enumerate(all_service_codes, start=0):
            services.append(
                ServiceModelFactory(
                    licence=otc_lic1,
                    registration_number=code.replace(":", "/"),
                    effective_date=datetime.date(year=2020, month=1, day=1),
                    service_number=all_line_names[index],
                )
            )

        ui_lta = UILtaFactory(name="UI_LTA")
        LocalAuthorityFactory(
            id="1", name="first_LTA", registration_numbers=services, ui_lta=ui_lta
        )
        AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

        request = request_factory.get("/operators/")
        request.user = UserFactory()

        response = OperatorDetailView.as_view()(request, pk=org.id)
        assert response.status_code == 200
        context = response.context_data

        assert context["view"].template_name == "browse/operators/operator_detail.html"
        assert context["total_in_scope_in_season_services"] == 8
        assert context["timetable_services_requiring_attention_count"] == 6
        assert context["avl_services_requiring_attention_count"] == 8
        assert context["fares_services_requiring_attention_count"] == 8
        assert context["total_services_requiring_attention"] == 8

    @override_flag(FeatureFlags.AVL_REQUIRES_ATTENTION.value, active=True)
    @override_flag(FeatureFlags.FARES_REQUIRE_ATTENTION.value, active=True)
    @override_flag(FeatureFlags.COMPLETE_SERVICE_PAGES.value, active=True)
    @patch.object(publish_attention, "AbodsRegistery")
    @patch.object(publish_attention, "get_vehicle_activity_operatorref_linename")
    @freeze_time("2023-02-24")
    def test_operator_detail_view_stats_compliant(
        self, mock_vehivle_activity, mock_abodsregistry, request_factory: RequestFactory
    ):
        """
        Test for operator profile compliant stats relating to:
            - Total in scope/in season registered services
            - Overall services requiring attention
            - Timetables data requiring attention
            - Location data requiring attention
            - Fares data requiring attention

        Args:
            request_factory (RequestFactory): Request Factory
        """
        national_operator_code = "BLAC"
        org = OrganisationFactory(nocs=national_operator_code)
        month = timezone.now().date() + datetime.timedelta(weeks=4)
        two_months = timezone.now().date() + datetime.timedelta(weeks=8)
        mock_registry_instance = MagicMock()
        mock_abodsregistry.return_value = mock_registry_instance
        mock_registry_instance.records.return_value = [
            "line0__BLAC",
            "line1__BLAC",
            "line2__BLAC",
        ]
        mock_vehivle_activity.return_value = pd.DataFrame(
            {"OperatorRef": ["SDCU"], "LineRef": ["line0"]}
        )

        total_services = 4
        licence_number = "PD5000123"
        all_service_codes = [f"{licence_number}:{n}" for n in range(total_services)]
        all_line_names = [f"line{n}" for n in range(total_services)]
        bods_licence = BODSLicenceFactory(organisation=org, number=licence_number)
        dataset1 = DatasetFactory(organisation=org)
        dataset2 = DatasetFactory(organisation=org)
        fares_dataset = DatasetFactory(
            organisation=org, dataset_type=DatasetType.FARES.value
        )
        fares_revision = FaresDatasetRevisionFactory(
            dataset__organisation=org,
            dataset__live_revision=fares_dataset.id,
        )
        fares_dataset_2 = DatasetFactory(
            organisation=org, dataset_type=DatasetType.FARES.value
        )
        fares_revision_2 = FaresDatasetRevisionFactory(
            dataset__organisation=org,
            dataset__live_revision=fares_dataset_2.id,
        )
        fares_dataset_3 = DatasetFactory(
            organisation=org, dataset_type=DatasetType.FARES.value
        )
        fares_revision_3 = FaresDatasetRevisionFactory(
            dataset__organisation=org,
            dataset__live_revision=fares_dataset_3.id,
        )

        request = request_factory.get("/operators/")
        request.user = UserFactory()

        # Setup three TXCFileAttributes that will be 'Up to Date'
        TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[0],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[0]],
            national_operator_code=national_operator_code,
        )
        faresmetadata = FaresMetadataFactory(
            revision=fares_revision,
            valid_from=datetime.datetime(2024, 12, 12),
            valid_to=datetime.datetime(2025, 1, 12),
        )
        DataCatalogueMetaDataFactory(
            fares_metadata=faresmetadata,
            fares_metadata__revision__is_published=True,
            line_name=[f"{all_line_names[0]}"],
            line_id=[f":::{all_line_names[0]}"],
            valid_from=datetime.datetime(2024, 12, 12),
            valid_to=datetime.datetime(2025, 1, 12),
            national_operator_code=[national_operator_code],
        )
        FaresValidationResultFactory(
            revision=fares_revision,
            organisation=org,
            count=0,
        )

        TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[1],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[1]],
            national_operator_code=national_operator_code,
        )
        faresmetadata_2 = FaresMetadataFactory(
            revision=fares_revision_2,
            valid_from=datetime.datetime(2024, 12, 12),
            valid_to=datetime.datetime(2025, 1, 12),
        )
        DataCatalogueMetaDataFactory(
            fares_metadata=faresmetadata_2,
            fares_metadata__revision__is_published=True,
            line_name=[f"{all_line_names[1]}"],
            line_id=[f":::{all_line_names[1]}"],
            valid_from=datetime.datetime(2024, 12, 12),
            valid_to=datetime.datetime(2025, 1, 12),
            national_operator_code=[national_operator_code],
        )
        FaresValidationResultFactory(
            revision=fares_revision_2,
            organisation=org,
            count=0,
        )

        TXCFileAttributesFactory(
            revision=dataset2.live_revision,
            service_code=all_service_codes[2],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[2]],
            national_operator_code=national_operator_code,
        )
        faresmetadata_3 = FaresMetadataFactory(
            revision=fares_revision_3,
            valid_from=datetime.datetime(2024, 12, 12),
            valid_to=datetime.datetime(2025, 1, 12),
        )
        DataCatalogueMetaDataFactory(
            fares_metadata=faresmetadata_3,
            fares_metadata__revision__is_published=True,
            line_name=[f"{all_line_names[2]}"],
            line_id=[f":::{all_line_names[2]}"],
            valid_from=datetime.datetime(2024, 12, 12),
            valid_to=datetime.datetime(2025, 1, 12),
            national_operator_code=[national_operator_code],
        )
        FaresValidationResultFactory(
            revision=fares_revision_3,
            organisation=org,
            count=0,
        )

        # Create Out of Season Seasonal Service
        SeasonalServiceFactory(
            licence=bods_licence,
            start=month,
            end=two_months,
            registration_code=int(all_service_codes[3][-1:]),
        )
        # Create In Season Seasonal Service for live, up to date service
        SeasonalServiceFactory(
            licence=bods_licence,
            start=timezone.now().date(),
            end=month,
            registration_code=int(all_service_codes[2][-1:]),
        )

        otc_lic1 = LicenceModelFactory(number=licence_number)
        services = []
        for index, code in enumerate(all_service_codes):
            services.append(
                ServiceModelFactory(
                    licence=otc_lic1,
                    registration_number=code.replace(":", "/"),
                    effective_date=datetime.date(year=2020, month=1, day=1),
                    service_number=all_line_names[index],
                )
            )

        ui_lta = UILtaFactory(name="UI_LTA")
        LocalAuthorityFactory(
            id="1", name="first_LTA", registration_numbers=services, ui_lta=ui_lta
        )
        AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

        response = OperatorDetailView.as_view()(request, pk=org.id)
        assert response.status_code == 200
        context = response.context_data
        assert context["view"].template_name == "browse/operators/operator_detail.html"
        assert context["total_in_scope_in_season_services"] == 3
        assert context["timetable_services_requiring_attention_count"] == 0
        assert context["avl_services_requiring_attention_count"] == 0
        assert context["fares_services_requiring_attention_count"] == 0
        assert context["total_services_requiring_attention"] == 0

    @override_flag(FeatureFlags.DQS_REQUIRE_ATTENTION.value, active=True)
    @override_flag(FeatureFlags.AVL_REQUIRES_ATTENTION.value, active=True)
    @override_flag(FeatureFlags.FARES_REQUIRE_ATTENTION.value, active=True)
    @override_flag(FeatureFlags.COMPLETE_SERVICE_PAGES.value, active=True)
    def test_operator_detail_view_dqs_stats_compliant(
        self, request_factory: RequestFactory
    ):
        """
        Test for Operator SRA timetable stat - DQS critical issues.

        Args:
            request_factory (RequestFactory): Request Factory
        """
        org = OrganisationFactory()
        month = timezone.now().date() + datetime.timedelta(weeks=4)
        two_months = timezone.now().date() + datetime.timedelta(weeks=8)

        total_services = 4
        licence_number = "PD5000123"
        all_service_codes = [f"{licence_number}:{n}" for n in range(total_services)]
        all_line_names = [f"line:{n}" for n in range(total_services)]
        bods_licence = BODSLicenceFactory(organisation=org, number=licence_number)
        dataset1 = DatasetFactory(organisation=org)
        dataset2 = DatasetFactory(organisation=org)

        request = request_factory.get("/operators/")
        request.user = UserFactory()

        # Setup three TXCFileAttributes that will be 'Up to Date'
        txcfileattribute1 = TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[0],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[0]],
        )
        TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[1],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[1]],
        )
        TXCFileAttributesFactory(
            revision=dataset2.live_revision,
            service_code=all_service_codes[2],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[2]],
        )

        # Create Out of Season Seasonal Service
        SeasonalServiceFactory(
            licence=bods_licence,
            start=month,
            end=two_months,
            registration_code=int(all_service_codes[3][-1:]),
        )
        # Create In Season Seasonal Service for live, up to date service
        SeasonalServiceFactory(
            licence=bods_licence,
            start=timezone.now().date(),
            end=month,
            registration_code=int(all_service_codes[2][-1:]),
        )

        # create transmodel servicepattern
        service_pattern = ServicePatternFactory(
            revision=dataset1.live_revision, line_name=txcfileattribute1.line_names[0]
        )

        # create transmodel service
        service = ServiceFactory(
            revision=dataset1.live_revision,
            name=all_line_names[0],
            service_code=all_service_codes[0],
            service_patterns=[service_pattern],
            txcfileattributes=txcfileattribute1,
        )

        # create transmodel servicepatternstop
        service_pattern_stop = ServicePatternStopFactory(
            service_pattern=service_pattern
        )

        # create DQS observation result
        check1 = ChecksFactory(queue_name="Queue1", importance="Critical")
        check2 = ChecksFactory(queue_name="Queue1")
        check1.importance = "Critical"

        dataquality_report = ReportFactory(revision=dataset1.live_revision)

        taskresult = TaskResultsFactory(
            transmodel_txcfileattributes=txcfileattribute1,
            dataquality_report=dataquality_report,
            checks=check1,
        )
        observation_result = ObservationResultsFactory(
            service_pattern_stop=service_pattern_stop, taskresults=taskresult
        )

        otc_lic1 = LicenceModelFactory(number=licence_number)
        services = []
        for index, code in enumerate(all_service_codes):
            services.append(
                ServiceModelFactory(
                    licence=otc_lic1,
                    registration_number=code.replace(":", "/"),
                    effective_date=datetime.date(year=2020, month=1, day=1),
                    service_number=all_line_names[index],
                )
            )

        ui_lta = UILtaFactory(name="UI_LTA")
        LocalAuthorityFactory(
            id="1", name="first_LTA", registration_numbers=services, ui_lta=ui_lta
        )
        AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

        response = OperatorDetailView.as_view()(request, pk=org.id)
        assert response.status_code == 200
        context = response.context_data
        assert context["view"].template_name == "browse/operators/operator_detail.html"
        # One out of season seasonal service reduces in scope services to 3
        assert context["total_in_scope_in_season_services"] == 3
        assert (
            context["timetable_services_requiring_attention_count"] == 1
        )  # DQS critical issues

    @patch(AVL_LINE_LEVEL_REQUIRE_ATTENTION)
    @override_flag(FeatureFlags.AVL_REQUIRES_ATTENTION.value, active=True)
    @override_flag(FeatureFlags.FARES_REQUIRE_ATTENTION.value, active=True)
    @override_flag(FeatureFlags.COMPLETE_SERVICE_PAGES.value, active=True)
    def test_operator_detail_weca_view_timetable_stats_compliant(
        self, avl_line_level_require_attention, request_factory: RequestFactory
    ):
        """Test Operator WECA details view stat with complaint data in_scope_in_season
        Count there are zero which required attention

        Args:
            request_factory (RequestFactory): Request Factory
        """
        org = OrganisationFactory()
        month = timezone.now().date() + datetime.timedelta(weeks=4)
        two_months = timezone.now().date() + datetime.timedelta(weeks=8)
        avl_line_level_require_attention.return_value = []

        total_services = 4
        licence_number = "PD5000123"
        service_code_prefix = "1101000"
        atco_code = "110"
        registration_code_index = -len(service_code_prefix) - 1
        all_service_codes = [
            f"{licence_number}:{service_code_prefix}{n}" for n in range(total_services)
        ]
        all_line_names = [f"line{n}" for n in range(total_services)]
        bods_licence = BODSLicenceFactory(organisation=org, number=licence_number)
        dataset1 = DatasetFactory(organisation=org)
        dataset2 = DatasetFactory(organisation=org)

        request = request_factory.get("/operators/")
        request.user = UserFactory()

        # Setup three TXCFileAttributes that will be 'Up to Date'
        TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[0],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[0]],
        )
        TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[1],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[1]],
        )
        TXCFileAttributesFactory(
            revision=dataset2.live_revision,
            service_code=all_service_codes[2],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[2]],
        )

        # Create Out of Season Seasonal Service
        SeasonalServiceFactory(
            licence=bods_licence,
            start=month,
            end=two_months,
            registration_code=int(all_service_codes[3][registration_code_index:]),
        )
        # Create In Season Seasonal Service for live, up to date service
        SeasonalServiceFactory(
            licence=bods_licence,
            start=timezone.now().date(),
            end=month,
            registration_code=int(all_service_codes[2][registration_code_index:]),
        )

        otc_lic1 = LicenceModelFactory(number=licence_number)
        services = []
        for index, code in enumerate(all_service_codes):
            services.append(
                ServiceModelFactory(
                    licence=otc_lic1,
                    registration_number=code.replace(":", "/"),
                    effective_date=datetime.date(year=2020, month=1, day=1),
                    api_type=API_TYPE_WECA,
                    atco_code=atco_code,
                    service_number=all_line_names[index],
                )
            )

        ui_lta = UILtaFactory(name="UI_LTA")
        LocalAuthorityFactory(
            id="1", name="first_LTA", registration_numbers=services, ui_lta=ui_lta
        )
        AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta, atco_code=atco_code)

        response = OperatorDetailView.as_view()(request, pk=org.id)
        assert response.status_code == 200
        context = response.context_data
        assert context["view"].template_name == "browse/operators/operator_detail.html"
        # One out of season seasonal service reduces in scope services to 3
        assert context["total_in_scope_in_season_services"] == 3
        # 3 services up to date, including one in season. 0/3 requiring attention = 0%
        assert context["timetable_services_requiring_attention_count"] == 0

    @patch(AVL_LINE_LEVEL_REQUIRE_ATTENTION)
    @override_flag(FeatureFlags.AVL_REQUIRES_ATTENTION.value, active=True)
    @override_flag(FeatureFlags.FARES_REQUIRE_ATTENTION.value, active=True)
    @override_flag(FeatureFlags.COMPLETE_SERVICE_PAGES.value, active=True)
    def test_operator_detail_view_avl_stats_overall_ppc_score(
        self, mock_avl_line_level_require_attention, request_factory: RequestFactory
    ):
        """
        Test for 'Weekly overall AVL to timetables matching score' for AVL section.

        Args:
            request_factory (RequestFactory): Request Factory
        """
        org = OrganisationFactory()
        num_datasets = 5
        datasets = DatasetFactory.create_batch(
            num_datasets, organisation=org, dataset_type=DatasetType.AVL.value
        )
        mock_avl_line_level_require_attention.return_value = []
        revisions = [DatasetRevisionFactory(dataset=d) for d in datasets]
        AVLValidationReportFactory(
            created=datetime.datetime.now().date(),
            revision=revisions[0],
            critical_count=2,
        )

        context = DatafeedPipelineLoggerContext(object_id=-1)
        adapter = PipelineAdapter(getLogger("pytest"), {"context": context})
        for dataset in AVLDataset.objects.all():
            cache_avl_compliance_status(adapter, dataset.id)

        request = request_factory.get("/operators/")
        request.user = UserFactory()

        response = OperatorDetailView.as_view()(request, pk=org.id)
        assert response.status_code == 200
        context = response.context_data

        assert context["overall_ppc_score"] is None

    @patch(AVL_LINE_LEVEL_REQUIRE_ATTENTION)
    @override_flag(FeatureFlags.AVL_REQUIRES_ATTENTION.value, active=True)
    @override_flag(FeatureFlags.FARES_REQUIRE_ATTENTION.value, active=True)
    @override_flag(FeatureFlags.COMPLETE_SERVICE_PAGES.value, active=True)
    def test_operator_detail_view_api_urls(
        self, mock_line_level_require_attention, request_factory: RequestFactory
    ):
        """
        Test for timetable, location and fares API URLs.

        Args:
            request_factory (RequestFactory): Request Factory
        """
        nocs = ["NOC1", "NOC2"]
        org = OrganisationFactory(nocs=nocs)
        user = UserFactory()

        mock_line_level_require_attention.return_value = []
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


class TestLTAView:
    def test_local_authority_view_basic(self, request_factory: RequestFactory):
        new_op = OperatorFactory()
        new_lic = LicenceFactory(number="LD0000007")
        o = OperatorModelFactory(**new_op.dict())
        l1 = LicenceModelFactory(**new_lic.dict())
        reg_number = l1.number + "/42"
        services = [
            ServiceModelFactory(
                operator=o,
                licence=l1,
                registration_number=reg_number,
                service_type_description="circular",
                variation_number=0,
            )
        ]

        ui_lta = UILtaFactory(id="1", name="first_ui_lta")

        LocalAuthorityFactory(
            id="1", name="first_LTA", registration_numbers=services, ui_lta=ui_lta
        )

        request = request_factory.get("/local-authority/")
        request.user = AnonymousUser()

        response = LocalAuthorityView.as_view()(request)

        assert response.status_code == 200
        assert (
            response.context_data["view"].template_name == "browse/local_authority.html"
        )
        assert response.context_data["q"] == ""
        assert response.context_data["ordering"] == "ui_lta_name_trimmed"

        ltas_context = response.context_data["ltas"]
        assert len(ltas_context) == 1

    def test_lta_view_order_by_name(self, request_factory: RequestFactory):
        ui_lta_1 = UILtaFactory(id="1", name="Derby City Council")
        ui_lta_2 = UILtaFactory(id="2", name="Cheshire East Council")
        LocalAuthorityFactory(id="1", name="Derby Council", ui_lta=ui_lta_1),
        LocalAuthorityFactory(id="2", name="Cheshire Council", ui_lta=ui_lta_2),

        request = request_factory.get("/local-authority/?ordering=ui_lta_name_trimmed")
        request.user = AnonymousUser()

        response = LocalAuthorityView.as_view()(request)
        assert response.status_code == 200
        expected_order = ["Cheshire East Council", "Derby City Council"]

        object_names = [
            obj.ui_lta_name() for obj in response.context_data["object_list"]
        ]
        assert object_names == expected_order

    def test_lta_view_pagination(self, request_factory: RequestFactory):
        get_lta_list_data()

        request = request_factory.get("/local-authority/?ordering=ui_lta_name_trimmed")
        request.user = AnonymousUser()

        response = LocalAuthorityView.as_view()(request)
        assert response.status_code == 200
        assert len(response.context_data["object_list"]) == 10

        request = request_factory.get(
            "/local-authority/?ordering=ui_lta_name_trimmed&page=2"
        )
        request.user = AnonymousUser()
        response = LocalAuthorityView.as_view()(request)

        assert response.status_code == 200
        assert len(response.context_data["object_list"]) == 1

    @override_flag(FeatureFlags.AVL_REQUIRES_ATTENTION.value, active=False)
    @override_flag(FeatureFlags.FARES_REQUIRE_ATTENTION.value, active=False)
    @override_flag(FeatureFlags.COMPLETE_SERVICE_PAGES.value, active=False)
    @override_flag(FeatureFlags.PREFETCH_DATABASE_COMPLIANCE_REPORT.value, active=False)
    @override_flag(FeatureFlags.UILTA_PREFETCH_SRA.value, active=False)
    def test_lta_view_complaint(self, request_factory: RequestFactory):
        get_lta_complaint_data_queryset()

        request = request_factory.get("/local-authority/?ordering=ui_lta_name_trimmed")
        request.user = AnonymousUser()
        response = LocalAuthorityView.as_view()(request)

        assert response.status_code == 200

        context = response.context_data
        # One out of season seasonal service reduces in scope services to 8
        assert context["total_in_scope_in_season_services"] == 8
        # 2 non-stale, 6 requiring attention. 6/8 services requiring attention = 75%
        assert context["services_require_attention_percentage"] == 75

    @override_flag(FeatureFlags.UILTA_PREFETCH_SRA.value, active=False)
    def test_lta_weca_view_complaint(self, request_factory: RequestFactory):
        get_lta_complaint_weca_data_queryset()

        request = request_factory.get("/local-authority/?ordering=ui_lta_name_trimmed")
        request.user = AnonymousUser()
        response = LocalAuthorityView.as_view()(request)

        assert response.status_code == 200

        context = response.context_data
        # One out of season seasonal service reduces in scope services to 8
        assert context["total_in_scope_in_season_services"] == 8
        # 2 non-stale, 6 requiring attention. 6/8 services requiring attention = 75%
        assert context["services_require_attention_percentage"] == 75

    def test_lta_view_auth_ids(self, request_factory: RequestFactory):
        get_lta_list_data()

        request = request_factory.get("/local-authority/?ordering=ui_lta_name_trimmed")
        request.user = AnonymousUser()

        response = LocalAuthorityView.as_view()(request)
        assert response.status_code == 200
        assert len(response.context_data["object_list"]) == 10

        for lta in response.context_data["object_list"]:
            if lta.ui_lta_name_trimmed == "Bournemouth, Christchurch and Poole Council":
                assert len(lta.auth_ids) == 2


class TestLineMetadataDetailView:
    @patch(
        "django.conf.settings.ABODS_AVL_LINE_LEVEL_DETAILS_URL", "http://dummy_url.com"
    )
    @patch("django.conf.settings.ABODS_AVL_AUTH_TOKEN", "dummy_token")
    @override_flag("dqs_require_attention", active=True)
    @override_flag("dqs_require_attention", active=True)
    @override_flag("is_complete_service_pages_active", active=True)
    @override_flag("is_avl_require_attention_active", active=True)
    @patch(REQUEST, side_effect=mocked_requests_post_valid_response)
    @patch.object(publish_attention, "get_vehicle_activity_operatorref_linename")
    def test_avl_data(self, mock_vehicle_activity, request_factory):
        """Test AVL data"""

        mock_vehicle_activity.return_value = pd.DataFrame(
            {"OperatorRef": ["SDCU"], "LineRef": ["line2"]}
        )
        org = OrganisationFactory()
        total_services = 4
        licence_number = "PD5000124"
        all_service_codes = [f"{licence_number}:{n}" for n in range(total_services)]
        all_line_names = [f"line:{n}" for n in range(total_services)]
        dataset1 = DatasetFactory(organisation=org)

        # Setup three TXCFileAttributes that will be 'Up to Date'
        txcfileattribute1 = TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[0],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[0]],
        )

        response = LineMetadataDetailView.get_avl_data(
            None, [txcfileattribute1], all_line_names[0]
        )
        assert isinstance(response, dict)
        assert "is_avl_compliant" in response


class TestLTADetailView:
    def test_local_authority_detail_view_timetable_stats_not_compliant(
        self, request_factory: RequestFactory
    ):
        """Test LTA details view stat with non complaint data in_scope_in_season
        Count there are few which required attention

        Args:
            request_factory (RequestFactory): Request Factory
        """
        local_authority = get_lta_complaint_data_queryset()

        request = request_factory.get(
            f"/local-authority/?auth_ids={local_authority.id}"
        )
        request.user = UserFactory()
        response = LocalAuthorityDetailView.as_view()(request, pk=local_authority.id)

        assert response.status_code == 200
        context = response.context_data
        assert (
            context["view"].template_name
            == "browse/local_authority/local_authority_detail.html"
        )
        # One out of season seasonal service reduces in scope services to 8
        assert context["total_in_scope_in_season_services"] == 8
        # 2 non-stale, 6 requiring attention. 6/8 services requiring attention = 75%
        assert context["services_require_attention_percentage"] == 75

    def test_local_authority_detail_view_timetable_stats_compliant(
        self, request_factory: RequestFactory
    ):
        """Test LTA details view stat with all complaint data in_scope_in_season count
        There are zero which required attention

        Args:
            request_factory (RequestFactory): Request Factory
        """
        org = OrganisationFactory()
        month = timezone.now().date() + datetime.timedelta(weeks=4)
        two_months = timezone.now().date() + datetime.timedelta(weeks=8)
        service = []
        total_services = 4
        licence_number = "PD5000124"
        all_service_codes = [f"{licence_number}:{n}" for n in range(total_services)]
        bods_licence = BODSLicenceFactory(organisation=org, number=licence_number)
        dataset1 = DatasetFactory(organisation=org)
        dataset2 = DatasetFactory(organisation=org)

        # Setup three TXCFileAttributes that will be 'Up to Date'
        TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[0],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
        )
        TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[1],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
        )
        TXCFileAttributesFactory(
            revision=dataset2.live_revision,
            service_code=all_service_codes[2],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
        )

        # Create Out of Season Seasonal Service
        SeasonalServiceFactory(
            licence=bods_licence,
            start=month,
            end=two_months,
            registration_code=int(all_service_codes[3][-1:]),
        )
        SeasonalServiceFactory(
            licence=bods_licence,
            start=timezone.now().date(),
            end=month,
            registration_code=int(all_service_codes[2][-1:]),
        )

        otc_lic = LicenceModelFactory(number=licence_number)
        for code in all_service_codes:
            service.append(
                ServiceModelFactory(
                    licence=otc_lic,
                    registration_number=code.replace(":", "/"),
                    effective_date=datetime.date(year=2020, month=1, day=1),
                    service_number="line1",
                )
            )

        ui_lta = UILtaFactory(
            name="Dorset County Council",
        )
        local_authority = LocalAuthorityFactory(
            id="1",
            name="Dorset Council",
            ui_lta=ui_lta,
            registration_numbers=service,
        )
        AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

        request = request_factory.get(
            f"/local-authority/?auth_ids={local_authority.id}"
        )
        request.user = UserFactory()

        response = LocalAuthorityDetailView.as_view()(request, pk=local_authority.id)
        assert response.status_code == 200
        context = response.context_data
        assert (
            context["view"].template_name
            == "browse/local_authority/local_authority_detail.html"
        )
        assert context["total_in_scope_in_season_services"] == 3
        assert context["services_require_attention_percentage"] == 0

    @override_flag(FeatureFlags.DQS_REQUIRE_ATTENTION.value, active=True)
    def test_local_authority_detail_view_dqs_non_compliant(
        self, request_factory: RequestFactory
    ):
        """Test LTA details view stat with all complaint data in_scope_in_season count
        There are zero which required attention

        Args:
            request_factory (RequestFactory): Request Factory
        """
        org = OrganisationFactory()
        month = timezone.now().date() + datetime.timedelta(weeks=4)
        two_months = timezone.now().date() + datetime.timedelta(weeks=8)
        total_services = 4
        licence_number = "PD5000124"
        all_service_codes = [f"{licence_number}:{n}" for n in range(total_services)]
        all_line_names = [f"line:{n}" for n in range(total_services)]
        bods_licence = BODSLicenceFactory(organisation=org, number=licence_number)
        dataset1 = DatasetFactory(organisation=org)
        dataset2 = DatasetFactory(organisation=org)

        # Setup three TXCFileAttributes that will be 'Up to Date'
        txcfileattribute1 = TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[0],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[0]],
        )
        TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[1],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[1]],
        )
        TXCFileAttributesFactory(
            revision=dataset2.live_revision,
            service_code=all_service_codes[2],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[2]],
        )

        # Create Out of Season Seasonal Service
        SeasonalServiceFactory(
            licence=bods_licence,
            start=month,
            end=two_months,
            registration_code=int(all_service_codes[3][-1:]),
        )
        SeasonalServiceFactory(
            licence=bods_licence,
            start=timezone.now().date(),
            end=month,
            registration_code=int(all_service_codes[2][-1:]),
        )

        # create transmodel servicepattern
        service_pattern = ServicePatternFactory(
            revision=dataset1.live_revision, line_name=txcfileattribute1.line_names[0]
        )

        # create transmodel service
        service = ServiceFactory(
            revision=dataset1.live_revision,
            name=all_line_names[0],
            service_code=all_service_codes[0],
            service_patterns=[service_pattern],
            txcfileattributes=txcfileattribute1,
        )

        # create transmodel servicepatternstop
        service_pattern_stop = ServicePatternStopFactory(
            service_pattern=service_pattern
        )

        # create DQS observation result
        check1 = ChecksFactory(queue_name="Queue1", importance="Critical")
        check2 = ChecksFactory(queue_name="Queue1")

        dataquality_report = ReportFactory(revision=dataset1.live_revision)

        taskresult = TaskResultsFactory(
            transmodel_txcfileattributes=txcfileattribute1,
            dataquality_report=dataquality_report,
            checks=check1,
        )
        observation_result = ObservationResultsFactory(
            service_pattern_stop=service_pattern_stop, taskresults=taskresult
        )

        otc_lic = LicenceModelFactory(number=licence_number)
        services = []
        for index, code in enumerate(all_service_codes):
            services.append(
                ServiceModelFactory(
                    licence=otc_lic,
                    registration_number=code.replace(":", "/"),
                    effective_date=datetime.date(year=2020, month=1, day=1),
                    service_number=all_line_names[index],
                )
            )

        ui_lta = UILtaFactory(
            name="Dorset County Council",
        )
        local_authority = LocalAuthorityFactory(
            id="1",
            name="Dorset Council",
            ui_lta=ui_lta,
            registration_numbers=services,
        )
        AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

        request = request_factory.get(
            f"/local-authority/?auth_ids={local_authority.id}"
        )
        request.user = UserFactory()

        response = LocalAuthorityDetailView.as_view()(request, pk=local_authority.id)
        assert response.status_code == 200
        context = response.context_data
        assert (
            context["view"].template_name
            == "browse/local_authority/local_authority_detail.html"
        )
        assert context["total_in_scope_in_season_services"] == 3
        assert context["services_require_attention_percentage"] == 33
        assert context["total_timetable_records_requiring_attention"] == 1

    def test_weca_local_authority_detail_view_timetable_stats_not_compliant(
        self, request_factory: RequestFactory
    ):
        """Test LTA WECA details view stat with non complaint data in_scope_in_season
        count there are few which required attention

        Args:
            request_factory (RequestFactory): Request Factory
        """
        local_authority = get_lta_complaint_weca_data_queryset()

        request = request_factory.get(
            f"/local-authority/?auth_ids={local_authority.id}"
        )
        request.user = UserFactory()
        response = LocalAuthorityDetailView.as_view()(request, pk=local_authority.id)

        assert response.status_code == 200
        context = response.context_data
        assert (
            context["view"].template_name
            == "browse/local_authority/local_authority_detail.html"
        )
        # One out of season seasonal service reduces in scope services to 8
        assert context["total_in_scope_in_season_services"] == 8
        # 2 non-stale, 6 requiring attention. 6/8 services requiring attention = 75%
        assert context["services_require_attention_percentage"] == 75

    def test_weca_local_authority_detail_view_timetable_stats_compliant(
        self, request_factory: RequestFactory
    ):
        """Test LTA WECA details view stat with complaint data in_scope_in_season
        count there are zero which required attention

        Args:
            request_factory (RequestFactory): Request Factory
        """
        org = OrganisationFactory()
        month = timezone.now().date() + datetime.timedelta(weeks=4)
        two_months = timezone.now().date() + datetime.timedelta(weeks=8)
        service = []
        total_services = 4
        licence_number = "PD5000124"
        service_code_prefix = "1101000"
        atco_code = "110"
        registration_code_index = -len(service_code_prefix) - 1
        all_service_codes = [
            f"{licence_number}:{service_code_prefix}{n}" for n in range(total_services)
        ]
        bods_licence = BODSLicenceFactory(organisation=org, number=licence_number)
        dataset1 = DatasetFactory(organisation=org)
        dataset2 = DatasetFactory(organisation=org)

        # Setup three TXCFileAttributes that will be 'Up to Date'
        TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[0],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
        )
        TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[1],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
        )
        TXCFileAttributesFactory(
            revision=dataset2.live_revision,
            service_code=all_service_codes[2],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
        )

        # Create Out of Season Seasonal Service
        SeasonalServiceFactory(
            licence=bods_licence,
            start=month,
            end=two_months,
            registration_code=int(all_service_codes[3][registration_code_index:]),
        )
        SeasonalServiceFactory(
            licence=bods_licence,
            start=timezone.now().date(),
            end=month,
            registration_code=int(all_service_codes[2][registration_code_index:]),
        )

        otc_lic = LicenceModelFactory(number=licence_number)
        for code in all_service_codes:
            ServiceModelFactory(
                licence=otc_lic,
                registration_number=code.replace(":", "/"),
                effective_date=datetime.date(year=2020, month=1, day=1),
                api_type=API_TYPE_WECA,
                atco_code=atco_code,
                service_number="line1",
            )

        ui_lta = UILtaFactory(
            name="Dorset County Council",
        )
        local_authority = LocalAuthorityFactory(
            id="1",
            name="Dorset Council",
            ui_lta=ui_lta,
            registration_numbers=service,
        )
        AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta, atco_code=atco_code)

        request = request_factory.get(
            f"/local-authority/?auth_ids={local_authority.id}"
        )
        request.user = UserFactory()

        response = LocalAuthorityDetailView.as_view()(request, pk=local_authority.id)
        assert response.status_code == 200
        context = response.context_data
        assert (
            context["view"].template_name
            == "browse/local_authority/local_authority_detail.html"
        )
        assert context["total_in_scope_in_season_services"] == 3
        assert context["services_require_attention_percentage"] == 0

    @override_flag("dqs_require_attention", active=True)
    @override_flag("is_complete_service_pages_active", active=True)
    @override_flag("is_avl_require_attention_active", active=True)
    @override_flag(FeatureFlags.FARES_REQUIRE_ATTENTION.value, active=True)
    @patch.object(publish_attention, "AbodsRegistery")
    @patch.object(publish_attention, "get_vehicle_activity_operatorref_linename")
    @freeze_time("2024-11-24T16:40:40.000Z")
    def test_complete_service_pages_lta_detail_view(
        self,
        mock_vehicle_activity,
        mock_abodsregistry,
        request_factory: RequestFactory,
    ):
        """Test LTA WECA details view stat with complaint data in_scope_in_season
        count there are zero which required attention

        Args:
            request_factory (RequestFactory): Request Factory
        """
        mock_registry_instance = MagicMock()
        mock_abodsregistry.return_value = mock_registry_instance
        mock_registry_instance.records.return_value = ["line1__SDCU", "line2__SDCU"]
        mock_vehicle_activity.return_value = pd.DataFrame(
            {"OperatorRef": ["SDCU"], "LineRef": ["line2"]}
        )
        org = OrganisationFactory()
        total_services = 9
        licence_number = "PD5000229"
        service = []
        service_code_prefix = "1101000"
        atco_code = "110"
        all_service_codes = [
            f"{licence_number}:{service_code_prefix}{n}" for n in range(total_services)
        ]
        bods_licence = BODSLicenceFactory(organisation=org, number=licence_number)
        dataset1 = DatasetFactory(organisation=org)
        txcfileattributes = []

        otc_lic = LicenceModelFactory(number=licence_number)
        for code in all_service_codes:
            service.append(
                ServiceModelFactory(
                    licence=otc_lic,
                    registration_number=code.replace(":", "/"),
                    effective_date=datetime.date(year=2020, month=1, day=1),
                    atco_code=atco_code,
                    service_number="line1",
                )
            )

        ui_lta = UILtaFactory(name="Dorset County Council")

        local_authority = LocalAuthorityFactory(
            id="1",
            name="Dorset Council",
            ui_lta=ui_lta,
            registration_numbers=service[0:6],
        )

        AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta, atco_code=atco_code)

        # Setup two TXCFileAttributes that will be 'Not Stale'
        txcfileattributes.append(
            TXCFileAttributesFactory(
                revision_id=dataset1.live_revision.id,
                licence_number=otc_lic.number,
                service_code=all_service_codes[0],
                operating_period_end_date=datetime.date.today()
                + datetime.timedelta(days=50),
                modification_datetime=timezone.now(),
                national_operator_code="SDCU",
            )
        )

        txcfileattributes.append(
            TXCFileAttributesFactory(
                revision_id=dataset1.live_revision.id,
                licence_number=otc_lic.number,
                service_code=all_service_codes[1],
                operating_period_end_date=datetime.date.today()
                + datetime.timedelta(days=75),
                modification_datetime=timezone.now() - datetime.timedelta(days=50),
                national_operator_code="SDCU",
            )
        )

        # Setup a draft TXCFileAttributes
        dataset2 = DraftDatasetFactory(organisation=org)
        txcfileattributes.append(
            TXCFileAttributesFactory(
                revision_id=dataset2.revisions.last().id,
                licence_number=otc_lic.number,
                service_code=all_service_codes[2],
            )
        )

        live_revision = dataset2.revisions.last()
        # Setup a TXCFileAttributes that will be 'Stale - 12 months old'
        txcfileattributes.append(
            TXCFileAttributesFactory(
                revision_id=live_revision.id,
                licence_number=otc_lic.number,
                service_code=all_service_codes[3],
                operating_period_end_date=None,
                modification_datetime=timezone.now() - datetime.timedelta(weeks=100),
                national_operator_code="SDCU",
            )
        )

        # Setup a TXCFileAttributes that will be 'Stale - 42 day look ahead'
        txcfileattributes.append(
            TXCFileAttributesFactory(
                revision_id=live_revision.id,
                licence_number=otc_lic.number,
                service_code=all_service_codes[4],
                operating_period_end_date=datetime.date.today()
                - datetime.timedelta(weeks=105),
                modification_datetime=timezone.now() - datetime.timedelta(weeks=100),
            )
        )

        # Setup a TXCFileAttributes that will be 'Stale - OTC Variation'
        txcfileattributes.append(
            TXCFileAttributesFactory(
                revision_id=live_revision.id,
                licence_number=otc_lic.number,
                service_code=all_service_codes[5],
                operating_period_end_date=datetime.date.today()
                + datetime.timedelta(days=50),
            )
        )
        check1 = ChecksFactory(importance=Level.critical.value)
        check2 = ChecksFactory(importance=Level.critical.value)

        services_with_critical = []
        services_with_advisory = []
        for i, txcfileattribute in enumerate(txcfileattributes):
            check_obj = check1 if i % 2 == 0 else check2
            if check_obj.importance == Level.critical.value:
                services_with_critical.append(
                    (txcfileattribute.service_code, txcfileattribute.line_names[0])
                )
            else:
                services_with_advisory.append(
                    (txcfileattribute.service_code, txcfileattribute.line_names[0])
                )

            task_result = TaskResultsFactory(
                status=TaskResultsStatus.PENDING.value,
                transmodel_txcfileattributes=txcfileattribute,
                dataquality_report=ReportFactory(revision=txcfileattribute.revision),
                checks=check_obj,
            )
            service_pattern = ServicePatternFactory(
                revision=txcfileattribute.revision,
                line_name=txcfileattribute.line_names[0],
            )
            ServiceFactory(
                revision=txcfileattribute.revision,
                service_code=txcfileattribute.service_code,
                name=txcfileattribute.line_names[0],
                service_patterns=[service_pattern],
                txcfileattributes=txcfileattribute,
            )

            service_pattern_stop = ServicePatternStopFactory(
                service_pattern=service_pattern
            )

            ObservationResultsFactory(
                service_pattern_stop=service_pattern_stop, taskresults=task_result
            )

        request = request_factory.get(
            f"/local-authority/?auth_ids={local_authority.id}"
        )
        request.user = UserFactory()

        response = LocalAuthorityDetailView.as_view()(request, pk=local_authority.id)
        assert response.status_code == 200
        context = response.context_data
        assert context["total_timetable_records_requiring_attention"] == 9
        assert context["total_location_records_requiring_attention"] == 7
        assert context["total_fares_records_requiring_attention"] == 9


class TestGlobalFeedbackView:
    view_name = "global-feedback"
    feedback_message = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."

    def test_global_feedback_form_fake_page_url(self, client):
        feedback_url = reverse(self.view_name)
        previous_url = "http://previous.url.bods/"
        response = client.post(
            feedback_url + "?url=" + previous_url,
            data={
                "page_url": "FAKE_URL",
                "satisfaction_rating": 3,
                "comment": self.feedback_message,
                "submit": "submit",
            },
            follow=True,
        )

        feedback = Feedback.objects.last()

        assert response.status_code == 200
        assert (
            response.context_data["view"].template_name == "pages/thank_you_page.html"
        )
        assert feedback.comment == self.feedback_message
        assert feedback.satisfaction_rating == 3
        assert feedback.page_url == previous_url

    def len_comment_number_carriage(self, comment: str) -> int:
        return len(comment.replace("\r", ""))

    @pytest.mark.parametrize(
        "comment",
        [
            DATA_SHORTER_MAXLENGTH_WITH_CARRIAGE_RETURN,
            DATA_LONG_MAXLENGTH_WITH_CARRIAGE_RETURN,
        ],
    )
    def test_global_feedback(self, comment, client):
        feedback_url = reverse(self.view_name)
        previous_url = "http://previous.url.bods/"
        response = client.post(
            feedback_url + "?url=" + previous_url,
            data={
                "page_url": previous_url,
                "satisfaction_rating": 5,
                "comment": comment,
                "submit": "submit",
            },
            follow=True,
        )

        feedback = Feedback.objects.last()
        len_comment = self.len_comment_number_carriage(comment)

        assert response.status_code == 200
        assert len(feedback.comment) == len_comment
        assert feedback.satisfaction_rating == 5
        assert feedback.page_url == previous_url

    @pytest.mark.parametrize(
        "comment",
        [
            DATA_LONGER_THAN_MAXLENGTH_WITH_CARRIAGE_RETURN,
            DATA_LONGER_THAN_MAXLENGTH,
        ],
    )
    def test_global_feedback_fail(self, comment, client):
        feedback_url = reverse(self.view_name)
        previous_url = "http://previous.url.bods/"
        client.post(
            feedback_url + "?url=" + previous_url,
            data={
                "page_url": previous_url,
                "satisfaction_rating": 5,
                "comment": comment,
                "submit": "submit",
            },
            follow=True,
        )

        feedback = Feedback.objects.last()

        assert feedback is None
