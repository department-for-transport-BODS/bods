from pydantic import BaseModel

from transit_odp.bods.domain.entities.identity import PublicationId, UserId


class Command(BaseModel):
    pass


class MonitorAVLFeeds(Command):
    pass


class SendFeedback(Command):
    sender_id: UserId
    publication_id: PublicationId
    feedback: str
    anonymous: bool
