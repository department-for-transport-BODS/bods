import json
import logging
from dataclasses import dataclass

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class EPAuthenticator:
    """
    Class responsible for providing Microsoft oauth2 Bearer token
    for sake of sending requests to the EP API.
    EP API requires 'Authorization' header to be added.
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
        return cache.get("ep-auth-bearer", None) or _get_token()


def _get_token() -> str:
    """
    Fetches Authorization Bearer token from MS.
    Updates cache with newly fetched auth token.

    Token cache timeout is calculated using the data received in response.

    expiry_time (to invalidate cache while the first token is still active)
    """
    logger.info("fetching ep authentication token")
    url = f"{settings.EP_AUTH_URL}"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    body = f"client_id={settings.EP_CLIENT_ID}&client_secret={settings.EP_CLIENT_SECRET}&grant_type=client_credentials"
    response = None
    try:
        response = requests.post(url=url, headers=headers, data=body)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        msg = f"Couldn't fetch Authorization token. {err}"
        logger.error(msg)
        logger.info(f"with credentials {body}")
        if response:
            logger.info(f"with content {response.content}")
        raise EPAuthorizationTokenException(msg)

    logger.info(f"EP auth url body: {body}")
    logger.info(f"EP auth url headers: {headers}")
    response = AuthResponse(**response.json())
    token_cache_timeout = response.expires_in
    cache.set("ep-auth-bearer", f"{response.access_token}", timeout=token_cache_timeout)
    auth_token = cache.get("ep-auth-bearer", None)
    logger.info(f"EP auth token from cache: {auth_token}")
    return auth_token


@dataclass(frozen=True)
class AuthResponse:
    expires_in: int
    access_token: str
    token_type: str


class EPAuthorizationTokenException(Exception):
    pass
