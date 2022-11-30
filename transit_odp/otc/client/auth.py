import logging
from dataclasses import dataclass

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class OTCAuthenticator:
    """
    Class responsible for providing Microsoft oauth2 Bearer token
    for sake of sending requests to the OTC API.
    OTC API requires 'Authorization' header to be added.
    {
        ...,
        "Authorization": <token>
    }
    """

    @property
    def token(self) -> str:
        """
        Fetch bearer token from Cache (Redis) or send request to generate new token.
        """
        return cache.get("otc-auth-bearer", None) or _get_token()


def _get_token() -> str:
    """
    Fetches Authorization Bearer token from MS.
    Updates cache with newly fetched auth token.

    Token cache timeout is calculated using the data received in response.

    expiry_time - 5mins (to invalidate cache while the first token is still active)
    """
    url = f"{settings.MS_LOGIN_URL}/{settings.MS_TENANT_ID}/oauth2/v2.0/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    body = {
        "client_secret": settings.OTC_CLIENT_SECRET,
        "client_id": settings.MS_CLIENT_ID,
        "scope": settings.MS_SCOPE,
        "grant_type": "client_credentials",
    }

    try:
        response = requests.post(url=url, headers=headers, data=body)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        msg = f"Couldn't fetch Authorization token. {err}"
        logger.error(msg)
        raise OTCAuthorizationTokenException(msg)

    response = AuthResponse(**response.json())
    token_cache_timeout = response.expires_in - 60 * 5
    cache.set("otc-auth-bearer", response.access_token, timeout=token_cache_timeout)
    return response.access_token


@dataclass(frozen=True)
class AuthResponse:
    expires_in: int
    access_token: str
    token_type: str
    ext_expires_in: int


class OTCAuthorizationTokenException(Exception):
    pass
