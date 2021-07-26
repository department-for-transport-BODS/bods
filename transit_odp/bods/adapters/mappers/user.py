from typing import Iterable, List, Optional, Union

from transit_odp.bods.domain.entities import Publisher, SiteAdmin, User
from transit_odp.bods.domain.entities.identity import OrganisationId, UserId
from transit_odp.bods.domain.entities.user import AgentUser, Email
from transit_odp.users import models
from transit_odp.users.constants import AccountType

UserType = Union[User, Publisher, SiteAdmin]


def load_users(
    user_ids: Optional[List[UserId]] = None,
    organisation_id: Optional[OrganisationId] = None,
    mute_all_dataset_notifications: Optional[bool] = None,
) -> Iterable[UserType]:
    """
    Loads User domain entities from the database
    Returns: A polymorphic list of User domain entities
    """
    records = models.User.objects.all()

    if user_ids is not None:
        records = records.filter(id__in=[identity.id for identity in user_ids])

    if organisation_id is not None:
        records = records.filter(organisations=organisation_id.id)

    if mute_all_dataset_notifications is not None:
        records = records.filter(
            settings__mute_all_dataset_notifications=mute_all_dataset_notifications
        )

    for record in records:
        yield map_orm_to_model(record)


def map_orm_to_model(record: models.User) -> UserType:
    """
    Maps the User model into a specific subtype of User
    """
    mute_all_dataset_notifications = record.settings.mute_all_dataset_notifications
    if record.is_agent_user:
        organisation_ids = [
            OrganisationId(id=org.id) for org in record.organisations.all()
        ]
        return AgentUser(
            id=UserId(id=record.id),
            email=Email(record.email),
            mute_all_dataset_notifications=mute_all_dataset_notifications,
            organisation_ids=organisation_ids,
            is_admin=False,
            notify_avl_unavailable=record.settings.notify_avl_unavailable,
        )
    elif record.is_org_admin or record.is_standard_user:
        return Publisher(
            id=UserId(id=record.id),
            email=Email(record.email),
            mute_all_dataset_notifications=mute_all_dataset_notifications,
            organisation_id=OrganisationId(id=record.organisation_id),
            is_admin=record.is_org_admin,
            notify_avl_unavailable=record.settings.notify_avl_unavailable,
        )
    elif record.is_site_admin:
        settings = record.settings
        return SiteAdmin(
            id=UserId(id=record.id),
            email=Email(record.email),
            mute_all_dataset_notifications=settings.mute_all_dataset_notifications,
        )
    else:
        return User(
            id=UserId(id=record.id),
            email=Email(record.email),
            mute_all_dataset_notifications=mute_all_dataset_notifications,
        )


def add_user(user: UserType) -> None:
    """
    Persists a user to storage
    Args:
        user: A polymorphic instance of a User domain entity

    Returns: None
    """
    record = models.User(
        id=user.get_id(),
        email=user.email,
        account_type=AccountType.developer.value,
    )

    if isinstance(user, Publisher):
        account_type = AccountType.org_staff.value
        if user.is_admin:
            account_type = AccountType.org_admin.value
        record.account_type = account_type
        record.save()
        # can only add organisation after user has been saved.
        record.organisations.add(user.organisation_id.id)
    elif isinstance(user, SiteAdmin):
        record.account_type = AccountType.site_admin.value
    record.save()
