import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Union

from pydantic import BaseModel
from stories import Failure, Result, Success, arguments, story

from transit_odp.bods.domain import events
from transit_odp.bods.domain.entities import AgentUser, AVLPublication, Publisher
from transit_odp.bods.interfaces.notifications import INotifications
from transit_odp.bods.interfaces.unit_of_work import IUnitOfWork
from transit_odp.organisation.constants import AVLFeedStatus

logger = logging.getLogger(__name__)


@dataclass
class SendAVLFeedPublisherDownNotification:
    """
    Retrieve status of AVLFeeds and notify the publisher if their feed has gone down
    """

    def __call__(self, event):
        with self.uow:
            self.story.run(event=event)

    @story
    @arguments("event")
    def story(I):  # noqa
        I.check_status_is_down
        I.fetch_publication
        I.check_publication_exists
        I.fetch_user_email
        I.check_user_exists
        I.check_user_opt_notification
        I.notify_publisher

    # Dependencies
    notifications: INotifications
    uow: IUnitOfWork

    # Steps
    def check_status_is_down(self, ctx):
        if ctx.event.status != AVLFeedStatus.FEED_DOWN:
            return Result()
        return Success()

    def fetch_publication(self, ctx):
        ctx.publication = self.uow.publications.find(
            publication_id=ctx.event.publication_id
        )
        return Success()

    def check_publication_exists(self, ctx):
        if ctx.publication is None:
            return Failure(Errors.publication_not_found)
        return Success()

    def fetch_user_email(self, ctx):
        ctx.user = self.uow.users.find(user_id=ctx.publication.contact_user_id)
        return Success()

    def check_user_exists(self, ctx):
        if ctx.user is None:
            return Failure(Errors.contact_not_found)
        return Success()

    def check_user_opt_notification(self, ctx):
        if not ctx.user.notify_avl_unavailable:
            return Result()  # ends story
        else:
            return Success()

    def notify_publisher(self, ctx):
        self.notifications.send_avl_feed_down_publisher_notification(
            publication_id=ctx.publication.get_id(),
            dataset_name=ctx.publication.live.dataset.name,
            dataset_id=ctx.publication.live.dataset.id,
            short_description=ctx.publication.short_description,
            contact_email=ctx.user.email,
        )
        return Success()


@SendAVLFeedPublisherDownNotification.story.contract
class Context(BaseModel):
    # Arguments
    event: events.AVLFeedStatusChanged

    # State
    publication: Optional[AVLPublication]
    user: Optional[Union[Publisher, AgentUser]]


@SendAVLFeedPublisherDownNotification.story.failures
class Errors(Enum):
    publication_not_found = auto()
    contact_not_found = auto()
