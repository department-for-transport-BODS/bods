import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from pydantic import BaseModel
from stories import Failure, Success, arguments, story

from transit_odp.bods.domain import commands
from transit_odp.bods.domain.entities import Organisation, Publication, Publisher, User
from transit_odp.bods.interfaces.notifications import INotifications
from transit_odp.bods.interfaces.unit_of_work import IUnitOfWork

logger = logging.getLogger(__name__)


@dataclass
class SendFeedback:
    """Send feedback from the Consumer to the Publisher"""

    def __call__(self, command):
        with self.uow:
            result = self.story.run(command=command)
            if result.is_success:
                self.uow.commit()

    @story
    @arguments("command")
    def story(I):  # noqa
        I.fetch_publication
        I.check_publication_exists
        I.fetch_organisation
        I.check_organisation_exists_and_is_active
        I.fetch_sender
        I.get_sender_email
        I.fetch_recipient
        I.check_recipient_exists
        I.send_notification

    # Dependencies
    uow: IUnitOfWork
    notifications: INotifications

    def fetch_publication(self, ctx):
        ctx.publication = self.uow.publications.find(
            publication_id=ctx.command.publication_id
        )
        return Success()

    def check_publication_exists(self, ctx):
        if ctx.publication is None:
            return Failure(Errors.publication_not_found)
        return Success()

    def fetch_organisation(self, ctx):
        ctx.organisation = self.uow.organisations.find(
            organisation_id=ctx.publication.organisation_id
        )
        return Success()

    def check_organisation_exists_and_is_active(self, ctx):
        if ctx.organisation is None:
            return Failure(Errors.organisation_not_found)
        elif not ctx.organisation.is_active:
            return Failure(Errors.organisation_is_inactive)
        return Success()

    def fetch_sender(self, ctx):
        ctx.sender = self.uow.users.find(user_id=ctx.command.sender_id)
        return Success()

    def get_sender_email(self, ctx):
        if ctx.command.anonymous:
            ctx.sender_email = None
        elif ctx.sender:
            ctx.sender_email = ctx.sender.email
        else:
            return Failure(Errors.sender_not_found)
        return Success()

    def fetch_recipient(self, ctx):
        ctx.recipient = self.uow.users.find(user_id=ctx.publication.contact_user_id)
        return Success()

    def check_recipient_exists(self, ctx):
        if ctx.recipient is None:
            return Failure(Errors.recipient_not_found)
        return Success()

    def send_notification(self, ctx):
        self.notifications.send_feedback_notification(
            publication_id=ctx.publication.get_id(),
            contact_email=ctx.recipient.email,
            dataset_name=ctx.publication.live.dataset.name,
            feedback=ctx.command.feedback,
            developer_email=ctx.sender_email,
        )
        return Success()


@SendFeedback.story.contract
class Context(BaseModel):
    # Arguments
    command: commands.SendFeedback

    # State
    publication: Publication
    organisation: Optional[Organisation]
    sender: User
    sender_email: Optional[str]
    recipient: Publisher


@SendFeedback.story.failures
class Errors(Enum):
    publication_not_found = auto()
    organisation_not_found = auto()
    organisation_is_inactive = auto()
    sender_not_found = auto()
    recipient_not_found = auto()
