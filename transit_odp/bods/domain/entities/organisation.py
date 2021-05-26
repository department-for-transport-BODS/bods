from typing import Optional

from pydantic import BaseModel

from transit_odp.bods.domain.entities.identity import OrganisationId, UserId


class Organisation(BaseModel):
    # TODO - will need to handle DB integrity errors in the mapper such as unique name
    id: OrganisationId
    name: str
    short_name: str
    is_active: bool
    key_contact_id: Optional[UserId]

    def get_id(self) -> int:
        return self.id.id

    def __eq__(self, other) -> bool:
        """Entity is identified by the value of its `Id` field."""
        return isinstance(other, self.__class__) and other.get_id() == self.get_id()

    def __hash__(self):
        return hash(self.get_id())
