from pydantic import BaseModel

from transit_odp.bods.domain.entities.identity import PublicationId
from transit_odp.organisation.constants import AVLFeedStatus


class Event(BaseModel):
    pass


class AVLFeedStatusChanged(Event):
    # TODO - make AVLFeed its own entity
    publication_id: PublicationId  # TODO - should use identity class
    status: AVLFeedStatus
