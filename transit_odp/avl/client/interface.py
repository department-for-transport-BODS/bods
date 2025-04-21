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
        description: str,
        short_description: str,
    ) -> bool:
        """
        Registers a feed in the AVL service.
        Args:
            feed_id: Datafeed ID for subscription
            publisher_id: Organisation ID that manages the subscription
            url: The data producers endpoint
            username: The data producers username
            password: The data producers password
            description: Description of the data feed (entered by user)
            short_description: Short description of the data feed (entered by user)

        Returns: Boolean indicating the feed was added successfully
        """
        ...

    def delete_feed(self, feed_id: int) -> bool:
        """
        Deletes the feed registered in CAVL by the ID
        Args:
            feed_id:

        Returns: Boolean indicating the feed was deleted successfully
        """
        ...

    def update_feed(
        self,
        feed_id: int,
        url: str,
        username: str,
        password: str,
        description: str,
        short_description: str,
    ) -> bool:
        """
        Updates an existing feed in the CAVL service.
        Args:
            feed_id: Datafeed ID for subscription
            url: The data producers endpoint
            username: The data producers username
            password: The data producers password
            description: Description of the data feed (entered by user)
            short_description: Short description of the data feed (entered by user)

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


class ICAVLSubscriptionService(Protocol):
    def subscribe(
        self,
        api_key: str,
        name: str,
        url: str,
        update_interval: int,
        subscription_id: str,
        dataset_ids: str,
        bounding_box: str,
        operator_ref: str,
        vehicle_ref: str,
        line_ref: str,
        producer_ref: str,
        origin_ref: str,
        destination_ref: str,
    ) -> None:
        """
        Creates a subscription in the AVL consumer subscription service.
        Args:
            api_key: The BODS user API key
            name: User-friendly name for the subscription
            url: The endpoint that AVL subscription data will be sent to
            update_interval: The update interval for data being sent
            subscription_id: An ID for the subscription
            dataset_ids: The dataset ID(s) to subscribe to, concatenated into a string
            bounding_box: Optional bounding box coordinates data filter
            operator_ref: Optional operator ref data filter
            vehicle_ref: Optional vehicle ref data filter
            line_ref: Optional line ref data filter
            producer_ref: Optional producer ref data filter
            origin_ref: Optional origin ref data filter
            destination_ref: Optional destination ref data filter

        Returns: Boolean indicating the subscription was created successfully
        """
        ...

    def unsubscribe(
        self,
        api_key: str,
        subscription_id: str,
    ) -> None:
        """
        Unsubscribes a subscription in the AVL consumer subscription service.
        Args:
            api_key: The BODS user API key
            subscription_id: An ID for the subscription

        Returns: Boolean indicating the subscription was unsubscribed successfully
        """
        ...

    def get_subscriptions(self, api_key: str) -> Sequence[dict]:
        """
        Retrieves the consumer subscriptions with the given api_key
        Args:
            api_key: The BODS user API key

        Returns: A collection of dict objects
        """
        ...

    def get_subscription(self, api_key: str, subscription_id: int) -> dict:
        """
        Retrieves the consumer subscription with the given api_key and subscription_id
        Args:
            api_key: The BODS user API key
            subscription_id: The ID of the subscription

        Returns: A dict object given by `subscription_id`
        """
        ...
