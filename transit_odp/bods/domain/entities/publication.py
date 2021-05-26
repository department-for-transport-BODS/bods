import datetime
from typing import ClassVar, Generic, List, Optional, TypeVar

from django.utils.timezone import now
from pydantic import BaseModel
from pydantic.generics import GenericModel

from transit_odp.bods.domain import events
from transit_odp.bods.domain.entities.identity import PublicationId, UserId
from transit_odp.organisation.constants import AVLFeedStatus, DatasetType

from .organisation import OrganisationId

T = TypeVar("T", bound="Dataset")


class Revision(GenericModel, Generic[T]):
    created_at: datetime.datetime
    published_at: Optional[datetime.datetime]
    published_by: Optional[UserId]
    dataset: T

    # TODO - add hash key to handle optimistic currency control (users
    # shouldn't be able to edit the same

    has_error: bool  # TODO - model state properly

    @property
    def is_published(self) -> bool:
        return self.published_at is not None

    def can_edit(self):
        return self.is_published is False


class Publication(GenericModel, Generic[T]):
    type: ClassVar[DatasetType]
    id: PublicationId
    organisation_id: OrganisationId
    contact_user_id: UserId
    subscribers: Optional[List[UserId]]
    live: Optional[Revision[T]]
    draft: Optional[Revision[T]]
    events: List[events.Event]

    # save(dataset: T) -- assigns revision to `draft`
    # publish(user_id) -- assuming valid, assign `draft` to `live` and
    # append to `revisions`
    # delete_draft()
    # archive()

    # Invariants
    # * Publication must have either draft or live Revision to be saved
    # * `live` and `revisions` list must be immutable
    # * writes should be to `draft` only
    # * Cannot save Revision if `last_saved` is older than DB value
    #    i.e. last_saved timestamp can be used for optimistic concurrency control
    # * Cannot publish draft if `Revision.created` is older than DB value

    def get_id(self):
        return self.id.id

    def __eq__(self, other) -> bool:
        """Entity is identified by the value of its `Id` field."""
        return isinstance(other, self.__class__) and other.get_id() == self.get_id()

    def __hash__(self):
        return hash(self.get_id())


class Dataset(BaseModel):
    name: str
    description: str
    short_description: str
    comment: str


# see https://github.com/samuelcolvin/pydantic/issues/704
Revision[T].update_forward_refs()


class AVLDataset(Dataset):
    url: str
    username: str
    password: str
    requestor_ref: str
    id: Optional[int]


class AVLPublication(Publication[AVLDataset]):
    type: ClassVar[DatasetType] = DatasetType.AVL
    feed_status: AVLFeedStatus = AVLFeedStatus.DEPLOYING
    feed_last_checked: Optional[datetime.datetime] = None
    subscribers: Optional[List[UserId]]

    def update_feed_status(self, status: AVLFeedStatus) -> None:
        self.feed_last_checked = now()  # TODO - should use service to get time
        if self.feed_status != status:
            self.feed_status = status
            self.events.append(
                events.AVLFeedStatusChanged(publication_id=self.id, status=status)
            )


class TimetableReport(BaseModel):
    transxchange_version: str
    num_of_operators: Optional[int]  # TODO - check why this is optional
    num_of_lines: Optional[int]
    num_of_bus_stops: Optional[int]
    admin_areas: List[str]
    localities: List[str]
    publisher_creation_datetime: Optional[datetime.datetime]
    publisher_modified_datetime: Optional[datetime.datetime]
    first_expiring_service: Optional[datetime.datetime]
    last_expiring_service: Optional[datetime.datetime]
    first_service_start: Optional[datetime.datetime]


class TimetableDataset(Dataset):
    url: Optional[str]
    filename: Optional[str]
    has_expired: bool
    report: Optional[TimetableReport]


class TimetablePublication(Publication[TimetableDataset]):
    type: ClassVar[DatasetType] = DatasetType.TIMETABLE
    server_available: Optional[bool]


class FaresDataset(Dataset):
    url: Optional[str]
    filename: Optional[str]
    has_expired: bool


class FaresPublication(Publication[FaresDataset]):
    type: ClassVar[DatasetType] = DatasetType.FARES
    server_available: Optional[bool]
