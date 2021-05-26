from django_hosts import reverse, reverse_host
from rest_framework import status
from rest_framework.test import APITestCase

import config.hosts
from transit_odp.api.app.serializers import ServicePatternSerializer
from transit_odp.transmodel.factories import ServicePatternFactory
from transit_odp.transmodel.models import ServicePattern
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import UserFactory
from transit_odp.users.utils import create_verified_org_user


class ServicePatternAPITests(APITestCase):
    def setUp(self):
        host = config.hosts.DATA_HOST
        self.hostname = reverse_host(host)
        self.feed_list_url = reverse("api:app:service_pattern-list", host=host)

        # Create developer
        self.developer = UserFactory.create(
            password="password", account_type=AccountType.developer.value
        )

        # Create organisation user
        self.org_user = create_verified_org_user()

        ServicePatternFactory.create_batch(4)

    def test_permissions__unauth_can_access(self):
        # Test
        response = self.client.get(self.feed_list_url, HTTP_HOST=self.hostname)
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
            HTTP_HOST=self.hostname,
        )

        # Assert
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # TODO - parameterize user accounts
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
        objs = ServicePattern.objects.all().add_service_name()
        serializer = ServicePatternSerializer(objs, many=True)
        expected = serializer.data

        # Test - Get response from API
        response = self.client.get(self.feed_list_url, HTTP_HOST=self.hostname)
        actual = response.data["features"]

        # Assert
        self.assertEqual(actual, expected["features"])

        feature = actual[0]
        fields = [
            "service_pattern_id",
            "revision",
            "origin",
            "destination",
            "description",
            "service_name",
        ]
        for field in fields:
            self.assertIn(field, feature["properties"].keys())
