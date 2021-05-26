from datetime import datetime
from typing import Dict, Sequence, Set

from cavl_client import ValidationTaskResult

from transit_odp.bods.interfaces.gateways import (
    VALIDATION_TASK_STATUS,
    AVLFeed,
    ICAVLService,
)
from transit_odp.organisation.constants import AVLFeedStatus


class FakeCAVLService(ICAVLService):
    def __init__(self, feeds=None):
        self.feeds: Set[AVLFeed] = set(feeds or [])

    def register_feed(
        self, feed_id: int, publisher_id: int, url: str, username: str, password: str
    ) -> bool:
        self.feeds.add(
            AVLFeed(
                id=feed_id,
                publisher_id=publisher_id,
                url=url,
                username=username,
                password=password,
                status=AVLFeedStatus.FEED_UP,
            )
        )
        return True

    def delete_feed(self, feed_id: int) -> bool:
        self.feeds = set(feed for feed in self.feeds if feed.id != feed_id)
        return True

    def update_feed(self, feed_id: int, url: str, username: str, password: str) -> bool:
        feed = self.get_feed(feed_id)
        if not feed:
            return False
        self.delete_feed(feed_id)
        self.register_feed(
            feed_id=feed_id,
            url=url,
            username=username,
            password=password,
            publisher_id=feed.publisher_id or 0,  # awkward
        )
        return True

    def get_feed(self, feed_id: int) -> AVLFeed:
        return next(feed for feed in self.feeds if feed.id == feed_id)

    def get_feeds(self) -> Sequence[AVLFeed]:
        return list(self.feeds)

    def validate_feed(
        self, url: str, username: str, password: str
    ) -> ValidationTaskResult:
        return ValidationTaskResult(
            url=url,
            username=username,
            password=password,
            status="FEED_VALID",
            created=datetime.utcnow(),
        )

    def _set_feed_status(self, feed_id: int, status: AVLFeedStatus):
        feed = self.get_feed(feed_id)
        feed.status = status
