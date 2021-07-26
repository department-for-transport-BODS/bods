import logging

from transit_odp.common.loggers import MonitoringLoggerContext, PipelineAdapter
from transit_odp.organisation.models import Dataset
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


def reprocess_live_revision(dataset: Dataset, comment: str, pipeline_task):
    context = MonitoringLoggerContext(object_id=dataset.id)
    adapter = PipelineAdapter(logger, {"context": context})
    adapter.info("Attempting local timetable update.")
    updater = TimetableUpdater(dataset)
    new_revision = updater.start_new_revision(comment=comment)
    try:
        adapter.info("Creating new revision.")
        args = (new_revision.id,)
        kwargs = {"do_publish": True}
        adapter.info("Start data set ETL pipeline.")
        pipeline_task.apply_async(args=args, kwargs=kwargs)
    except Exception as err:
        adapter.error("Unexpected error occurred during update.", err)
