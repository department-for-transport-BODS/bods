import logging
from datetime import timedelta

from rest_framework.response import Response
from rest_framework.views import APIView

from transit_odp.avl.models import CAVLValidationTaskResult
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models import DatasetRevision
from transit_odp.publish.views.utils import get_simulated_progress

logger = logging.getLogger(__name__)

PROGRESS_TIMEOUT = 2
COMPLETED = 100


class ProgressAPIView(APIView):
    def get_object(self, pk):
        """Get a dataset revision object from a dataset id."""
        return DatasetRevision.objects.filter(dataset_id=pk).latest()

    def get_avl_progress(self, revision):
        """Get the progress of a currently processing AVL datafeed."""
        try:
            task = CAVLValidationTaskResult.objects.filter(
                revision_id=revision.id
            ).latest("created")
        except CAVLValidationTaskResult.DoesNotExist:
            msg = f"Could not find CAVLValidationTaskResult for revision: {revision.id}"
            logger.warning(msg, exc_info=True)
            return COMPLETED

        if task.status in [task.SUCCESS, task.FAILURE]:
            progress = COMPLETED
        else:
            # We need to fake the progression
            max_minutes = timedelta(minutes=PROGRESS_TIMEOUT)
            progress = get_simulated_progress(task.created, max_minutes)
            if progress >= 99:
                # if we get here then something has gone wrong
                task.to_timeout_error()
                task.save()
        return progress

    def get_timetable_progress(self, revision):
        """Get the progress of a currently processing timetables dataset."""
        progress = 0
        task = revision.etl_results.order_by("-id").first()
        if task is not None:
            progress = task.progress
            if task.error_code:
                progress = COMPLETED
        return progress

    def get_fares_progress(self, revision):
        """Get the progress of a currently processing fares dataset."""
        progress = 0
        task = revision.etl_results.order_by("-id").first()
        if task is not None:
            progress = task.progress
            if task.error_code:
                progress = COMPLETED
        return progress

    def get(self, request, pk, format=None):
        """Get the progress of a dataset revision."""
        revision = self.get_object(pk)
        progress = 0
        if revision.dataset.dataset_type == DatasetType.TIMETABLE:
            progress = self.get_timetable_progress(revision)

        elif revision.dataset.dataset_type == DatasetType.AVL:
            progress = self.get_avl_progress(revision)

        elif revision.dataset.dataset_type == DatasetType.FARES:
            progress = self.get_fares_progress(revision)

        return Response({"progress": progress, "status": revision.status})
