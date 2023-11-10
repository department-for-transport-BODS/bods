from django.contrib.gis.geos import Point, Polygon
from django_hosts.resolvers import reverse, reverse_host
from rest_framework.test import APITestCase

import config.hosts
from transit_odp.api.serializers import FaresDatasetSerializer
from transit_odp.fares.factories import FaresMetadataFactory
from transit_odp.naptan.factories import StopPointFactory
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.organisation.models import Dataset
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import UserFactory
from transit_odp.users.utils import create_verified_org_user


class FaresAPITests(APITestCase):
    def setUp(self):
        host = config.hosts.DATA_HOST
        self.hostname = reverse_host(host)
        self.feed_list_url = reverse("api:fares-api-list", host=host)

        # Create developer
        self.developer = UserFactory.create(
            password="password", account_type=AccountType.developer.value
        )

        # Create organisation user
        self.org_user = create_verified_org_user()

        # create stops
        self.stop1 = StopPointFactory.create(
            location=Point(x=float(53.7678012), y=float(-3.0267357), srid=4326)
        )
        self.stop2 = StopPointFactory.create(
            location=Point(x=float(53.8824715), y=float(-3.0421374), srid=4326)
        )
        self.stop3 = StopPointFactory.create(
            location=Point(x=float(50.0524657), y=float(-5.3706624), srid=4326)
        )
        self.stop4 = StopPointFactory.create(
            location=Point(x=float(50.1024801), y=float(-5.2553059), srid=4326)
        )

        # create faresmetadata - this creates dataset, datasettrevisions as well
        fares_metadata = FaresMetadataFactory.create(
            revision=DatasetRevisionFactory(
                dataset__dataset_type=DatasetType.FARES.value
            ),
            stops=(self.stop1, self.stop2),
        )
        self.dataset1 = fares_metadata.datasetmetadata_ptr.revision.dataset

        fares_metadata1 = FaresMetadataFactory.create(
            revision=DatasetRevisionFactory(
                dataset__dataset_type=DatasetType.FARES.value
            ),
            stops=(self.stop3, self.stop4),
        )
        self.dataset2 = fares_metadata1.datasetmetadata_ptr.revision.dataset

    def test_search_bounding_box(self):
        """
        Ensures API returns datasets whose stops are within the bouding box
        """
        # Set up
        self.assertTrue(
            # Login into browser session as developer
            self.client.login(username=self.developer.username, password="password")
        )

        # draw bounding box around test stop locations - stop1, stop2
        bot_left_x, bot_left_y = float("inf"), float("inf")
        top_right_x, top_right_y = float("-inf"), float("-inf")
        for stop in [self.stop1, self.stop2]:
            bot_left_x = min(bot_left_x, stop.location.x)
            bot_left_y = min(bot_left_y, stop.location.y)
            top_right_x = max(top_right_x, stop.location.x)
            top_right_y = max(top_right_y, stop.location.y)

        geom = Polygon.from_bbox([top_right_y, bot_left_y, top_right_x, bot_left_x])

        objs = (
            Dataset.objects.select_related("live_revision")
            .prefetch_related("live_revision__metadata__faresmetadata__stops")
            .filter(
                live_revision__metadata__faresmetadata__stops__location__within=geom,
                dataset_type=DatasetType.FARES.value,
            )
        )
        self.assertEqual(len(objs), 1)
        self.assertTrue(objs[0] == self.dataset1)  # datasets with stop1, stop2

        serializer = FaresDatasetSerializer(objs, many=True)
        expected = serializer.data

        query_params = (
            f"?boundingBox={top_right_y},{bot_left_y},{top_right_x},{bot_left_x}"
        )
        url = reverse("api:fares-api-list", host=config.hosts.DATA_HOST) + query_params
        response = self.client.get(url, HTTP_HOST=self.hostname)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], expected)

    def test_bbox_with_empty_values(self):
        """
        Ensures API returns validation error when passed with empty values
        """
        # Set up
        self.assertTrue(
            # Login into browser session as developer
            self.client.login(username=self.developer.username, password="password")
        )

        expected = {"Unsupported query parameter value for": ["boundingBox"]}

        query_params = "?boundingBox=12,,,"
        url = reverse("api:fares-api-list", host=config.hosts.DATA_HOST) + query_params
        response = self.client.get(url, HTTP_HOST=self.hostname)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, expected)

    def test_bbox_with_alphabets(self):
        """
        Ensures API returns validation error when passed with alphabets
        """
        # Set up
        self.assertTrue(
            # Login into browser session as developer
            self.client.login(username=self.developer.username, password="password")
        )

        expected = {"Unsupported query parameter value for": ["boundingBox"]}

        # Test - Get response from API
        query_params = "?boundingBox=12,ab,cd,ef"
        url = reverse("api:fares-api-list", host=config.hosts.DATA_HOST) + query_params
        response = self.client.get(url, HTTP_HOST=self.hostname)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, expected)

    def test_bbox_with_more_values(self):
        """
        Ensures API returns validation error when passed with >4 values
        """
        # Set up
        self.assertTrue(
            # Login into browser session as developer
            self.client.login(username=self.developer.username, password="password")
        )

        expected = {"Unsupported query parameter value for": ["boundingBox"]}

        query_params = "?boundingBox=-3,-2,53.67,53.9,1,2"
        url = (
            reverse("api:fares-api-list", host=config.hosts.DATA_HOST) + query_params
        )  # bbox with more than 4 values
        response = self.client.get(url, HTTP_HOST=self.hostname)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, expected)

    def test_is_dummy_field_not_displayed_in_fares_dataset_response(self) -> None:
        """
        Ensures API doesn't return 'is_dummy' field in response
        """
        # Set up
        self.assertTrue(
            # Login into browser session as organisation user
            self.client.login(username=self.org_user.username, password="password")
        )
        url = reverse("api:fares-api-list", host=config.hosts.DATA_HOST)

        hidden_key = "is_dummy"

        response = self.client.get(url, HTTP_HOST=self.hostname)

        results_with_hidden_key_displayed = [
            result for result in response.data["results"] if hidden_key in result
        ]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)  # 2 entries created in SetUp
        self.assertEqual(len(results_with_hidden_key_displayed), 0)

    def test_status_filter(self):
        """
        Ensures API response filters feed by status
        """
        self.assertTrue(
            self.client.login(username=self.developer.username, password="password")
        )
        objs = (
            Dataset.objects.get_published()
            .filter(dataset_type=DatasetType.FARES.value)
            .get_viewable_statuses()
            .get_active_org()
            .add_organisation_name()
            .select_related("live_revision")
            .prefetch_related("organisation__nocs")
            .prefetch_related("live_revision__metadata__faresmetadata__stops")
        )
        serializer = FaresDatasetSerializer(objs, many=True)
        expected = serializer.data

        query_params = "?status=published"
        url = reverse("api:fares-api-list", host=config.hosts.DATA_HOST) + query_params
        response = self.client.get(url, HTTP_HOST=self.hostname)
        actual = response.data["results"]

        self.assertEqual(actual, expected)

    def assertEqualIgnoringFields(self, actual, expected, ignore_fields):
        """
        Custom assertion method to compare dictionaries while ignoring specified fields.
        """
        for field in ignore_fields:
            if field in actual:
                del actual[field]
            if field in expected:
                del expected[field]

        self.assertEqual(actual, expected)

    def test_blank_status_filter(self):
        """
        Ensures API response filters feed by status=live when query param status is not supplied
        """
        ignore_fields = ["id", "created", "modified"]
        self.assertTrue(
            self.client.login(username=self.developer.username, password="password")
        )
        objs = (
            Dataset.objects.get_published()
            .filter(dataset_type=DatasetType.FARES.value)
            .get_viewable_statuses()
            .get_active_org()
            .add_organisation_name()
            .select_related("live_revision")
            .prefetch_related("organisation__nocs")
            .prefetch_related("live_revision__metadata__faresmetadata__stops")
        )
        serializer = FaresDatasetSerializer(objs, many=True)
        expected = serializer.data
        print("expected", expected)
        query_params = ""
        url = reverse("api:fares-api-list", host=config.hosts.DATA_HOST) + query_params
        response = self.client.get(url, HTTP_HOST=self.hostname)
        actual = response.data["results"]
        print("actual", actual)

        self.assertEqualIgnoringFields(actual, expected, ignore_fields)
