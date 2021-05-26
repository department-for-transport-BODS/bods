import json

from django.utils.timezone import now
from mocket import Mocketizer
from mocket.plugins.httpretty import Entry

from transit_odp.bods.adapters.gateways.cavl import CAVLService
from transit_odp.bods.interfaces.gateways import AVLFeed
from transit_odp.organisation.constants import AVLFeedStatus

# TODO - make this a proper integration test


class TestCAVLService:
    MUT = "transit_odp.bods.adapters.gateways.cavl"

    def test_can_register_feed(self, settings):
        """Tests a feed is created"""
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

        assert result == 1

    def test_can_delete_feed(self, settings):
        """Tests feed is deleted"""
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

    def test_update_feed(self, settings):
        """Tests a feed is updated"""
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

    def test_can_get_feeds(self, settings):
        """Tests a list of feeds is returned"""
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
        assert result[0] == AVLFeed(
            id=1,
            publisher_id=1,
            url="https://www.siri-feed.com",
            username="12345",
            password=None,
            status=AVLFeedStatus.FEED_UP,
        )

    def test_can_validate_feed(self, settings):
        """Tests a feed is validated"""
        dt = now()
        Entry.single_register(
            Entry.POST,
            f"{settings.CAVL_URL}/validate",
            body=json.dumps(
                [
                    {
                        "url": "https://www.siri-feed.com",
                        "username": "12345",
                        "status": "DEPLOYING",
                        "created": str(dt),
                    }
                ]
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
