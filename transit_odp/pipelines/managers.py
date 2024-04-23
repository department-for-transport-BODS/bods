import datetime

from django.conf import settings
from django.db import models
from django.utils.timezone import now

from transit_odp.data_quality.models import DataQualityReportSummary


class DataQualityTaskManager(models.Manager):
    def get_unfinished(self):
        return self.filter(task_id__isnull=False).exclude(
            status__in=[self.model.SUCCESS, self.model.FAILURE, self.model.RECEIVED]
        )

    def get_latest_status(self):
        model = self.model
        try:
            # Get the latest DataQualityTask - in the future the user may retry
            # generating the report. The status of
            # revision as a whole should reflect the state of the latest task/report
            task = self.select_related("report__summary").latest()
            if task.status == model.FAILURE:
                return task.status

            if (task.status == model.SUCCESS) and task.report:
                try:
                    # If the summary exists then we know the DQS report was loaded
                    # successfully
                    _ = task.report.summary
                    return task.status
                except DataQualityReportSummary.DoesNotExist:
                    # Hack: if the summary does not exist 1 minute after the report
                    # was created consider the task failed
                    # TODO - track DQS report ETL state
                    # NOTE: CM - 1 minute isn't enough time for big datasets increasing
                    # to 5 minutes
                    if task.report.created < now() - datetime.timedelta(
                        minutes=settings.DQS_WAIT_TIMEOUT
                    ):
                        return model.FAILURE

        except model.DoesNotExist:
            pass

        return model.PENDING
