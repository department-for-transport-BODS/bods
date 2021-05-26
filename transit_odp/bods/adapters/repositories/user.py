from typing import List, Optional, Union

from django.db import connection

from transit_odp.bods.adapters.mappers import user as mappers
from transit_odp.bods.domain.entities import Publisher, SiteAdmin, User
from transit_odp.bods.domain.entities.identity import OrganisationId, UserId
from transit_odp.bods.interfaces.repository import IUserRepository

UserType = Union[User, Publisher, SiteAdmin]


# NOTE
# functions modifying the data should not return anything
# functions retrieving the data should not modify anything


class UserRepository(IUserRepository[UserType]):
    def next_identity(self) -> UserId:
        cursor = connection.cursor()
        cursor.execute("select nextval('users_user_id_seq')")
        result = cursor.fetchone()[0]
        return UserId(id=result)

    def add(self, user: UserType) -> None:
        mappers.add_user(user)

    def update(self, user: UserType) -> None:
        # TODO - implement update
        pass

    def find(self, user_id: UserId) -> Optional[UserType]:
        users = self.list(user_ids=[user_id])
        return users[0] if len(users) else None

    def list(self, user_ids: Optional[List[UserId]] = None) -> List[UserType]:
        return list(mappers.load_users(user_ids))

    def list_members_of_organisation(
        self, organisation_id: OrganisationId
    ) -> List[Publisher]:
        return list(mappers.load_users(organisation_id=organisation_id))

    def filter_users_by_mute_subscription(
        self, user_ids: List[UserId], mute_all_dataset_notifications=None
    ) -> List[UserType]:
        return list(
            mappers.load_users(
                user_ids=user_ids,
                mute_all_dataset_notifications=mute_all_dataset_notifications,
            )
        )
