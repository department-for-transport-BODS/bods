from datetime import datetime, timedelta
from unittest import skip

import pytz
from django.db.models import Q
from django_hosts.resolvers import reverse, reverse_host
from rest_framework import status
from rest_framework.test import APITestCase

import config.hosts
from transit_odp.api.serializers import DatasetSerializer
from transit_odp.data_quality.factories.transmodel import DataQualityReportFactory
from transit_odp.naptan.factories import AdminAreaFactory
from transit_odp.organisation.constants import DatasetType, FeedStatus, TimetableType
from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetRevisionFactory,
    OrganisationFactory,
)
from transit_odp.organisation.models import Dataset, Organisation
from transit_odp.transmodel.factories import ServiceFactory
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import UserFactory
from transit_odp.users.utils import create_verified_org_user


class FeedAPITests(APITestCase):
    # Configure assert
    maxDiff = None

    def setUp(self):
        self.now = datetime.utcnow().isoformat()
        # timezone = pytz.timezone("Europe/London")
        # self.now = timezone.localize(date)

        self.yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
        self.tomorrow = (datetime.utcnow() + timedelta(days=1)).isoformat()
        # self.yesterday = timezone.localize(past_date)

        # TODO - test Publish service API
        host = config.hosts.DATA_HOST
        self.hostname = reverse_host(host)
        self.feed_list_url = reverse("api:feed-list", host=host)

        # Create developer
        self.developer = UserFactory.create(
            password="password", account_type=AccountType.developer.value
        )

        # Create organisation user
        self.org_user = create_verified_org_user()

        # create admin_areas
        self.admin_areas = AdminAreaFactory.create_batch(2)

        # Create a bunch of feeds
        for dataset in DatasetFactory.create_batch(
            4,
            organisation=self.org_user.organisation,
            live_revision__status=FeedStatus.live.value,
            live_revision__admin_areas=(self.admin_areas[0], self.admin_areas[1]),
            live_revision__first_service_start=pytz.timezone("Europe/London").localize(
                datetime.utcnow() + timedelta(days=1)
            ),
        ):
            DataQualityReportFactory(revision=dataset.live_revision)

        DatasetFactory.create_batch(
            4,
            dataset_type=DatasetType.AVL.value,
            organisation=self.org_user.organisation,
            live_revision__status=FeedStatus.live.value,
            live_revision__admin_areas=(self.admin_areas[0], self.admin_areas[1]),
            live_revision__first_service_start=pytz.timezone("Europe/London").localize(
                datetime.utcnow() + timedelta(days=1)
            ),
        )
        expiring_datasets = DatasetFactory.create_batch(
            1,
            organisation=self.org_user.organisation,
            live_revision__status=FeedStatus.expiring.value,
            live_revision__admin_areas=(self.admin_areas[1],),
        )
        revision = expiring_datasets[0].live_revision
        service = ServiceFactory(revision=revision)
        service.name = "1"
        service.other_names = ["1", "3"]
        service.save()

        # create unpublished revisions
        DatasetRevisionFactory.create_batch(
            2,
            dataset__organisation=self.org_user.organisation,
            status=FeedStatus.error.value,
            is_published=False,
            first_service_start=pytz.timezone("Europe/London").localize(
                datetime.utcnow()
            ),
        )
        expired_datasets = DatasetFactory.create_batch(
            2,
            organisation=self.org_user.organisation,
            live_revision__status=FeedStatus.expired.value,
            live_revision__is_published=True,
            live_revision__first_service_start=pytz.timezone("Europe/London").localize(
                datetime.utcnow() - timedelta(days=1)
            ),
        )

        revision_1 = expired_datasets[0].live_revision
        service1 = ServiceFactory(revision=revision_1)
        service1.name = "1"
        service1.other_names = ["2", "3"]
        service1.save()

        revision_2 = expired_datasets[1].live_revision
        service2 = ServiceFactory(revision=revision_2)
        service2.name = "2"
        service2.other_names = ["1"]
        service2.save()

        DatasetFactory.create_batch(
            2,
            organisation=self.org_user.organisation,
            live_revision__status=FeedStatus.expired.value,
        )

    def test_permissions__unauth_no_access(self):
        # Test
        response = self.client.get(self.feed_list_url, HTTP_HOST=self.hostname)
        # Assert
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permissions__developer_read(self):
        """Developer can read public feeds"""
        self.assertTrue(
            self.client.login(username=self.developer.username, password="password")
        )
        feeds = (
            Dataset.objects.get_published()
            .get_active_org()
            .get_live_dq_score()
            .add_is_live_pti_compliant()
            .get_viewable_statuses()
            .add_organisation_name()
            .order_by("id")
            .filter(dataset_type=DatasetType.TIMETABLE.value)
        )
        serializer = DatasetSerializer(feeds, many=True)
        expected = serializer.data
        response = self.client.get(self.feed_list_url, HTTP_HOST=self.hostname)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        actual = response.data["results"]

        # Assert
        self.assertEqual(actual, expected)

    def test_permissions__developer_readonly(self):
        # Setup
        self.assertTrue(
            # Login into browser session
            self.client.login(username=self.developer.username, password="password")
        )

        # Test
        response = self.client.post(
            self.feed_list_url,
            {"name": "Developer cannot create feeds"},
            format="json",
            HTTP_HOST=self.hostname,
        )

        # Assert
        # For now, API is readonly for everyone, so response should be method not
        # allowed rather than forbidden
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @skip("Test should be implemented when working on publishing via API")
    def test_permissions__orguser_create(self):
        # Setup
        self.assertTrue(
            # Login into browser session
            self.client.login(username=self.org_user.username, password="password")
        )

        # Test
        with open("transit_odp/indexing/tests/data/ea_20-1A-A-y08-1.xml", "r") as fp:
            response = self.client.post(
                self.feed_list_url,
                {
                    "name": "New Feed",
                    "description": "Feed created by organisation user via REST api",
                    "comment": "",
                    "upload_file": fp,
                },
                format="json",
                HTTP_HOST=self.hostname,
            )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        feed = Dataset.objects.get_live_dq_score().latest()
        self.assertEqual(feed.name, "New Feed")
        self.assertEqual(
            feed.description, "Feed created by organisation user via REST api"
        )
        # cannot check filename as this may be uniquified by Django
        self.assertTrue(feed.upload_file)

    def test_feeds(self):
        """
        Ensure API returns all 'public' feeds
        """
        self.assertTrue(
            self.client.login(username=self.developer.username, password="password")
        )
        objs = (
            Dataset.objects.get_published()
            .get_active_org()
            .get_live_dq_score()
            .get_viewable_statuses()
            .add_is_live_pti_compliant()
            .add_live_data()
            .add_organisation_name()
            .order_by("id")
            .filter(dataset_type=DatasetType.TIMETABLE.value)
        )
        serializer = DatasetSerializer(objs, many=True)
        expected = serializer.data

        response = self.client.get(self.feed_list_url, HTTP_HOST=self.hostname)
        actual = response.data["results"]

        self.assertEqual(actual, expected)

    def test_status_filter(self):
        """
        Ensures API response filters feed by status
        """
        self.assertTrue(
            self.client.login(username=self.developer.username, password="password")
        )
        objs = (
            Dataset.objects.get_published()
            .add_organisation_name()
            .get_active_org()
            .get_live_dq_score()
            .add_is_live_pti_compliant()
            .filter(live_revision__status="live")
            .order_by("id")
            .filter(dataset_type=DatasetType.TIMETABLE.value)
        )
        serializer = DatasetSerializer(objs, many=True)
        expected = serializer.data

        params = {"status": "live"}
        response = self.client.get(self.feed_list_url, params, HTTP_HOST=self.hostname)
        actual = response.data["results"]

        self.assertEqual(actual, expected)

    def test_blank_status_filter(self):
        """
        Ensures API response filters feed by status=live when query param status is not supplied
        """
        self.assertTrue(
            self.client.login(username=self.developer.username, password="password")
        )
        objs = (
            Dataset.objects.get_published()
            .add_organisation_name()
            .get_active_org()
            .get_live_dq_score()
            .add_is_live_pti_compliant()
            .filter(live_revision__status="live")
            .order_by("id")
            .filter(dataset_type=DatasetType.TIMETABLE.value)
        )
        serializer = DatasetSerializer(objs, many=True)
        expected = serializer.data

        params = {"status": ""}
        response = self.client.get(self.feed_list_url, params, HTTP_HOST=self.hostname)
        actual = response.data["results"]

        self.assertEqual(actual, expected)

    def test_noc_whole_string_filter(self):
        """
        Ensures API response filters feed by noc whole
        """
        self.assertTrue(
            self.client.login(username=self.developer.username, password="password")
        )
        organisation = self.org_user.organisation

        nocs = [organisation.nocs.first().noc]
        organisations = (
            Organisation.objects.filter(nocs__noc__in=nocs)
            .order_by("id")
            .distinct("id")
        )
        objs = (
            Dataset.objects.get_published()
            .get_active_org()
            .get_live_dq_score()
            .get_viewable_statuses()
            .add_is_live_pti_compliant()
            .add_live_data()
            .add_organisation_name()
            .filter(organisation__in=organisations)
            .order_by("id")
            .filter(dataset_type=DatasetType.TIMETABLE.value)
        )
        serializer = DatasetSerializer(objs, many=True)
        expected = serializer.data

        params = {"noc": nocs}
        response = self.client.get(self.feed_list_url, params, HTTP_HOST=self.hostname)
        actual = response.data["results"]

        self.assertEqual(actual, expected)

    def test_noc_part_string_filter(self):
        """
        Ensures API response filters feed by noc part
        Testcase to test fix for BODP-1232: API Query Parameters -
        A partial NOC should not bringing back no datasets


        Given a noc of NOC1234, a noc query param 1234 should return 0 datasets.
        """
        self.assertTrue(
            self.client.login(username=self.developer.username, password="password")
        )
        organisation = self.org_user.organisation
        noc = organisation.nocs.first().noc
        partial_noc = noc[2:]
        expected = 0
        params = {"noc": [partial_noc]}
        response = self.client.get(self.feed_list_url, params, HTTP_HOST=self.hostname)
        actual = len(response.data["results"])
        self.assertEqual(actual, expected)

    def test_list_of_nocs_filter(self):
        """
        Ensures API response filters feed by list of noc
        Testcase to test fix for BODP-1232: API Query Parameters -
        NOC not bringing back correct information
        """
        self.assertTrue(
            self.client.login(username=self.developer.username, password="password")
        )
        organisation = self.org_user.organisation
        nocs = [ops.noc for ops in organisation.nocs.all()]
        organisations = (
            Organisation.objects.filter(nocs__noc__in=nocs)
            .order_by("id")
            .distinct("id")
        )
        objs = (
            Dataset.objects.get_published()
            .add_live_data()
            .get_active_org()
            .get_viewable_statuses()
            .get_live_dq_score()
            .add_is_live_pti_compliant()
            .add_organisation_name()
            .filter(organisation__in=organisations)
            .filter(dataset_type=DatasetType.TIMETABLE.value)
            .order_by("id")
        )

        serializer = DatasetSerializer(objs, many=True)
        expected = serializer.data
        params = {"noc": nocs}
        response = self.client.get(self.feed_list_url, params, HTTP_HOST=self.hostname)
        actual = response.data["results"]

        self.assertEqual(actual, expected)

    def test_admin_area_filter(self):
        """
        Ensures API response filters feed by admin_area
        """
        self.assertTrue(
            self.client.login(username=self.developer.username, password="password")
        )
        atco_code = self.admin_areas[0].atco_code
        objs = (
            Dataset.objects.get_published()
            .add_organisation_name()
            .get_active_org()
            .get_live_dq_score()
            .add_is_live_pti_compliant()
            .add_live_data()
            .filter(live_revision__admin_areas__atco_code=atco_code)
            .order_by("id")
            .filter(dataset_type=DatasetType.TIMETABLE.value)
        )
        serializer = DatasetSerializer(objs, many=True)
        expected = serializer.data
        params = {"adminArea": atco_code}
        response = self.client.get(self.feed_list_url, params, HTTP_HOST=self.hostname)
        actual = response.data["results"]
        self.assertEqual(actual, expected)

    def test_only_published_feeds(self):
        """
        Ensures API response filters by only published feeds
        """
        self.assertTrue(
            self.client.login(username=self.developer.username, password="password")
        )
        datasets = (
            Dataset.objects.get_published()
            .add_organisation_name()
            .get_active_org()
            .get_live_dq_score()
            .get_viewable_statuses()
            .add_is_live_pti_compliant()
            .add_live_data()
            .order_by("id")
            .filter(dataset_type=DatasetType.TIMETABLE.value)
        )
        serializer = DatasetSerializer(datasets, many=True)
        expected = serializer.data

        response = self.client.get(self.feed_list_url, HTTP_HOST=self.hostname)
        actual = response.data["results"]

        self.assertEqual(expected, actual)

    def test_start_date_start_filter(self):
        """
        Ensures API response filters feed by start date start
        """
        self.assertTrue(
            self.client.login(username=self.developer.username, password="password")
        )
        objs = (
            Dataset.objects.get_published()
            .get_active_org()
            .get_live_dq_score()
            .add_is_live_pti_compliant()
            .get_viewable_statuses()
            .add_organisation_name()
            .filter(
                Q(live_revision__first_service_start__gte=self.now)
                | Q(live_revision__first_service_start__isnull=True)
            )
            .order_by("id")
            .filter(dataset_type=DatasetType.TIMETABLE.value)
        )
        serializer = DatasetSerializer(objs, many=True)
        expected = serializer.data

        params = {"startDateStart": self.now}
        response = self.client.get(self.feed_list_url, params, HTTP_HOST=self.hostname)
        actual = response.data["results"]

        self.assertEqual(actual, expected)

    def test_start_date_start_end_filter(self):
        """
        Ensures API response filters feed by start date start and end
        """
        self.assertTrue(
            self.client.login(username=self.developer.username, password="password")
        )
        start_date = self.yesterday
        end_date = self.now
        objs = (
            Dataset.objects.get_published()
            .get_active_org()
            .get_live_dq_score()
            .add_is_live_pti_compliant()
            .get_viewable_statuses()
            .add_organisation_name()
            .filter(
                Q(live_revision__first_service_start__gte=start_date)
                | Q(live_revision__first_service_start__isnull=True)
            )
            .filter(
                Q(live_revision__first_service_start__lte=end_date)
                | Q(live_revision__first_service_start__isnull=True)
            )
            .order_by("id")
        )
        serializer = DatasetSerializer(objs, many=True)
        expected = serializer.data
        params = {"startDateStart": start_date, "startDateEnd": end_date}
        response = self.client.get(self.feed_list_url, params, HTTP_HOST=self.hostname)
        actual = response.data["results"]
        self.assertEqual(actual, expected)

    def test_invalid_param_key(self):
        """
        Ensures API response filters invalid query param keys
        """
        # Set up
        self.assertTrue(
            # Login into browser session as developer
            self.client.login(username=self.developer.username, password="password")
        )

        expected = {"Unsupported query parameter": ["Status", "testparam"]}

        # Test - Get response from API
        url = (
            reverse("api:feed-list", host=config.hosts.DATA_HOST)
            + "?Status=live&testparam=test"
        )
        response = self.client.get(url, HTTP_HOST=self.hostname)

        # Assert
        self.assertEqual(response.status_code, 400)  # Bad request
        self.assertEqual(response.data, expected)

    def test_invalid_param_value(self):
        """
        Ensures API response filters invalid query param value for limit and offset
        """
        # Set up
        self.assertTrue(
            # Login into browser session as developer
            self.client.login(username=self.developer.username, password="password")
        )

        expected = {"Unsupported query parameter value for": ["limit", "offset"]}

        # Test - Get response from API
        url = (
            reverse("api:feed-list", host=config.hosts.DATA_HOST)
            + "?limit=123abc&offset=bg234"
        )
        response = self.client.get(url, HTTP_HOST=self.hostname)

        # Assert
        self.assertEqual(response.status_code, 400)  # Bad request
        self.assertEqual(response.data, expected)

    def test_api_key_filter(self):
        """
        Ensures API response filters feed by start date start
        """
        self.assertTrue(
            self.client.login(username=self.developer.username, password="password")
        )

        test_date = self.now
        objs = (
            Dataset.objects.get_published()
            .get_active_org()
            .get_live_dq_score()
            .add_is_live_pti_compliant()
            .add_organisation_name()
            .filter(
                Q(live_revision__first_service_start__gte=test_date)
                | Q(live_revision__first_service_start__isnull=True)
            )
            .order_by("id")
            .filter(dataset_type=DatasetType.TIMETABLE.value)
        )
        serializer = DatasetSerializer(objs, many=True)
        expected = serializer.data

        params = {
            "startDateStart": test_date,
            "api_key": str(self.developer.auth_token),
        }
        response = self.client.get(self.feed_list_url, params, HTTP_HOST=self.hostname)
        actual = response.data["results"]
        self.assertEqual(actual, expected)

    def test_search_for_non_existent_feed(self):
        """
        Ensures API returns nothing dues to bad search, protects against BODP-1198
        """
        # Set up
        self.assertTrue(
            # Login into browser session as developer
            self.client.login(username=self.developer.username, password="password")
        )

        # Test - Get response from API
        url = (
            reverse("api:feed-list", host=config.hosts.DATA_HOST)
            + "?search=nobodywilleversearchthis"
        )
        response = self.client.get(url, HTTP_HOST=self.hostname)
        self.assertEqual(response.status_code, 200, "Check this hasnt blown up")
        self.assertEqual(response.data["results"], [], "check we get an empty list")

    def test_search_feed(self):
        """
        Ensures API returns nothing dues to bad search, protects against BODP-1198
        """
        # Set up
        self.assertTrue(
            # Login into browser session as developer
            self.client.login(username=self.developer.username, password="password")
        )

        dataset_to_test = (
            Dataset.objects.get_published().get_live_dq_score().get_active_org().first()
        )
        # double check there are no name clashed VERY UNLIKELY
        objs = (
            Dataset.objects.select_related("live_revision")
            .get_live_dq_score()
            .get_viewable_statuses()
            .add_is_live_pti_compliant()
            .filter(live_revision__name=dataset_to_test.live_revision.name)
        )
        serializer = DatasetSerializer(objs, many=True)
        expected = serializer.data

        # Test - Get response from API
        url = (
            reverse("api:feed-list", host=config.hosts.DATA_HOST)
            + f"?search={dataset_to_test.live_revision.name}"
        )
        response = self.client.get(url, HTTP_HOST=self.hostname)
        self.assertEqual(response.status_code, 200, "Check this hasnt blown up")
        self.assertEqual(response.data["results"], expected)

    def test_feed_from_active_org(self):
        """
        Ensure API returns all 'public' feeds live
        """
        self.assertTrue(
            self.client.login(username=self.developer.username, password="password")
        )

        org1 = OrganisationFactory.create(is_active=False)
        DatasetFactory.create_batch(5, organisation=org1)
        objs = (
            Dataset.objects.get_published()
            .get_active_org()
            .get_viewable_statuses()
            .get_live_dq_score()
            .add_is_live_pti_compliant()
            .add_live_data()
            .add_organisation_name()
            .order_by("id")
            .filter(dataset_type=TimetableType)
        )
        serializer = DatasetSerializer(objs, many=True)
        expected = serializer.data
        response = self.client.get(self.feed_list_url, HTTP_HOST=self.hostname)
        actual = response.data["results"]
        self.assertEqual(actual, expected)
