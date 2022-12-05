from typing import Protocol, Sequence

from transit_odp.avl.dataclasses import Feed, ValidationTaskResult


class ICAVLService(Protocol):
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

    def get_feed(self, feed_id: int) -> Feed:
        """
        Retrieves the feed registered in CAVL by the ID
        Args:
            feed_id:

        Returns: A Feed object given by `feed_id`
        """
        ...

    def get_feeds(self) -> Sequence[Feed]:
        """
        Retrieves the list of feeds registered in CAVL
        Returns: A collection of Feed objects
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
