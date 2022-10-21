from http import HTTPStatus
from unittest.mock import Mock, patch

from transit_odp.otc.client import OTCAuthenticator


class TestOTCAPIAuthCache:
    @patch("transit_odp.otc.client.auth.cache")
    @patch("transit_odp.otc.client.auth.requests")
    def test(self, request_mock: Mock, cache_mock: Mock) -> None:
        """
        When we call for access token for OTC API the first request
        should create entry in cache and next requests should use that
        value saved in cache instead of sending additional requests.

        Cache behaviour was mocked here.
        """
        OTCAuth = OTCAuthenticator()
        dummy_token = "dummy_token"

        mock_api_response = Mock()
        mock_api_response.status_code = HTTPStatus.OK
        mock_api_response.json.side_effect = [
            {
                "expires_in": 100,
                "access_token": dummy_token,
                "ext_expires_in": "dummy",
                "token_type": "dummy",
            },
            {
                "expires_in": 100,
                "access_token": "dummy_token_2",
                "ext_expires_in": "dummy",
                "token_type": "dummy",
            },
        ]

        mock_api_response.raise_for_status.return_value = None

        request_mock.post.return_value = mock_api_response

        cache_mock.get.side_effect = [None, dummy_token]
        cache_mock.set.return_value = None

        token = OTCAuth.token
        assert token == dummy_token
        request_mock.post.assert_called_once()
        cache_mock.get.assert_called_once()
        cache_mock.set.assert_called_once()

        token = OTCAuth.token
        assert token == dummy_token
        # Should not increment call count as value was taken from cache
        request_mock.post.assert_called_once()
        # Cache got called for value
        assert cache_mock.get.call_count == 2
        cache_mock.set.assert_called_once()
