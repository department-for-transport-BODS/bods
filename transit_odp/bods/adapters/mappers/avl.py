from typing import Optional

from transit_odp.bods.domain.entities import AVLDataset, AVLPublication, Revision
from transit_odp.bods.domain.entities.identity import OrganisationId, PublicationId
from transit_odp.bods.domain.entities.user import UserId
from transit_odp.organisation import models
from transit_odp.organisation.constants import AVLFeedStatus, FeedStatus


class AVLMapper:
    @staticmethod
    def map_dataset_to_publication(
        dataset: models.Dataset,
        live: Optional[Revision[AVLDataset]],
        draft: Optional[Revision[AVLDataset]],
    ) -> AVLPublication:
        feed_status = AVLFeedStatus.DEPLOYING

        if dataset.avl_feed_status in AVLFeedStatus.__members__.keys():
            feed_status = AVLFeedStatus[dataset.avl_feed_status]

        subscribers = [
            UserId(id=subscriber.pk) for subscriber in dataset.subscribers.all()
        ]

        return AVLPublication(
            id=PublicationId(id=dataset.id),
            organisation_id=OrganisationId(id=dataset.organisation_id),
            contact_user_id=UserId(id=dataset.contact_id),
            feed_status=feed_status,
            feed_last_checked=dataset.avl_feed_last_checked,
            subscribers=subscribers,
            live=live,
            draft=draft,
            events=[],
        )

    @staticmethod
    def map_datasetrevision_to_revision(
        revision: models.DatasetRevision,
    ) -> Revision[AVLDataset]:
        has_error = False
        if revision.status == FeedStatus.error.value:
            has_error = True

        published_by = None
        if revision.published_by_id:
            published_by = UserId(id=revision.published_by_id)

        return Revision[AVLDataset](
            created_at=revision.created,
            published_at=revision.published_at,
            published_by=published_by,
            has_error=has_error,
            dataset=AVLDataset(
                name=revision.name,
                description=revision.description,
                short_description=revision.short_description,
                comment=revision.comment,
                url=revision.url_link,
                username=revision.username,
                password=revision.password,
                requestor_ref=revision.requestor_ref,
                id=revision.dataset.id,
            ),
        )

    @staticmethod
    def map_publication_to_datset(
        publication: AVLPublication, model: models.Dataset
    ) -> models.Dataset:
        model.avl_feed_status = publication.feed_status.value
        model.avl_feed_last_checked = publication.feed_last_checked
        return model

    @staticmethod
    def map_revision_to_datsetrevision(
        revision: Revision[AVLDataset], model: models.DatasetRevision
    ) -> models.DatasetRevision:
        model.url_link = revision.dataset.url
        model.username = revision.dataset.username
        model.password = revision.dataset.password
        model.requestor_ref = revision.dataset.requestor_ref
        return model
