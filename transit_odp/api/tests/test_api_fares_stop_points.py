from django_hosts import reverse, reverse_host
from rest_framework import status
from rest_framework.test import APITestCase

import config.hosts
from transit_odp.api.app.serializers import StopPointSerializer
from transit_odp.fares.factories import FaresMetadataFactory
from transit_odp.fares.models import FaresMetadata
from transit_odp.naptan.factories import StopPointFactory
from transit_odp.organisation.factories import DatasetFactory, DatasetRevisionFactory
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import UserFactory
from transit_odp.users.utils import create_verified_org_user


class FareStopsAPITests(APITestCase):
    def setUp(self):
        host = config.hosts.DATA_HOST
        self.hostname = reverse_host(host)

        # Create developer
        self.developer = UserFactory.create(
            password="password", account_type=AccountType.developer.value
        )

        # Create organisation user
        self.org_user = create_verified_org_user()

        dataset = DatasetFactory()

        self.revision = DatasetRevisionFactory.create(
            dataset=dataset,
            published_by=None,
            last_modified_user=None,
            url_link="http://broken.test",
        )

        stops = StopPointFactory.create_batch(4)
        StopPointFactory.create_batch(4)

        FaresMetadataFactory.create(revision=self.revision, stops=stops)

        self.feed_list_url = (
            reverse("api:app:fare_stops-list", host=host)
            + "?revision="
            + str(self.revision.id)
        )

    def test_permissions__unauth_can_access(self):
        # Test
        response = self.client.get(self.feed_list_url, headers={"host": self.hostname})
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_permissions__developer_readonly(self):
        # Setup
        self.assertTrue(
            # Login into browser session
            self.client.login(username=self.developer.username, password="password")
        )

        # Test
        response = self.client.post(
            self.feed_list_url,
            {"name": "Some data"},
            format="json",
            headers={"host": self.hostname},
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get(self):
        """
        Ensure API returns all 'public' feeds (live or expiring)
        """
        # Set up
        self.assertTrue(
            # Login into browser session as developer
            self.client.login(username=self.developer.username, password="password")
        )
        #  Get expected data
        objs = FaresMetadata.objects.get(revision_id=self.revision.id).stops.all()
        serializer = StopPointSerializer(objs, many=True)
        expected = serializer.data

        # Test - Get response from API
        response = self.client.get(self.feed_list_url, headers={"host": self.hostname})
        actual = response.data["features"]

        # Assert
        self.assertEqual(actual, expected["features"])
        self.assertEqual(
            actual.__len__(), 4
        )  # includes stops belonging to the revision only

        feature = actual[0]
        fields = ["atco_code", "common_name"]
        for field in fields:
            self.assertIn(field, feature["properties"].keys())
