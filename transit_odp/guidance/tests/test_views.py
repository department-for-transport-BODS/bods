import pytest
from django_hosts.resolvers import reverse

import config.hosts

pytestmark = pytest.mark.django_db


class TestLocalAuthorityReqView:
    host = config.hosts.PUBLISH_HOST

    def test_overview_section(self, client_factory):
        client = client_factory(host=self.host)
        url = reverse("guidance:support-local_authorities", host=self.host)
        response = client.get(url)
        assert response.status_code == 200
        assert (
            response.template_name == "guidance/local_authorities/overview.html"
        )  # default section is 'overview'
        assert response.context_data["current_section"].name == "overview"
        assert response.context_data["prev_section"] is None
        assert response.context_data["next_section"].name == "support"

    def test_intermediate_sections(self, client_factory):
        client = client_factory(host=self.host)
        url = reverse("guidance:support-local_authorities", host=self.host)
        response = client.get(url, data={"section": "naptan"})

        assert response.status_code == 200
        assert response.template_name == "guidance/local_authorities/naptan.html"
        assert response.context_data["current_section"].name == "naptan"
        assert response.context_data["prev_section"].name == "agent"
        assert response.context_data["next_section"].name == "local-auth-buses"

    def test_help_section(self, client_factory):
        client = client_factory(host=self.host)
        url = reverse("guidance:support-local_authorities", host=self.host)
        response = client.get(url, data={"section": "help"})

        assert response.status_code == 200
        assert response.template_name == "guidance/local_authorities/help.html"
        assert response.context_data["current_section"].name == "help"
        assert response.context_data["prev_section"].name == "usingbods"
        assert response.context_data["next_section"] is None

    def test_incorrect_section(self, client_factory):
        client = client_factory(host=self.host)
        url = reverse("guidance:support-local_authorities", host=self.host)
        response = client.get(url, data={"section": "idontexist"})

        assert response.status_code == 200
        assert (
            response.template_name == "guidance/local_authorities/overview.html"
        )  # default section is 'overview'
        assert response.context_data["current_section"].name == "overview"
        assert response.context_data["prev_section"] is None
        assert response.context_data["next_section"].name == "support"


class TestBusOperatorReqView:
    host = config.hosts.PUBLISH_HOST

    def test_overview_section(self, client_factory):
        client = client_factory(host=self.host)
        url = reverse("guidance:support-bus_operators", host=self.host)

        # Test
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert (
            response.template_name == "guidance/bus_operators/overview.html"
        )  # default section is 'Overview'
        assert response.context_data["current_section"].name == "overview"
        assert response.context_data["prev_section"] is None
        assert response.context_data["next_section"].name == "whopublishes"

    def test_intermediate_sections(self, client_factory):
        client = client_factory(host=self.host)
        url = reverse("guidance:support-bus_operators", host=self.host)
        # Test
        response = client.get(url, data={"section": "agents"})

        # Assert
        assert response.status_code == 200
        assert response.template_name == "guidance/bus_operators/agents.html"
        assert response.context_data["current_section"].name == "agents"
        assert response.context_data["prev_section"].name == "registering"
        assert response.context_data["next_section"].name == "publishing"

    def test_help_section(self, client_factory):
        client = client_factory(host=self.host)
        url = reverse("guidance:support-bus_operators", host=self.host)
        # Test
        response = client.get(url, data={"section": "help"})

        # Assert
        assert response.status_code == 200
        assert response.template_name == "guidance/bus_operators/help.html"
        assert response.context_data["current_section"].name == "help"
        assert response.context_data["prev_section"].name == "dataquality"
        assert response.context_data["next_section"] is None

    def test_incorrect_section(self, client_factory):
        client = client_factory(host=self.host)
        url = reverse("guidance:support-bus_operators", host=self.host)

        # Test
        response = client.get(url, data={"section": "blah"})

        # Assert
        assert response.status_code == 200
        assert (
            response.template_name == "guidance/bus_operators/overview.html"
        )  # default section is 'Overview'
        assert response.context_data["current_section"].name == "overview"
        assert response.context_data["prev_section"] is None
        assert response.context_data["next_section"].name == "whopublishes"


class TestDeveloperReqView:
    host = config.hosts.DATA_HOST

    def test_overview_section(self, client_factory):
        client = client_factory(host=self.host)
        url = reverse("guidance:support-developer", host=self.host)

        # Test
        response = client.get(url)

        # Assert
        assert response.status_code == 200
        assert (
            response.template_name == "guidance/developer/overview.html"
        )  # default section is 'Overview'
        assert response.context_data["current_section"].name == "overview"
        assert response.context_data["prev_section"] is None
        assert response.context_data["next_section"].name == "quickstart"

    @pytest.mark.parametrize(
        "current_section_name,prev_section_name,next_section_name,template",
        [
            (
                "quickstart",
                "overview",
                "databyoperator",
                "guidance/developer/quick_start.html",
            ),
            (
                "databyoperator",
                "quickstart",
                "browse",
                "guidance/developer/data_by_op_loc.html",
            ),
            (
                "browse",
                "databyoperator",
                "download",
                "guidance/developer/browse_data.html",
            ),
            (
                "download",
                "browse",
                "api",
                "guidance/developer/downloading_data.html",
            ),
            (
                "api",
                "download",
                "apireference",
                "guidance/developer/using_the_api.html",
            ),
            (
                "apireference",
                "api",
                "dataformats",
                "guidance/developer/api_reference.html",
            ),
            (
                "dataformats",
                "apireference",
                "maintainingqualitydata",
                "guidance/developer/data_formats.html",
            ),
            (
                "maintainingqualitydata",
                "dataformats",
                "help",
                "guidance/developer/maintaining_quality_data.html",
            ),
        ],
    )
    def test_intermediate_sections(
        self,
        current_section_name,
        prev_section_name,
        next_section_name,
        template,
        client_factory,
    ):
        client = client_factory(host=self.host)
        url = reverse("guidance:support-developer", host=self.host)
        response = client.get(url, data={"section": current_section_name})
        assert response.status_code == 200
        assert response.template_name == template
        assert response.context_data["current_section"].name == current_section_name
        assert response.context_data["prev_section"].name == prev_section_name
        assert response.context_data["next_section"].name == next_section_name

    def test_help_section(self, client_factory):
        client = client_factory(host=self.host)
        url = reverse("guidance:support-developer", host=self.host)

        # Test
        response = client.get(url, data={"section": "help"})

        # Assert
        assert response.status_code == 200
        assert response.template_name == "guidance/developer/help.html"
        assert response.context_data["current_section"].name == "help"
        assert response.context_data["prev_section"].name == "maintainingqualitydata"
        assert response.context_data["next_section"] is None

    def test_incorrect_section(self, client_factory):
        client = client_factory(host=self.host)
        url = reverse("guidance:support-developer", host=self.host)

        # Test
        response = client.get(url, data={"section": "Testsection"})

        # Assert
        assert response.status_code == 200
        assert (
            response.template_name == "guidance/developer/overview.html"
        )  # default section is 'Overview'
        assert response.context_data["current_section"].name == "overview"
        assert response.context_data["prev_section"] is None
        assert response.context_data["next_section"].name == "quickstart"
