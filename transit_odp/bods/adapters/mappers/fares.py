from typing import Optional

from django.core.files.storage import default_storage

from transit_odp.bods.domain.entities import Revision
from transit_odp.bods.domain.entities.identity import OrganisationId, PublicationId
from transit_odp.bods.domain.entities.publication import FaresDataset, FaresPublication
from transit_odp.bods.domain.entities.user import UserId
from transit_odp.organisation import models
from transit_odp.organisation.constants import FeedStatus


class FaresMapper:
    @staticmethod
    def map_dataset_to_publication(
        dataset: models.Dataset,
        live: Optional[Revision[FaresDataset]],
        draft: Optional[Revision[FaresDataset]],
    ) -> FaresPublication:
        return FaresPublication(
            id=PublicationId(id=dataset.id),
            organisation_id=OrganisationId(id=dataset.organisation_id),
            contact_user_id=UserId(id=dataset.contact_id),
            live=live,
            draft=draft,
            events=[],
        )

    @staticmethod
    def map_datasetrevision_to_revision(
        revision: models.DatasetRevision,
    ) -> Revision[FaresDataset]:
        """Maps a DatasetRevision onto FaresDataset"""
        has_error = False
        if revision.status == FeedStatus.error.value:
            has_error = True

        has_expired = False
        if revision.status == FeedStatus.expired.value:
            has_expired = True

        report = None
        if revision.transxchange_version:
            report = FaresMapper._map_revision_to_fares_report(revision)

        published_by = None
        if revision.published_by_id:
            published_by = UserId(id=revision.published_by_id)

        return Revision[FaresDataset](
            created_at=revision.created,
            published_at=revision.published_at,
            published_by=published_by,
            has_error=has_error,
            dataset=FaresDataset(
                name=revision.name,
                description=revision.description,
                short_description=revision.short_description,
                comment=revision.comment,
                url=revision.url_link,
                filename=revision.upload_file.name,
                has_expired=has_expired,
                report=report,
            ),
        )

    @staticmethod
    def map_publication_to_datset(
        publication: FaresPublication, model: models.Dataset
    ) -> models.Dataset:
        return model

    @staticmethod
    def map_revision_to_datsetrevision(
        revision: Revision[FaresDataset], model: models.DatasetRevision
    ) -> models.DatasetRevision:
        # Set FaresDataset fields
        model.url_link = revision.dataset.url
        model = FaresMapper._sync_filefield(revision, model)
        return model

    @staticmethod
    def _sync_filefield(
        revision: Revision[FaresDataset], model: models.DatasetRevision
    ) -> models.DatasetRevision:
        """
        Synchronise filename on the domain model with upload_file on the ORM model.

        We cannot rely on the ORM to store and associate the file with the
        DatasetRevision because the ORM model isn't created until after the domain
        entity. Thus, we need to persist the file (using Django FileStorage) first
        and pass the filename to FaresDataset. Unfortunately, Django doesn't make
        it easy for us to manually associate the filename to model.
        """
        # check new file exists in storage
        if revision.dataset.filename:
            # TODO - handle exception better
            assert default_storage.exists(revision.dataset.filename)

        # TODO delete old file
        # old_filename = model.upload_file.name or None
        # if old_filename != revision.dataset.filename:
        #     transaction.on_commit(lambda: default_storage.delete(old_filename))

        # associate new file
        if revision.dataset.filename:
            # perform intermediate save to ensure we don't override our
            # changes in the next step
            model.save()

            # update filename directly in DB to prevent Django regenerating a new one
            models.DatasetRevision.objects.filter(id=model.id).update(
                upload_file=revision.dataset.filename
            )

            # refresh from DB to allow any further changes to be applied to the model
            model.refresh_from_db()

        return model
