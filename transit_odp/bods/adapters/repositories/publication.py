from typing import List, Optional, TypeVar, cast

from django.db import connection

from transit_odp.bods.adapters.mappers import publication as mappers
from transit_odp.bods.domain.entities import (
    AVLDataset,
    AVLPublication,
    Dataset,
    Publication,
    Revision,
    TimetableDataset,
    TimetablePublication,
)
from transit_odp.bods.domain.entities.identity import PublicationId
from transit_odp.bods.domain.entities.publication import FaresDataset, FaresPublication
from transit_odp.bods.interfaces.repository import (
    IAVLRepository,
    IFaresRepository,
    IPublicationRepository,
    ITimetableRepository,
)
from transit_odp.organisation.constants import DatasetType

P = TypeVar("P", bound=Publication)
D = TypeVar("D", bound=Dataset)

# NOTE
# functions modifying the data should not return anything
# functions retrieving the data should not modify anything


class PublicationRepository(IPublicationRepository[P, D]):
    def __init__(self):
        self.seen = set()

    def next_identity(self) -> PublicationId:
        cursor = connection.cursor()
        cursor.execute("select nextval('organisation_dataset_id_seq')")
        result = cursor.fetchone()[0]
        return PublicationId(id=result)

    def add(self, publication: P) -> None:
        mappers.add_publication(publication)
        self.seen.add(publication)

    def update(self, publication: P) -> None:
        mappers.update_publication(publication)
        self.seen.add(publication)

    def find(self, publication_id: PublicationId) -> Optional[P]:
        results: List[P] = self.list(publication_ids=[publication_id])
        if len(results) == 1:
            return results[0]
        return None

    def list(
        self,
        dataset_types: Optional[List[DatasetType]] = None,
        publication_ids: Optional[List[PublicationId]] = None,
    ) -> List[P]:
        return list(
            mappers.load_publications(
                dataset_types=dataset_types, publication_ids=publication_ids
            )
        )

    def get_revision_history(
        self,
        publication_id: PublicationId,
        page_num: int = 1,
        page_size: int = 10,
    ) -> List[Revision[D]]:
        return list(
            mappers.load_revision_history(
                publication_id, page_num=page_num, page_size=page_size
            )
        )


class TimetableRepository(
    ITimetableRepository, PublicationRepository[TimetablePublication, TimetableDataset]
):
    # Extend with methods specific to TimetablePublications.
    # Note: These are likely to be limited to read-only queries

    def list(
        self,
        dataset_types: Optional[List[DatasetType]] = None,
        publication_ids: Optional[List[PublicationId]] = None,
    ) -> List[TimetablePublication]:
        dataset_types = [DatasetType.TIMETABLE]
        results = super().list(
            dataset_types=dataset_types, publication_ids=publication_ids
        )
        return cast(List[TimetablePublication], results)  # mypy: ignore


class AVLRepository(IAVLRepository, PublicationRepository[AVLPublication, AVLDataset]):
    # Extend with methods specific to AVLPublications
    # Note: These are likely to be limited to read-only queries

    def list(
        self,
        dataset_types: Optional[List[DatasetType]] = None,
        publication_ids: Optional[List[PublicationId]] = None,
    ) -> List[AVLPublication]:
        dataset_types = [DatasetType.AVL]
        results = super().list(
            dataset_types=dataset_types, publication_ids=publication_ids
        )
        return cast(List[AVLPublication], results)  # mypy: ignore


class FaresRepository(
    IFaresRepository, PublicationRepository[FaresPublication, FaresDataset]
):
    # Extend with methods specific to AVLPublications
    # Note: These are likely to be limited to read-only queries

    def list(
        self,
        dataset_types: Optional[List[DatasetType]] = None,
        publication_ids: Optional[List[PublicationId]] = None,
    ) -> List[FaresPublication]:
        dataset_types = [DatasetType.FARES]
        results = super().list(
            dataset_types=dataset_types, publication_ids=publication_ids
        )
        return cast(List[FaresPublication], results)  # mypy: ignore
