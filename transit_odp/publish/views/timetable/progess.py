import datetime
import json
import logging
import math

from django.http import HttpResponse
from django.utils.timezone import now

from transit_odp.avl.models import CAVLValidationTaskResult
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models import DatasetRevision

logger = logging.getLogger(__name__)


# TODO - move to DRF


class PublishProgressView:
    def get_progress(self, pk):
        feed_id = pk
        if feed_id is not None:
            revision = DatasetRevision.objects.filter(dataset_id=feed_id).latest()
            progress = 0

            if revision.dataset.dataset_type in [
                DatasetType.TIMETABLE,
                DatasetType.FARES,
            ]:
                task = revision.etl_results.latest()
                progress = task.progress
                # TODO - should probably return the error code rather than progress=100
                if task.error_code:
                    progress = 100
            elif revision.dataset.dataset_type == DatasetType.AVL:
                try:
                    validation_task = CAVLValidationTaskResult.objects.filter(
                        revision=revision
                    ).latest("created")
                    if (validation_task.status == CAVLValidationTaskResult.SUCCESS) or (
                        validation_task.status == CAVLValidationTaskResult.FAILURE
                    ):
                        progress = 100
                    else:
                        # TODO do this better
                        # fake progress assuming validation might take 5 minutes
                        expected_time = datetime.timedelta(seconds=5 * 60)
                        elapsed_time = now() - validation_task.created
                        # don't let it reach 99% or page will continuously refresh...
                        progress = math.floor(
                            min(elapsed_time / expected_time, 0.99) * 100
                        )
                except CAVLValidationTaskResult.DoesNotExist:
                    message = (
                        f"Could not find CAVLValidationTaskResult "
                        f"for revision: {revision}"
                    )
                    logger.warning(message, exc_info=True)

            response_data = {"progress": progress}

            return HttpResponse(
                json.dumps(response_data), content_type="application/json"
            )
