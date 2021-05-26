from typing import List, Optional, Protocol, Set, TypeVar, runtime_checkable

from transit_odp.bods.domain.entities import (
    Dataset,
    Organisation,
    Publication,
    Publisher,
    Revision,
    User,
)
from transit_odp.bods.domain.entities.identity import (
    OrganisationId,
    PublicationId,
    UserId,
)
from transit_odp.organisation.constants import DatasetType

P = TypeVar("P", bound=Publication)
D = TypeVar("D", bound=Dataset)


@runtime_checkable
class IPublicationRepository(Protocol[P, D]):
    seen: Set[P]

    def next_identity(self) -> PublicationId:
        """Generates the identity for the next Publication"""
        ...

    def add(self, publication: P) -> None:
        """Adds publication to the repository"""
        ...

    def update(self, publication: P) -> None:
        ...

    def find(self, publication_id: PublicationId) -> Optional[P]:
        ...

    def list(
        self,
        dataset_types: Optional[List[DatasetType]] = None,
        publication_ids: Optional[List[PublicationId]] = None,
    ) -> List[P]:
        ...

    def get_revision_history(
        self,
        publication_id: PublicationId,
        page_num: int = 1,
        page_size: int = 10,
    ) -> List[Revision[D]]:
        ...


class IAVLRepository(IPublicationRepository, Protocol):
    ...


class ITimetableRepository(IPublicationRepository, Protocol):
    ...


class IFaresRepository(IPublicationRepository, Protocol):
    ...


U = TypeVar("U", bound=User)


@runtime_checkable
class IUserRepository(Protocol[U]):
    seen: Set[U]

    def next_identity(self) -> UserId:
        """Generates the identity for the next User"""
        ...

    def add(self, user: U) -> None:
        """Adds user to the repository"""
        ...

    def update(self, user: U) -> None:
        """Updates user in the repository"""
        ...

    def find(self, user_id: UserId) -> Optional[U]:
        """Retrieves user from the repository"""
        ...

    def list(self, user_ids: Optional[List[UserId]]) -> List[U]:
        """Retrieves users from the repository"""
        ...

    def list_members_of_organisation(
        self, organisation_id: OrganisationId
    ) -> List[Publisher]:
        """Retrieves users belonging to Organisation from the repository"""
        ...

    def filter_users_by_mute_subscription(
        self, user_ids: List[UserId], mute_all_dataset_notifications=None
    ) -> List[U]:
        """Retrieves users who have subscribed to notifications"""
        ...


@runtime_checkable
class IOrganisationRepository(Protocol):
    seen: Set[Organisation]

    def next_identity(self) -> OrganisationId:
        """Generates the identity for the next Organisation"""
        ...

    def add(self, organisation: Organisation) -> None:
        """Adds an organisation to the repository"""
        ...

    def update(self, organisation: Organisation) -> None:
        """Updates an organisation in the repository"""
        ...

    def find(self, organisation_id: OrganisationId) -> Optional[Organisation]:
        """Retrieves an organisation from the repository"""
        ...

    def list(self) -> List[Organisation]:
        """Retrieves a list of organisations from the repository"""
        ...
