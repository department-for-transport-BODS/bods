import json
import socket

import pytest
from django.utils.timezone import now
from mocket.mocket import Mocketizer
from mocket.plugins.httpretty import Entry

from transit_odp.avl.clients.cavl import Feed, FeedStatus
from transit_odp.bods.adapters.gateways.cavl import CAVLService


class TestCAVLService:
    def test_register_feed(self, settings):
        """
        GIVEN: feed_id: int, publisher_id: int, url: str,
               username: str, password: str
        WHEN:  calling `register_feed` with the arguments in GIVEN
               it's testing the success of the method `register_feed`
        THEN:  the boolean True return
        """
        Entry.single_register(
            Entry.POST,
            f"{settings.CAVL_URL}/feed",
            status=201,
            body=json.dumps({"id": 1}),
            headers={"content-type": "application/json"},
        )

        with Mocketizer():
            cavl_service = CAVLService()
            result = cavl_service.register_feed(
                feed_id=1,
                publisher_id=1,
                url="https://www.siri-feed.com",
                username="12345",
                password="password123",
            )

        assert result is True

    def test_register_feed_raise_exception(self, settings):
        """
        GIVEN: feed_id: int, publisher_id: int, url: str,
               username: str, password: str
        WHEN:  calling `register_feed` with the arguments in GIVEN
               it's testing the fail of the method `register_feed`,
               an exception will be raised possible exceptions are:
               ConnectionError, ConnectTimeout, RequestException
        THEN:  the boolean False return
        """
        Entry.single_register(
            Entry.POST,
            f"{settings.CAVL_URL}/feed",
            status=201,
            body=json.dumps({"id": 1}),
            headers={"content-type": "application/json"},
            exception=socket.error(),
        )

        with Mocketizer():
            cavl_service = CAVLService()
            result = cavl_service.register_feed(
                feed_id=1,
                publisher_id=1,
                url="https://www.siri-feed.com",
                username="12345",
                password="password123",
            )

        assert result is False

    def test_delete_feed(self, settings):
        """
        GIVEN: feed_id: int
        WHEN:  calling `delete_feed` with the arguments in GIVEN
               it's testing the success of the method `delete_feed`
        THEN:  return the boolean True
        """
        Entry.single_register(
            Entry.DELETE,
            f"{settings.CAVL_URL}/feed/1",
            status=204,
            headers={"content-type": "application/json"},
        )

        with Mocketizer():
            cavl_service = CAVLService()
            result = cavl_service.delete_feed(feed_id=1)

        assert result is True

    def test_delete_feed_raise_exception(self, settings):
        """
        GIVEN: feed_id: int
        WHEN:  calling `delete_feed` with the arguments in GIVEN
               it's testing the fail of the method `delete_feed`
               possible exceptions are:
               ConnectionError, ConnectTimeout, RequestException
        THEN:  return the boolean False
        """
        Entry.single_register(
            Entry.DELETE,
            f"{settings.CAVL_URL}/feed/1",
            status=204,
            headers={"content-type": "application/json"},
            exception=socket.error(),
        )

        with Mocketizer():
            cavl_service = CAVLService()
            result = cavl_service.delete_feed(feed_id=1)

        assert result is False

    def test_update_feed(self, settings):
        """
        GIVEN: feed_id: int, url: str, username: str, password: str
        WHEN:  calling `update_feed` with the argments in GIVEN
               it's testing the success of the method `update_feed`
        THEN:  return the boolean True
        """
        Entry.single_register(
            Entry.POST,
            f"{settings.CAVL_URL}/feed/1",
            status=204,
            headers={"content-type": "application/json"},
        )

        with Mocketizer():
            cavl_service = CAVLService()
            result = cavl_service.update_feed(
                feed_id=1,
                url="https://www.siri-feed.com",
                username="12345",
                password="password123",
            )

        assert result is True

    def test_update_feed_raise_exception(self, settings):
        """
        GIVEN: feed_id: int, url: str, username: str,
               password: str
        WHEN:  calling `update_feed` with the arguments
               it's testing the fail of the method,
               possible exceptions are:
               ConnectionError, ConnectTimeout, RequestException
        THEN:  return the boolean False
        """
        Entry.single_register(
            Entry.POST,
            f"{settings.CAVL_URL}/feed/1",
            status=204,
            headers={"content-type": "application/json"},
            exception=socket.error(),
        )

        with Mocketizer():
            cavl_service = CAVLService()
            result = cavl_service.update_feed(
                feed_id=1,
                url="https://www.siri-feed.com",
                username="12345",
                password="password123",
            )

        assert result is False

    def test_get_feed(self, settings):
        """
        GIVEN: feed_id: int
        WHEN:  calling `get_feed` with the arguments in GIVEN
               it's testing the success of the method
        THEN:  return the corresponding Feed object
        """
        Entry.single_register(
            Entry.GET,
            f"{settings.CAVL_URL}/feed/1",
            body=json.dumps(
                {
                    "id": 1,
                    "publisherId": 1,
                    "url": "https://www.siri-feed.com",
                    "username": "12345",
                    "password": None,
                    "status": "FEED_UP",
                    "created": None,
                    "modified": None,
                }
            ),
            headers={"content-type": "application/json"},
        )

        with Mocketizer():
            cavl_service = CAVLService()
            result = cavl_service.get_feed(feed_id=1)

        assert result == Feed(
            id=1,
            publisherId=1,
            url="https://www.siri-feed.com",
            username="12345",
            password=None,
            status=FeedStatus.FEED_UP,
        )

    def test_get_feed_raise_exception(self, settings):
        """
        GIVEN: feed_id: int
        WHEN:  calling `get_feed` with the arguments in GIVEN
               it's testing the fail of the method
               possible exceptions are:
               ConnectionError, ConnectTimeout, RequestException
        THEN:  an exception will be raised
        """
        Entry.single_register(
            Entry.GET,
            f"{settings.CAVL_URL}/feed/1",
            body=json.dumps(
                [
                    {
                        "id": 1,
                        "publisherId": 1,
                        "url": "https://www.siri-feed.com",
                        "username": "12345",
                        "password": None,
                        "status": "FEED_UP",
                        "created": None,
                        "modified": None,
                    }
                ]
            ),
            headers={"content-type": "application/json"},
            exception=socket.error(),
        )

        with Mocketizer():
            cavl_service = CAVLService()
            result = cavl_service.get_feed(feed_id=1)
            assert result is None

    def test_get_feeds(self, settings):
        """
        WHEN: calling the method `get_feeds()`
              it's testing the success of the method
        THEN: return a list of objects Feed
        """
        Entry.single_register(
            Entry.GET,
            f"{settings.CAVL_URL}/feed",
            body=json.dumps(
                [
                    {
                        "id": 1,
                        "publisherId": 1,
                        "url": "https://www.siri-feed.com",
                        "username": "12345",
                        "password": None,
                        "status": "FEED_UP",
                        "created": None,
                        "modified": None,
                    }
                ]
            ),
            headers={"content-type": "application/json"},
        )

        with Mocketizer():
            cavl_service = CAVLService()
            result = cavl_service.get_feeds()

        assert len(result) == 1
        assert result[0] == Feed(
            id=1,
            publisherId=1,
            url="https://www.siri-feed.com",
            username="12345",
            password=None,
            status=FeedStatus.FEED_UP,
        )

    def test_get_feeds_raise_exception(self, settings):
        """
        WHEN: calling the method `get_feeds()`
              it's testing the fail of the method
              possible exceptions are:
              ConnectionError, ConnectTimeout, RequestException
        THEN: None is returned
        """
        Entry.single_register(
            Entry.GET,
            f"{settings.CAVL_URL}/feed",
            body=json.dumps(
                [
                    {
                        "id": 1,
                        "publisherId": 1,
                        "url": "https://www.siri-feed.com",
                        "username": "12345",
                        "password": None,
                        "status": "FEED_UP",
                        "created": None,
                        "modified": None,
                    }
                ]
            ),
            headers={"content-type": "application/json"},
            exception=socket.error(),
        )

        with Mocketizer():
            cavl_service = CAVLService()
            assert cavl_service.get_feeds() == []

    def test_validate_feed(self, settings):
        """
        GIVEN: url: str, username: str, password: str
        WHEN:  calling `validate_feed` with the arguments
               it's testing the success of the method
        THEN:  an object ValidationTaskResult is returned
        """
        dt = now()
        Entry.single_register(
            Entry.POST,
            f"{settings.CAVL_URL}/validate",
            body=json.dumps(
                {
                    "url": "https://www.siri-feed.com",
                    "username": "12345",
                    "status": "DEPLOYING",
                    "created": str(dt),
                }
            ),
            headers={"content-type": "application/json"},
        )

        with Mocketizer():
            cavl_service = CAVLService()
            result = cavl_service.validate_feed(
                url="https://www.siri-feed.com",
                username="12345",
                password="password123",
            )

        assert result.status == "DEPLOYING"

    def test_validate_feed_raise_exception(self, settings):
        """
        GIVEN: url: str, username: str, password: str
        WHEN:  calling `validate_feed` with the arguments
               it's testing the fail of the method
        THEN:  None is returned
        """
        dt = now()
        Entry.single_register(
            Entry.POST,
            f"{settings.CAVL_URL}/validate",
            body=json.dumps(
                {
                    "url": "https://www.siri-feed.com",
                    "username": "12345",
                    "status": "DEPLOYING",
                    "created": str(dt),
                }
            ),
            headers={"content-type": "application/json"},
            exception=socket.error(),
        )

        with Mocketizer():
            with pytest.raises(Exception):
                cavl_service = CAVLService()
                cavl_service.validate_feed(
                    url="https://www.siri-feed.com",
                    username="12345",
                    password="password123",
                )
