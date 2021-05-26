"""updaters.py Module for automatically updating timetable datasets
uploaded via url.
"""
import hashlib
import logging

import requests
from django.conf import settings
from requests.exceptions import ConnectionError as RequestConnectionError
from requests.exceptions import RequestException

from transit_odp.bods.interfaces.plugins import get_notifications
from transit_odp.common.enums import FeedErrorCategory, FeedErrorSeverity
from transit_odp.organisation.constants import TimetableType
from transit_odp.organisation.models import Dataset
from transit_odp.organisation.notifications import (
    send_endpoint_available_notification,
    send_feed_changed_notification,
    send_feed_monitor_fail_final_try_notification,
    send_feed_monitor_fail_first_try_notification,
)
from transit_odp.pipelines.models import DatasetETLError
from transit_odp.timetables.exceptions import (
    TimetableDoesNotExist,
    TimetableUnavailable,
    TransXChangeException,
)

logger = logging.getLogger(__name__)

notifier = get_notifications()

ERROR = "error"


class TimetableUpdater:
    def __init__(self, dataset, task):
        self._dataset = dataset
        self.pk = self._dataset.pk
        self._current_revision = self._dataset.live_revision
        self._content = None
        self._pipeline_task = task

    def __repr__(self):
        class_name = self.__class__.__name__
        return f"{class_name}(pk={self.pk}, url={self.url!r})"

    @classmethod
    def from_pk(cls, pk, task):
        dataset = (
            Dataset.objects.filter(id=pk, dataset_type=TimetableType)
            .select_related("live_revision__availability_retry_count")
            .select_related("live_revision")
        )

        if not dataset.exists():
            msg = f"Dataset {pk} does not exist."
            raise TimetableDoesNotExist(msg)

        return cls(dataset.first(), task)

    def update(self):
        """Attempt to updated the timetable."""
        try:
            if self.has_new_update:
                self._new_timetable_available()
        except TimetableUnavailable:
            self._timetable_unavailable()

    def _expire_dataset(self):
        """Create a DatasetETLError and expire the Dataset."""
        DatasetETLError.objects.filter(revision=self._dataset.live_revision).delete()
        DatasetETLError.objects.create(
            revision=self._dataset.live_revision,
            severity=FeedErrorSeverity.severe.value,
            category=FeedErrorCategory.availability.value,
            description="Data set is not reachable",
        )
        self._dataset.live_revision.to_expired()
        self._dataset.live_revision.save()

    def _timetable_unavailable(self):
        """Logic to handle case when the Timetable is unavailable."""
        max_retries = settings.FEED_MONITOR_MAX_RETRY_ATTEMPTS
        self.retry_count += 1

        if self.retry_count == 1:
            send_feed_monitor_fail_first_try_notification(self._dataset)
        elif self.retry_count >= max_retries:
            send_feed_monitor_fail_final_try_notification(self._dataset)
            self._expire_dataset()

    def has_errored_draft(self):
        return self._dataset.revisions.filter(is_published=False, status=ERROR).exists()

    def delete_drafts(self):
        self._dataset.revisions.filter(is_published=False).delete()
        self._dataset.refresh_from_db()

    def _new_timetable_available(self):
        """Logic for when a new Timetable is available."""
        comment = "Automatically detected change in data set"
        draft = self._dataset.revisions.filter(is_published=False).first()

        if draft is None:
            revision = self._dataset.start_revision(comment=comment)
        elif draft.status == ERROR:
            # errored draft exists, delete to prevent integrity error
            self.delete_drafts()
            revision = self._dataset.start_revision(comment=comment)
        else:
            # a error free draft exists, do nothing.
            return
        revision.save()
        self._pipeline_task.apply_async(
            args=(revision.id,), kwargs={"do_publish": True}
        )
        send_feed_changed_notification(self._dataset)

    def _url_available(self):
        """Logic for when a url is accessible."""

        if self.is_unavailable:
            self.reset_retry_count()
            send_endpoint_available_notification(self._dataset)

    def _get_content(self, url):
        """Retrieve content from the datasets url."""
        try:
            response = requests.get(url)
            if response.ok:
                self._content = response.content
                self._url_available()
                return self._content
            else:
                raise TimetableUnavailable(
                    f"Dataset {self.pk} => {self.url} returned {response.status_code}."
                )
        except RequestConnectionError as exc:
            raise TimetableUnavailable(
                f"Dataset {self.pk} => {self.url} is currently unavailable."
            ) from exc
        except RequestException as exc:
            raise TransXChangeException(
                f"Dataset {self.pk} => Unable to check for new data."
            ) from exc

    @property
    def retry_count(self):
        return self._dataset.get_availability_retry_count().count

    @retry_count.setter
    def retry_count(self, count):
        retry_obj = self._dataset.get_availability_retry_count()
        retry_obj.count = count
        retry_obj.save()

    def reset_retry_count(self):
        self._dataset.get_availability_retry_count().reset()

    @property
    def url(self):
        return self._current_revision.url_link

    @property
    def is_unavailable(self):
        return self.retry_count > 0

    @property
    def content(self):
        if self._content is not None:
            return self._content
        self._content = self._get_content(self.url)
        return self._content

    @property
    def has_new_update(self):
        """Check if the content found at the url is different from the current
        timetable file."""
        new_hash = hashlib.sha1(self.content).hexdigest()
        if self._current_revision.upload_file is None:
            return False

        with self._current_revision.upload_file.open("rb") as f:
            old_hash = hashlib.sha1(f.read()).hexdigest()

        return new_hash != old_hash
