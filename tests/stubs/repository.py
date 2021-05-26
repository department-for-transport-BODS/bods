from typing import List, Optional, Union

from transit_odp.bods.domain.entities import (
    Organisation,
    Publication,
    Publisher,
    SiteAdmin,
    User,
)
from transit_odp.bods.domain.entities.identity import (
    OrganisationId,
    PublicationId,
    UserId,
)
from transit_odp.bods.interfaces.repository import (
    IOrganisationRepository,
    IPublicationRepository,
    IUserRepository,
)
from transit_odp.organisation.constants import DatasetType

UserType = Union[User, Publisher, SiteAdmin]


class FakePublicationRepository(IPublicationRepository):
    def __init__(self, publications: List[Publication]):
        self._count = 0
        self._publications = set(publications)
        self.seen = set()

    def next_identity(self) -> PublicationId:
        self._count += 1
        return PublicationId(id=self._count)

    def add(self, publication) -> None:
        self._publications.add(publication)
        self.seen.add(publication)

    def update(self, publication) -> None:
        self._publications.remove(publication)
        self._publications.add(publication)
        self.seen.add(publication)

    def find(self, publication_id):
        return next(pub for pub in self._publications if pub.id == publication_id)

    def list(
        self,
        dataset_types: Optional[List[DatasetType]] = None,
        publication_ids: Optional[List[PublicationId]] = None,
    ):
        return list(self._publications)


class FakeUserRepository(IUserRepository[UserType]):
    def __init__(self):
        self._count = 0
        self.seen = set()

    def next_identity(self) -> UserId:
        self._count += 1
        return UserId(id=self._count)

    def add(self, user: UserType) -> None:
        self.seen.add(user)

    def update(self, user: UserType) -> None:
        self.seen.add(user)

    def find(self, user_id: UserId) -> Optional[UserType]:
        return next(user for user in self.seen if user.id == user_id)

    def list(self, user_ids: Optional[List[UserId]]) -> List[UserType]:
        return list(user for user in self.seen if user.id in user_ids)

    def list_members_of_organisation(
        self, organisation_id: OrganisationId
    ) -> List[Publisher]:
        return list(
            user for user in self.seen if user.organisation_id == organisation_id
        )

    def filter_users_by_mute_subscription(
        self, user_ids: List[UserId], mute_all_dataset_notifications=None
    ) -> List[UserType]:
        return list(
            user
            for user in self.seen
            if user.mute_all_dataset_notifications == mute_all_dataset_notifications
        )


class FakeOrganisationRepository(IOrganisationRepository):
    def __init__(self):
        self._count = 0
        self.seen = set()

    def next_identity(self) -> OrganisationId:
        self._count += 1
        return OrganisationId(id=self._count)

    def add(self, organisation: Organisation) -> None:
        self.seen.add(organisation)

    def update(self, organisation: Organisation) -> None:
        self.seen.add(organisation)

    def find(self, organisation_id: OrganisationId) -> Optional[Organisation]:
        return next(org for org in self.seen if org.id == organisation_id)

    def list(self) -> List[Organisation]:
        return list(self.seen)
