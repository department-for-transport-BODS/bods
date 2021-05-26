from typing import Iterable, List, Optional

from transit_odp.bods.domain.entities import Organisation
from transit_odp.bods.domain.entities.user import OrganisationId, UserId
from transit_odp.organisation import models


def load_organisations(
    organisation_ids: Optional[List[OrganisationId]] = None,
) -> Iterable[Organisation]:
    """
    Loads Organisation domain entities from the database
    Returns: A list of Organisation domain entities
    """
    records = models.Organisation.objects.all()

    if organisation_ids is not None:
        records = records.filter(id__in=[identity.id for identity in organisation_ids])

    for record in records:
        yield map_orm_to_model(record)


def map_orm_to_model(record: models.Organisation) -> Organisation:
    """
    Maps the Organisation model into a Organisation entity
    """
    key_contact_id = None
    if record.key_contact_id is not None:
        key_contact_id = UserId(id=record.key_contact_id)

    return Organisation(
        id=OrganisationId(id=record.id),
        name=record.name,
        short_name=record.short_name,
        is_active=record.is_active,
        key_contact_id=key_contact_id,
    )


def add_organisation(organisation: Organisation) -> None:
    """
    Persists an organisation to storage
    Args:
        organisation: An instance of a Organisation domain entity

    Returns: None
    """
    record = models.Organisation(
        id=organisation.get_id(),
        name=organisation.name,
        short_name=organisation.short_name,
        is_active=organisation.is_active,
        key_contact_id=organisation.key_contact_id,
    )

    record.save()
