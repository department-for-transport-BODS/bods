from typing import Dict, Iterable, List, Optional, Protocol, Type, TypeVar

from django.core.paginator import Paginator
from freezegun import freeze_time

from transit_odp.bods.adapters.mappers.avl import AVLMapper
from transit_odp.bods.adapters.mappers.fares import FaresMapper
from transit_odp.bods.adapters.mappers.timetable import TimetableMapper
from transit_odp.bods.domain.entities import Dataset, Publication, Revision
from transit_odp.bods.domain.entities.identity import PublicationId
from transit_odp.organisation import models
from transit_odp.organisation.constants import AVLFeedStatus, DatasetType, FeedStatus

P = TypeVar("P", bound=Publication)
D = TypeVar("D", bound=Dataset)


class PublicationMapper(Protocol[P, D]):
    @staticmethod
    def map_dataset_to_publication(
        dataset: models.Dataset,
        live: Optional[Revision[D]],
        draft: Optional[Revision[D]],
    ) -> P:
        ...

    @staticmethod
    def map_datasetrevision_to_revision(
        revision: models.DatasetRevision,
    ) -> Revision[D]:
        ...

    @staticmethod
    def map_publication_to_datset(
        publication: P, model: models.Dataset
    ) -> models.Dataset:
        ...

    @staticmethod
    def map_revision_to_datsetrevision(
        revision: Revision[D], model: models.DatasetRevision
    ) -> models.DatasetRevision:
        ...


dispatcher: Dict[DatasetType, Type[PublicationMapper]] = {
    DatasetType.TIMETABLE: TimetableMapper,
    DatasetType.AVL: AVLMapper,
    DatasetType.FARES: FaresMapper,
}


def load_publications(
    dataset_types: Optional[List[DatasetType]] = None,
    publication_ids: Optional[List[PublicationId]] = None,
) -> Iterable[P]:
    """
    Loads Publication domain entities from the database
    Args:
        dataset_types: an optional list of DatasetType enums
        publication_ids: as optional list of PublicationId

    Returns:
        A polymorphic list of Publication domain entities
    """
    # Fetch Datasets
    datasets = models.Dataset.objects.select_related(
        "live_revision"
    ).add_draft_revisions()  # prefetches draft revision

    # Filter by DatasetType
    if dataset_types is not None:
        datasets = datasets.filter(dataset_type__in=[t.value for t in dataset_types])

    # Prefetch admin_areas and localities for Timetables
    if dataset_types is None or DatasetType.TIMETABLE in dataset_types:
        datasets = datasets.prefetch_related("revisions__admin_areas").prefetch_related(
            "revisions__localities"
        )

    # Filter specific PublicationIds
    if publication_ids is not None:
        datasets = datasets.filter(id__in=[identity.id for identity in publication_ids])

    # Map Dataset to Publication
    for dataset in datasets:
        yield map_dataset_to_publication(dataset)


def map_dataset_to_publication(dataset: models.Dataset) -> P:
    """
    Maps the Dataset model into a specific subtype of Publication domain object
    Args:
        dataset: an instance of Dataset ORM model

    Returns:
        A polymorphic instance of Publication domain object
    """
    # Get the mapper for the dataset_type
    mapper = dispatcher[DatasetType(dataset.dataset_type)]

    # Map live_revision to Revision
    live = None
    if dataset.live_revision is not None:
        live = mapper.map_datasetrevision_to_revision(dataset.live_revision)

    # Map draft_revision to Revision
    draft = None
    if len(dataset.draft_revisions):
        draft = mapper.map_datasetrevision_to_revision(dataset.draft_revisions[0])

    return mapper.map_dataset_to_publication(dataset, live, draft)


def load_revision_history(
    publication_id: PublicationId, page_num: int = 1, page_size: int = 10
) -> Iterable[Revision[D]]:
    """
    Loads a polymorphic list of Revision domain entities from the database
    for the given `publication_id`
    Args:
        publication_id: the ID of the Publication
        page_num: the page number for paginating the list of Revision objects
        page_size: the number of Revision objects to load

    Returns:
    """
    revisions = (
        models.DatasetRevision.objects.filter(dataset_id=publication_id.id)
        .get_published()
        .prefetch_related("admin_areas")
        .prefetch_related("localities")
        .select_related("dataset")
        .order_by("-created")
    )

    if not revisions:
        return None

    # Get the mapper for the dataset_type
    dataset_type = revisions[0].dataset.dataset_type
    mapper = dispatcher[DatasetType(dataset_type)]

    # Paginate queryset
    # TODO - handle error case
    page = Paginator(revisions, per_page=page_size).page(page_num)

    # TODO - pagination info could may be embedded in the response, e.g. page_num, count
    for revision in page.object_list:
        yield mapper.map_datasetrevision_to_revision(revision)


def add_publication(publication: P):
    """
    Persists a publication to storage
    Args:
        publication: A polymorphic instance of a Publication domain entity

    Returns: None
    """
    publication_id = publication.get_id()
    assert publication.draft

    mapper = dispatcher[publication.type]

    dataset = models.Dataset(
        id=publication_id,
        organisation_id=publication.organisation_id.id,
        contact_id=publication.contact_user_id.id,
        dataset_type=publication.type,
    )
    dataset = mapper.map_publication_to_datset(publication, dataset)
    dataset.save()

    # TODO - remove this hack by removing autonow on `created` field
    with freeze_time(publication.draft.created_at):
        # Create DatasetRevision from Publication.
        draft_revision = models.DatasetRevision(
            dataset=dataset,
            name=publication.draft.dataset.name,
            description=publication.draft.dataset.description,
            short_description=publication.draft.dataset.short_description,
            comment=publication.draft.dataset.comment,
        )
        draft_revision = mapper.map_revision_to_datsetrevision(
            publication.draft, draft_revision
        )
        draft_revision.save()


def update_publication(publication: P):
    """
    Updates a publication to storage
    Args:
        publication: A polymorphic instance of a Publication domain entity

    Returns: None
    """
    publication_id = publication.get_id()

    feed_status = publication.feed_status
    feed_last_checked = publication.feed_last_checked
    publication.subscribers

    datasets = models.Dataset.objects.filter(id=publication_id)
    live_revision = datasets[0].live_revision

    # TODO: add updates to other fields in Dataset and DatasetRevision
    datasets.update(avl_feed_status=feed_status.value)

    # Check if live_revision is not already inactive/expired This is because when a
    # feed is deactivated, CAVL service takes few minutes to clean up SWA resources
    # before the feed is actually removed from DB, so till then the feed

    # status comes back as FEED_DOWN
    # TODO: introduce a new status in CAVL service to handle the wait time till the
    #  feed is removed from DB, so that BODS can handle that new status
    if live_revision is not None and live_revision.status not in [
        FeedStatus.inactive.value,
        FeedStatus.expired.value,
    ]:
        if feed_status in [AVLFeedStatus.FEED_DOWN, AVLFeedStatus.SYSTEM_ERROR]:
            # We do not want to update the avl_feed_last_checked field if the
            # revision is already marked as 'error'
            if live_revision.status == FeedStatus.live.value:
                datasets.update(
                    avl_feed_last_checked=feed_last_checked,
                )
            live_revision.status = FeedStatus.error.value
        else:
            datasets.update(
                avl_feed_last_checked=feed_last_checked,
            )
            live_revision.status = FeedStatus.live.value

        live_revision.save()
