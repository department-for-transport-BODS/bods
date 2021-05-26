from typing import List, Optional

from django.db import connection

from transit_odp.bods.adapters.mappers import organisation as mappers
from transit_odp.bods.domain.entities import Organisation
from transit_odp.bods.domain.entities.identity import OrganisationId
from transit_odp.bods.interfaces.repository import IOrganisationRepository

# NOTE
# functions modifying the data should not return anything
# functions retrieving the data should not modify anything


class OrganisationRepository(IOrganisationRepository):
    def next_identity(self) -> OrganisationId:
        cursor = connection.cursor()
        cursor.execute("select nextval('organisation_organisation_id_seq')")
        result = cursor.fetchone()[0]
        return OrganisationId(id=result)

    def add(self, organisation: Organisation) -> None:
        mappers.add_organisation(organisation)

    def update(self, organisation: Organisation) -> None:
        # TODO - implement update
        pass

    def find(self, organisation_id: OrganisationId) -> Optional[Organisation]:
        organisations = self.list(organisation_ids=[organisation_id])
        return organisations[0] if len(organisations) else None

    def list(
        self, organisation_ids: Optional[List[OrganisationId]] = None
    ) -> List[Organisation]:
        return list(mappers.load_organisations(organisation_ids=organisation_ids))
