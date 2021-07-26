import json
import logging
from typing import List, Sequence

import cavl_client
import pydantic
from cavl_client import ValidationTaskResult
from cavl_client.rest import ApiException
from django.conf import settings

from transit_odp.bods.interfaces.gateways import AVLFeed, ICAVLService
from transit_odp.organisation.constants import AVLFeedStatus

logger = logging.getLogger(__name__)


class CAVLService(ICAVLService):
    def register_feed(
        self,
        feed_id: int,
        publisher_id: int,
        url: str,
        username: str,
        password: str,
    ) -> bool:
        configuration = self._get_configuration()
        api_instance = self._get_feed_api(configuration)

        body = cavl_client.Feed(
            id=feed_id,
            publisher_id=publisher_id,
            url=url,
            username=username,
            password=password,
            # Ensure these read-only types are set to none to prevent errors
            status=None,
            created=None,
            modified=None,
        )  # Feed | Feed object that needs to be added to the consumer config

        try:
            # Adds a new feed
            api_instance.add_feed(body)
        except (ApiException, Exception):
            logger.exception("Exception when calling FeedApi->add_feed")
            # return False
            raise

        return True

    def delete_feed(self, feed_id: int):
        """

        Args:
            feed_id: int | The ID of the feed to delete

        Returns: True if deleted successfully

        """
        configuration = self._get_configuration()
        api_instance = self._get_feed_api(configuration)

        try:
            # Deletes the feed with the specified ID
            api_instance.delete_feed(feed_id)
        except (ApiException, Exception):
            logger.exception("Exception when calling FeedApi->delete_feed")
            raise

        return True

    def get_feed(self, feed_id) -> AVLFeed:
        pass

    def get_feeds(self) -> Sequence[AVLFeed]:
        configuration = self._get_configuration()
        api_instance = self._get_feed_api(configuration)

        try:
            # Gets a list of feeds
            api_response: List[cavl_client.Feed] = api_instance.get_feeds()
            return list(self._parse_avl_feeds(api_response))
        except (ApiException, Exception):
            logger.exception("Exception when calling FeedApi->get_feeds")
            raise

    def update_feed(self, feed_id: int, url: str, username: str, password: str):
        configuration = self._get_configuration()
        api_instance = self._get_feed_api(configuration)

        body = {"url": url, "username": username, "password": password}

        try:
            # Updates an existing feed with the specified ID with form data
            api_instance.update_feed_with_form(feed_id, body=body)
        except (ApiException, Exception):
            logger.exception("Exception when calling FeedApi->update_feed_with_form")
            raise

        return True

    def validate_feed(
        self, url: str, username: str, password: str, **kwargs
    ) -> ValidationTaskResult:
        configuration = self._get_configuration()
        api_instance = self._get_validate_api(configuration)

        # ValidationTaskResult object is used in both the request and the response
        body = cavl_client.ValidationTaskResult(
            url=url,
            username=username,
            password=password,
            # Ensure these read-only types are set to none to prevent errors
            status=None,
            created=None,
        )

        try:
            api_response = api_instance.validate_feed(body, **kwargs)
            return api_response
        except (ApiException, Exception):
            logger.exception("Exception when calling ValidateApi->validate_feed")
            raise

    @staticmethod
    def _get_configuration():
        # create client config
        configuration = cavl_client.Configuration()

        # Set host url with CAVL_URL configuration setting
        configuration.host = settings.CAVL_URL
        configuration.proxy = settings.HTTPS_PROXY
        return configuration

    @staticmethod
    def _get_feed_api(configuration):
        return cavl_client.FeedApi(cavl_client.ApiClient(configuration))

    @staticmethod
    def _get_validate_api(configuration):
        return cavl_client.ValidateApi(cavl_client.ApiClient(configuration))

    def _parse_avl_feeds(self, feeds):
        for feed in feeds:
            try:
                yield AVLFeed(
                    id=feed.id,
                    publisher_id=feed.publisher_id,
                    url=feed.url,
                    username=feed.username,
                    password=feed.password,
                    # Note - this assumes the API response adheres to the Swagger spec
                    status=AVLFeedStatus[feed.status],
                )
            except pydantic.ValidationError:
                # Ignore any malformed responses
                logger.exception(
                    f"Could not parse cavl_client.Feed: {json.dumps(feed.to_dict())}"
                )
                pass
