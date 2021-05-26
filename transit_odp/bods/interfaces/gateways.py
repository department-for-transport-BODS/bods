from typing import Literal, Optional, Protocol, Sequence

from cavl_client.models import ValidationTaskResult
from pydantic import BaseModel

# TODO - make this part of the domain
from transit_odp.organisation.constants import AVLFeedStatus

VALIDATION_TASK_STATUS = Literal[
    "DEPLOYING", "SYSTEM_ERROR", "FEED_VALID", "FEED_INVALID"
]


class AVLFeed(BaseModel):
    id: int
    publisher_id: int
    url: str
    username: str
    password: Optional[str] = None
    status: Optional[AVLFeedStatus] = None

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other) -> bool:
        return isinstance(other, self.__class__) and other.id == self.id


class ICAVLService(Protocol):
    """
    Gateway service to the CAVL service

    See [Gateway](https://martinfowler.com/eaaCatalog/gateway.html) pattern
    """

    def register_feed(
        self,
        feed_id: int,
        publisher_id: int,
        url: str,
        username: str,
        password: str,
    ) -> bool:
        """
        Registers a feed in the CAVL service.
        Args:
            feed_id:
            publisher_id:
            url:
            username:
            password:

        Returns: Boolean indicating the feed was added successfully.
        TODO - may need to refactor this later allow better handling, e.g. if feed_id is
        already registered violating uniqueness. I didn't want exception classes from
        the cavl_client lib, e.g. ApiException, to be leaked into the client code of
        the service

        However, on that point, how to handle errors such a 'feed_id already exists',
        etc.
        """
        ...

    def delete_feed(self, feed_id: int) -> bool:
        ...

    def update_feed(self, feed_id: int, url: str, username: str, password: str) -> bool:
        """
        Updates an existing feed in the CAVL service.
        Args:
            feed_id:
            url:
            username:
            password:

        Returns:
        """
        ...

    def get_feed(self, feed_id: int) -> AVLFeed:
        """
        Retrieves the feed registered in CAVL by the ID
        Args:
            feed_id:

        Returns: A AVLFeed object given by `feed_id`
        """
        ...

    def get_feeds(self) -> Sequence[AVLFeed]:
        """
        Retrieves the list of feeds registered in CAVL
        Returns: A collection of AVLFeed objects
        """
        ...

    def validate_feed(
        self,
        url: str,
        username: str,
        password: str,
    ) -> ValidationTaskResult:
        """
        Creates a task to validate the AVL data feed
        Args:
            url: The URL to the AVL data feed (required)
            username: The username to authenticate access to the AVL feed (required)
            password: The password to authenticate access to the AVL feed (required)

        Returns: A ValidationTaskResult containing the status of the validation
        """
        ...
