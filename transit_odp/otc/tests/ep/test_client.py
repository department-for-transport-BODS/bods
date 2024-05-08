import pytest
from unittest.mock import patch, Mock
from requests.exceptions import Timeout, HTTPError
from transit_odp.otc.ep.client import EPClient, APIResponse


class TestEPClient:
    @pytest.fixture
    def client(self):
        return EPClient()

    @pytest.fixture
    def mock_get(self, monkeypatch):
        mock = Mock()
        monkeypatch.setattr("requests.get", mock)
        return mock

    @patch.object(EPClient, "_make_request")
    def test_fetch_ep_services(self, mock_make_request, get_ep_data):
        # setup
        mock_make_request.return_value = get_ep_data
        client = EPClient()

        # test
        response = client.fetch_ep_services()

        # Assert
        mock_make_request.assert_called_once()
        assert response == APIResponse(**get_ep_data)

    @patch("transit_odp.otc.ep.client.requests.get")
    @patch("transit_odp.otc.ep.client.EPAuthenticator")
    def test_make_request(self, mock_auth, mock_get, get_ep_data):
        # Arrange
        mock_auth.return_value.token = "test_token"
        dummy_response = get_ep_data
        mock_get.return_value.json.return_value = dummy_response
        mock_get.return_value.status_code = 200
        client = EPClient()

        # Act
        response = client._make_request()

        # Assert
        mock_get.assert_called_once()
        assert response == APIResponse(**dummy_response)

    @patch("transit_odp.otc.ep.client.requests.get")
    @patch("transit_odp.otc.ep.client.EPAuthenticator")
    def test_make_request_timeout(self, mock_auth, mock_get):
        # setup
        mock_auth.return_value.token = "test_token"
        mock_get.side_effect = Timeout("Request timed out")
        client = EPClient()

        # test
        with pytest.raises(Timeout):
            client._make_request()

    @patch("transit_odp.otc.ep.client.requests.get")
    @patch("transit_odp.otc.ep.client.EPAuthenticator")
    def test_make_request_http_error(self, mock_auth, mock_get):
        # setup
        mock_auth.return_value.token = "test_token"
        mock_get.side_effect = HTTPError("HTTP Error occurred")
        client = EPClient()

        # Act and Assert
        with pytest.raises(HTTPError):
            client._make_request()
