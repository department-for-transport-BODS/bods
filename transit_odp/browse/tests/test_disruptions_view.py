import pytest
from django_hosts import reverse

from config.hosts import DATA_HOST
from unittest.mock import patch, MagicMock
from django.test import TestCase
import json

pytestmark = pytest.mark.django_db


class TestDisruptionsDataView:
    host = DATA_HOST
    url = reverse("disruptions-data", host=host)
    template_path = "browse/disruptions/disruptions_data.html"
    org_data = [
        {
            "id": 50,
            "nocCode": "A2BR",
            "operatorPublicName": "A2B Bus and Coach",
            "vosaPsvLicenseName": "",
            "opId": "138245",
            "pubNmId": "96067",
            "nocCdQual": "",
            "changeDate": "",
            "changeAgent": "",
            "changeComment": "",
            "dateCeased": "",
            "dataOwner": "",
            "mode": "bus",
            "dataSource": "bods",
        },
        {
            "id": 50,
            "nocCode": "A2BR",
            "operatorPublicName": "D2B Bus and Coach",
            "vosaPsvLicenseName": "",
            "opId": "138245",
            "pubNmId": "96067",
            "nocCdQual": "",
            "changeDate": "",
            "changeAgent": "",
            "changeComment": "",
            "dateCeased": "",
            "dataOwner": "",
            "mode": "bus",
            "dataSource": "tnds",
        },
    ]

    @patch(
        "transit_odp.browse.views.disruptions_views._get_disruptions_organisation_data"
    )
    def test_display_with_api_data(self, mrequests, client_factory):

        mrequests.return_value = (self.org_data, 200)
        client = client_factory(host=self.host)
        response = client.get(self.url)

        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        assert len(response.context_data["object_list"]) == 2

    @patch(
        "transit_odp.browse.views.disruptions_views._get_disruptions_organisation_data"
    )
    def test_display_with_sort_by_name(self, mrequests, client_factory):
        mrequests.return_value = (self.org_data, 200)
        client = client_factory(host=self.host)
        response = client.get(self.url, data={"ordering": "-name"})

        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        assert len(response.context_data["object_list"]) == 2
        assert (
            response.context_data["object_list"][0]["operatorPublicName"]
            == "D2B Bus and Coach"
        )

    @patch(
        "transit_odp.browse.views.disruptions_views._get_disruptions_organisation_data"
    )
    def test_display_with_search(self, mrequests, client_factory):
        mrequests.return_value = (self.org_data, 200)
        client = client_factory(host=self.host)
        response = client.get(self.url, data={"q": "D2B"})

        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        assert len(response.context_data["object_list"]) == 1
        assert (
            response.context_data["object_list"][0]["operatorPublicName"]
            == "D2B Bus and Coach"
        )
        assert response.context_data["q"] == "D2B"
