"""updaters.py Module for automatically updating datasets uploaded via url.
"""
import hashlib
import logging

import requests
from django.conf import settings
from requests.exceptions import ConnectionError as RequestConnectionError
from requests.exceptions import ConnectTimeout, RequestException

from transit_odp.common.loggers import MonitoringLoggerContext, PipelineAdapter
from transit_odp.organisation.constants import INACTIVE
from transit_odp.organisation.models import Dataset, DatasetRevision
from transit_odp.organisation.notifications import (
    send_endpoint_available_notification,
    send_feed_changed_notification,
    send_feed_monitor_fail_final_try_notification,
    send_feed_monitor_fail_first_try_notification,
)

ERROR = "error"
DEFUALT_COMMENT = "Automatically detected change in data set"
DEACTIVATE_COMMENT = "Data set is not reachable"
TIMEOUT = 90

logger = logging.getLogger(__name__)


class DatasetUpdateException(Exception):
    pass


class DatasetUpdater:
    """
    Class to handle how and when an automated data set update occurs.
    """

    def __init__(self, dataset):
        self.dataset: Dataset = dataset
        self.live_revision: DatasetRevision = dataset.live_revision
        self._content = None

    @property
    def url(self):
        return self.live_revision.url_link

    @property
    def retry_count(self):
        return self.dataset.get_availability_retry_count().count

    @retry_count.setter
    def retry_count(self, count):
        retry_obj = self.dataset.get_availability_retry_count()
        retry_obj.count = count
        retry_obj.save()

    @property
    def content(self):
        if self._content is not None:
            return self._content
        self._content = self.get_content()
        return self._content

    @property
    def draft(self):
        return self.dataset.revisions.filter(is_published=False).first()

    def reset_retry_count(self):
        self.retry_count = 0

    def deactivate_dataset(self):
        """
        Deactivate the dataset.
        """
        self.live_revision.status = INACTIVE
        self.live_revision.comment = DEACTIVATE_COMMENT
        self.live_revision.save()

    def get_content(self):
        """
        Retrieve content from the datasets url.
        """
        try:
            response = requests.get(self.url, timeout=TIMEOUT)
            if response.ok:
                return response.content
            else:
                message = (
                    f"Dataset {self.dataset.id} => {self.url} returned "
                    f"{response.status_code}."
                )
                raise DatasetUpdateException(message)
        except (RequestConnectionError, ConnectTimeout) as exc:
            message = (
                f"Dataset {self.dataset.id} => {self.url} is currently unavailable."
            )
            raise DatasetUpdateException(message) from exc
        except RequestException as exc:
            message = f"Dataset {self.dataset.id} => Unable to check for new data."
            raise DatasetUpdateException(message) from exc

    def has_new_update(self):
        """
        Check if the data found at the url is different from the data in
        the live revision.
        """

        if not self.live_revision.upload_file:
            return False

        new_hash = hashlib.sha1(self.content).hexdigest()
        with self.live_revision.upload_file.open("rb") as f:
            live_hash = hashlib.sha1(f.read()).hexdigest()

        return new_hash != live_hash

    def draft_is_different(self):
        """
        Checks whether the content at the end of the url is different from the current
        draft.
        """
        new_hash = hashlib.sha1(self.content).hexdigest()
        with self.draft.upload_file.open("rb") as f:
            draft_hash = hashlib.sha1(f.read()).hexdigest()
        return new_hash != draft_hash

    def start_new_revision(self):
        if self.draft is None:
            revision = self.dataset.start_revision(comment=DEFUALT_COMMENT)
        elif self.draft.status == ERROR:
            self.draft.delete()
            revision = self.dataset.start_revision(comment=DEFUALT_COMMENT)
        else:
            # We have draft not the error state, do nothing.
            return

        revision.save()
        return revision


def update_dataset(dataset: Dataset, publish_task):
    context = MonitoringLoggerContext(object_id=dataset.id)
    adapter = PipelineAdapter(logger, {"context": context})
    updater = DatasetUpdater(dataset)
    try:
        adapter.info("Checking for update.")
        if updater.content is not None and updater.retry_count > 0:
            adapter.info("Dataset is now available.")
            updater.reset_retry_count()
            send_endpoint_available_notification(updater.dataset)

        if updater.has_new_update():
            if updater.draft and not updater.draft_is_different():
                adapter.info(
                    "Current draft is the same as the remote content - doing nothing."
                )
                return

            adapter.info("New data available.")
            new_revision = updater.start_new_revision()
            if new_revision is not None:
                adapter.info("Creating new revision.")
                args = (new_revision.id,)
                kwargs = {"do_publish": True}
                adapter.info("Start data set ETL pipeline.")
                publish_task.apply_async(args=args, kwargs=kwargs)
                send_feed_changed_notification(updater.dataset)
            else:
                adapter.info("Dataset contains a good revision. Do nothing.")
        else:
            adapter.info("No update required.")

    except DatasetUpdateException:
        adapter.warning("Unable to reach data set.")
        updater.retry_count += 1
        if updater.retry_count == 1:
            adapter.warning("First retry failed. Email operator.")
            send_feed_monitor_fail_first_try_notification(updater.dataset)
        elif updater.retry_count >= settings.FEED_MONITOR_MAX_RETRY_ATTEMPTS:
            adapter.warning("Max retries reached. Expiring data set.")
            send_feed_monitor_fail_final_try_notification(updater.dataset)
            updater.deactivate_dataset()
    except Exception:
        message = "Unexpected exception. Failed to update data set."
        adapter.error(message, exc_info=True)
