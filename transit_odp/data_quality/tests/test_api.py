import random

from django_hosts import reverse, reverse_host
from rest_framework import status
from rest_framework.test import APITestCase

import config.hosts
from transit_odp.data_quality.factories import (
    ServiceLinkFactory,
    ServicePatternFactory,
    StopPointFactory,
)
from transit_odp.data_quality.helpers import create_comma_separated_string
from transit_odp.data_quality.models import ServiceLink, ServicePattern, StopPoint
from transit_odp.users.utils import create_verified_org_user


class BaseAPITests:
    """
    Mixin for testing the Data Quality API endpoints that serve the map.

    Inheriting classes will generally also need to inherit APITestCase.
    """

    @classmethod
    def setUpTestData(cls):
        cls.host = config.hosts.PUBLISH_HOST
        cls.hostname = reverse_host(cls.host)
        # permissions for this API don't currently require an org admin,
        # just an authenticated user
        cls.org_admin = create_verified_org_user()

        # attributes most likely to vary in test subclasses
        cls.model = None
        cls.endpoint_url = ""
        cls.expected_feature_properties_keys = []

    # helper method
    def get_response(self, url):
        self.client.login(username=self.org_admin.username, password="password")
        return self.client.get(url, HTTP_HOST=self.hostname)

    def test_cannot_post(self):
        self.client.login(username=self.org_admin.username, password="password")
        response = self.client.post(self.endpoint_url, HTTP_HOST=self.hostname)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_cannot_put(self):
        self.client.login(username=self.org_admin.username, password="password")
        response = self.client.put(self.endpoint_url, HTTP_HOST=self.hostname)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_cannot_patch(self):
        self.client.login(username=self.org_admin.username, password="password")
        response = self.client.patch(self.endpoint_url, HTTP_HOST=self.hostname)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_cannot_delete(self):
        self.client.login(username=self.org_admin.username, password="password")
        response = self.client.delete(self.endpoint_url, HTTP_HOST=self.hostname)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_returns_expected_fields(self):
        # expected_keys come from GeoFeatureModelSerializer. Keys in properties come
        # from our serializers
        expected_keys = ("id", "type", "geometry", "properties")

        response = self.get_response(self.endpoint_url)
        feature = response.data["features"][0]  # get arbitrary feature to test

        # assertCountEqual is confusingly named -- it compares sequences, ignoring order
        self.assertCountEqual(feature.keys(), expected_keys)
        self.assertCountEqual(
            feature["properties"].keys(), self.expected_properties_keys
        )

    def test_returns_expected_features(self):
        # values_list returns a ValuesListQuerySet, but random.sample requires
        # list or set
        ids = list(self.model.objects.values_list("id", flat=True))
        selected_ids = random.sample(ids, 5)
        selected_ids_string = create_comma_separated_string(selected_ids)
        url = f"{self.endpoint_url}?id__in={selected_ids_string}"

        response = self.get_response(url)
        response_feature_ids = [feature["id"] for feature in response.data["features"]]

        self.assertCountEqual(response_feature_ids, selected_ids)


class StopPointAPITest(BaseAPITests, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.model = StopPoint
        cls.endpoint_url = reverse("dq-api:stop_point-list", host=cls.host)
        cls.expected_properties_keys = ("effected", "name", "atco_code")

        StopPointFactory.create_batch(10)

    def test_returns_expected_effected_values(self):
        # values_list returns a ValuesListQuerySet, but random.sample requires
        # list or set
        ids = list(self.model.objects.values_list("id", flat=True))
        effected_ids = random.sample(ids, 5)
        ids_string = create_comma_separated_string(ids)
        effected_ids_string = create_comma_separated_string(effected_ids)
        url = f"{self.endpoint_url}?id__in={ids_string}&effected={effected_ids_string}"

        response = self.get_response(url)
        features = response.data["features"]

        for feature in features:
            if feature["id"] in effected_ids:
                self.assertTrue(feature["properties"]["effected"])
            else:
                self.assertFalse(feature["properties"]["effected"])


class ServicePaternAPITests(BaseAPITests, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.model = ServicePattern
        cls.endpoint_url = reverse("dq-api:service_pattern-list", host=cls.host)
        cls.expected_properties_keys = ("service_name",)

        ServicePatternFactory.create_batch(5)


class ServiceLinkAPITests(BaseAPITests, APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.model = ServiceLink
        cls.endpoint_url = reverse("dq-api:service_link-list", host=cls.host)
        cls.expected_properties_keys = ("service_name",)

        ServiceLinkFactory.create_batch(10)
