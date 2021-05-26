import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional

from django.utils.timezone import now
from pydantic import BaseModel
from stories import Failure, Result, Success, arguments, story

from transit_odp.bods.domain import events
from transit_odp.bods.domain.entities import AVLPublication, User
from transit_odp.bods.interfaces.notifications import INotifications
from transit_odp.bods.interfaces.unit_of_work import IUnitOfWork

logger = logging.getLogger(__name__)


@dataclass
class SendAVLFeedSubscriberNotification:
    """Retrieve status of AVLFeeds and notify the subscribers"""

    def __call__(self, event):
        with self.uow:
            self.story.run(event=event)

    @story
    @arguments("event")
    def story(I):  # noqa
        I.fetch_publication
        I.check_publication_exists
        I.check_subscribers_exists
        I.fetch_subscribers
        I.fetch_org_name
        I.notify_subscribers

    # Dependencies
    notifications: INotifications
    uow: IUnitOfWork

    # Steps
    def fetch_publication(self, ctx):
        ctx.publication = self.uow.publications.find(
            publication_id=ctx.event.publication_id
        )
        return Success()

    def check_publication_exists(self, ctx):
        if ctx.publication is None:
            return Failure(Errors.publication_not_found)
        return Success()

    def check_subscribers_exists(self, ctx):
        if ctx.publication.subscribers is None:
            return Result()
        return Success()

    def fetch_subscribers(self, ctx):
        ctx.subscribers = self.uow.users.filter_users_by_mute_subscription(
            user_ids=ctx.publication.subscribers, mute_all_dataset_notifications=False
        )
        return Success()

    def fetch_org_name(self, ctx):
        ctx.org_name = self.uow.organisations.find(
            organisation_id=ctx.publication.organisation_id
        ).name
        return Success()

    def notify_subscribers(self, ctx):
        for user in ctx.subscribers:
            self.notifications.send_avl_feed_subscriber_notification(
                publication_id=ctx.publication.get_id(),
                operator_name=ctx.org_name,
                dataset_status=ctx.event.status,
                updated_time=now(),
                subscriber_email=user.email,
            )
        return Success()


@SendAVLFeedSubscriberNotification.story.contract
class Context(BaseModel):
    # Arguments
    event: events.AVLFeedStatusChanged

    # State
    publication: Optional[AVLPublication]
    subscribers: Optional[List[User]]
    org_name: Optional[str]


@SendAVLFeedSubscriberNotification.story.failures
class Errors(Enum):
    publication_not_found = auto()
