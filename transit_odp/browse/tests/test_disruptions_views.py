import datetime
import pytest
import uuid
from django_hosts import reverse

from config.hosts import DATA_HOST
from unittest.mock import patch

from transit_odp.organisation.constants import DatasetType


pytestmark = pytest.mark.django_db


class TestDisruptionsDataView:
    host = DATA_HOST
    url = reverse("disruptions-data", host=host)
    template_path = "browse/disruptions/disruptions_data.html"
    org_data = [
        {
            "id": "5a6e9348-9bd7-46d8-b939-a394876b2ea5",
            "name": "TEST1",
            "adminAreaCodes": ["099", "110", "146", "147"],
            "stats": {
                "disruptionReasonCount": {
                    "roadClosed": 13,
                    "routeDiversion": 1,
                    "maintenanceWork": 3,
                    "roadworks": 14,
                    "repairWork": 1,
                    "vandalism": 2,
                    "unknown": 1,
                },
                "networkWideConsequencesCount": 2,
                "operatorWideConsequencesCount": 9,
                "servicesAffected": 54,
                "servicesConsequencesCount": 32,
                "stopsAffected": 41,
                "stopsConsequencesCount": 7,
                "totalDisruptionsCount": 35,
                "totalConsequencesCount": 50,
                "lastUpdated": "2023-11-10T12:10:00.123Z",
            },
        },
        {
            "id": "169504c9-de3c-4399-a732-843a258e47ab",
            "name": "TEST2",
            "adminAreaCodes": ["083"],
            "stats": {
                "disruptionReasonCount": {
                    "routeDiversion": 1,
                },
                "networkWideConsequencesCount": 0,
                "operatorWideConsequencesCount": 1,
                "servicesAffected": 0,
                "servicesConsequencesCount": 0,
                "stopsAffected": 0,
                "stopsConsequencesCount": 0,
                "totalDisruptionsCount": 1,
                "totalConsequencesCount": 1,
                "lastUpdated": "",
            },
        },
    ]

    org_data_no_disruptions = [
        {
            "id": "169504c9-de3c-4399-a732-843a258e47ab",
            "name": "SYMCA",
            "adminAreaCodes": ["083"],
            "stats": {
                "disruptionReasonCount": {},
                "networkWideConsequencesCount": 0,
                "operatorWideConsequencesCount": 0,
                "servicesAffected": 0,
                "servicesConsequencesCount": 0,
                "stopsAffected": 0,
                "stopsConsequencesCount": 0,
                "totalDisruptionsCount": 0,
                "totalConsequencesCount": 0,
                "lastUpdated": "",
            },
        },
    ]

    org_data_no_disruptions_with_lastupdated = [
        {
            "id": "169504c9-de3c-4399-a732-843a258e47ab",
            "name": "SYMCA",
            "adminAreaCodes": ["083"],
            "stats": {
                "disruptionReasonCount": {},
                "networkWideConsequencesCount": 0,
                "operatorWideConsequencesCount": 0,
                "servicesAffected": 0,
                "servicesConsequencesCount": 0,
                "stopsAffected": 0,
                "stopsConsequencesCount": 0,
                "totalDisruptionsCount": 0,
                "totalConsequencesCount": 0,
                "lastUpdated": "2023-11-10T12:10:00.123Z",
            },
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
        assert response.context_data["object_list"][0]["name"] == "TEST1"

    @patch(
        "transit_odp.browse.views.disruptions_views._get_disruptions_organisation_data"
    )
    def test_display_with_api_data_with_no_disruptions(self, mrequests, client_factory):
        mrequests.return_value = (self.org_data_no_disruptions, 200)
        client = client_factory(host=self.host)
        response = client.get(self.url)

        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        assert len(response.context_data["object_list"]) == 0

    @patch(
        "transit_odp.browse.views.disruptions_views._get_disruptions_organisation_data"
    )
    def test_display_with_api_data_with_no_disruptions_with_lastupdated(
        self, mrequests, client_factory
    ):
        mrequests.return_value = (self.org_data_no_disruptions_with_lastupdated, 200)
        client = client_factory(host=self.host)
        response = client.get(self.url)

        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        assert len(response.context_data["object_list"]) == 1

    @patch(
        "transit_odp.browse.views.disruptions_views._get_disruptions_organisation_data"
    )
    def test_adds_dataset_type_to_response(self, mrequests, client_factory):
        mrequests.return_value = (self.org_data, 200)
        client = client_factory(host=self.host)
        response = client.get(self.url)

        assert (
            response.context_data["object_list"][0]["dataset_type"]
            == DatasetType.DISRUPTIONS.value
        )

    @patch(
        "transit_odp.browse.views.disruptions_views._get_disruptions_organisation_data"
    )
    def test_formats_disruptions_datetimes(self, mrequests, client_factory):
        mrequests.return_value = (self.org_data, 200)
        client = client_factory(host=self.host)
        response = client.get(self.url)

        assert response.context_data["object_list"][0]["stats"][
            "lastUpdated"
        ] == datetime.datetime(2023, 11, 10, 12, 10, 0, 123000)

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
        assert response.context_data["object_list"][0]["name"] == "TEST2"

    @patch(
        "transit_odp.browse.views.disruptions_views._get_disruptions_organisation_data"
    )
    def test_display_with_search_query(self, mrequests, client_factory):
        mrequests.return_value = (self.org_data, 200)
        client = client_factory(host=self.host)
        response = client.get(self.url, data={"q": "TEST2"})

        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        assert len(response.context_data["object_list"]) == 1
        assert response.context_data["object_list"][0]["name"] == "TEST2"


class TestDisruptionOrganisationDetailView:
    host = DATA_HOST
    url = reverse(
        "org-detail",
        kwargs={"orgId": uuid.UUID("5a6e9348-9bd7-46d8-b939-a394876b2ea5")},
        host=host,
    )
    template_path = "browse/disruptions/organisation/organisation_detail.html"
    org_data = {
        "name": "Awesome Org",
        "id": "eb153301-2a2b-4279-8670-13c57ad3e118",
        "adminAreaCodes": ["002", "083", "107", "146", "147"],
        "stats": {
            "disruptionReasonCount": {
                "constructionWork": 4,
                "ice": 10,
                "operatorCeasedTrading": 14,
                "accident": 15,
                "repairWork": 3,
                "insufficientDemand": 8,
                "signalFailure": 1,
                "roadClosed": 2,
                "industrialAction": 8,
                "maintenanceWork": 3,
                "routeDiversion": 1,
                "overcrowded": 5,
                "emergencyEngineeringWork": 4,
                "heavySnowFall": 1,
                "breakDown": 4,
                "incident": 2,
                "congestion": 3,
                "fog": 2,
            },
            "networkWideConsequencesCount": 66,
            "operatorWideConsequencesCount": 13,
            "servicesAffected": 10,
            "servicesConsequencesCount": 10,
            "stopsAffected": 3,
            "stopsConsequencesCount": 3,
            "totalDisruptionsCount": 90,
            "totalConsequencesCount": 92,
            "lastUpdated": "2023-11-10T12:10:00.123Z",
        },
    }

    @patch(
        "transit_odp.browse.views.disruptions_views._get_disruptions_organisation_data"
    )
    def test_organisation_details_view(self, mrequests, client_factory):
        mrequests.return_value = (self.org_data, 200)
        client = client_factory(host=self.host)
        response = client.get(self.url)

        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        assert response.context_data["object"] == self.org_data

    @patch(
        "transit_odp.browse.views.disruptions_views._get_disruptions_organisation_data"
    )
    def test_organisation_details_view_with_error_data(self, mrequests, client_factory):
        mrequests.return_value = (None, 200)
        client = client_factory(host=self.host)
        response = client.get(self.url)

        assert response.status_code == 200
        assert response.context_data["view"].template_name == self.template_path
        assert object not in response.context_data
