from typing import NewType, Optional

from pydantic import BaseModel

from transit_odp.bods.domain.entities.identity import OrganisationId, UserId

Email = NewType("Email", str)


class User(BaseModel):
    id: UserId
    email: Email
    mute_all_dataset_notifications: Optional[bool]

    def get_id(self) -> int:
        return self.id.id

    def __eq__(self, other) -> bool:
        """Entity is identified by the value of its `Id` field."""
        return isinstance(other, self.__class__) and other.get_id() == self.get_id()

    def __hash__(self):
        return hash(self.get_id())


class Publisher(User):
    organisation_id: OrganisationId
    is_admin: bool  # has addition privileges to invite
    notify_avl_unavailable: bool


class SiteAdmin(User):
    pass


# TODO - add Invitation
# TODO - add Token
