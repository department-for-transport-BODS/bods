import logging

from transit_odp.organisation.updaters import DatasetUpdater

logger = logging.getLogger(__name__)


class TimetableUpdater(DatasetUpdater):
    def start_new_revision(self, comment: str):
        if self.draft is None:
            revision = self.dataset.start_revision(comment=comment)
        else:
            self.draft.delete()
            revision = self.dataset.start_revision(comment=comment)

        revision.upload_file = self.live_revision.upload_file
        revision.save()
        return revision
