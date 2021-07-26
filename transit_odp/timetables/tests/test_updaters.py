from datetime import datetime
from unittest.mock import patch

import pytest
import pytz
from django.test import override_settings

from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.organisation.updaters import ERROR
from transit_odp.timetables.tasks import task_reprocess_file_based_datasets

pytestmark = pytest.mark.django_db

PIPELINE_TASK = "transit_odp.timetables.tasks.task_dataset_pipeline"


@override_settings(PTI_START_DATE=datetime(2021, 5, 24))
def test_reprocess_dataset_create_new_revision():
    """
    Given that a dataset has not be updated since PTI_START_DATE.
    Ensure that a new revision is created and the task is called with the correct
    details.
    """
    live_revision = DatasetRevisionFactory(
        upload_file__data=b"data",
        created=datetime(2021, 5, 1, tzinfo=pytz.utc),
    )
    dataset = live_revision.dataset

    with patch(PIPELINE_TASK) as task:
        task_reprocess_file_based_datasets()
        assert dataset.revisions.count() == 2
        new_revision = dataset.revisions.order_by("created").last()
        assert new_revision.upload_file == dataset.live_revision.upload_file
        task.apply_async.assert_called_once_with(
            args=(new_revision.id,), kwargs={"do_publish": True}
        )


@override_settings(PTI_START_DATE=datetime(2021, 5, 24))
def test_reprocess_dataset_dont_create_new_revision():
    live_revision = DatasetRevisionFactory(
        upload_file__data=b"data",
        created=datetime(2021, 5, 26, tzinfo=pytz.utc),
    )
    dataset = live_revision.dataset
    with patch(PIPELINE_TASK) as task:
        task_reprocess_file_based_datasets()
        assert dataset.revisions.count() == 1
        new_revision = dataset.revisions.order_by("created").last()
        assert new_revision.upload_file == dataset.live_revision.upload_file
        task.assert_not_called()


@override_settings(PTI_START_DATE=datetime(2021, 5, 24))
def test_reprocess_dataset_delete_draft():
    live_revision = DatasetRevisionFactory(
        upload_file__data=b"data",
        created=datetime(2021, 5, 1, tzinfo=pytz.utc),
    )
    dataset = live_revision.dataset
    draft = DatasetRevisionFactory(dataset=dataset, is_published=False)

    assert dataset.revisions.count() == 2

    with patch(PIPELINE_TASK) as task:
        task_reprocess_file_based_datasets()
        assert dataset.revisions.count() == 2
        new_revision = dataset.revisions.order_by("created").last()
        assert new_revision.upload_file == dataset.live_revision.upload_file
        task.apply_async.assert_called_once_with(
            args=(new_revision.id,), kwargs={"do_publish": True}
        )
        assert new_revision.id != draft.id


@override_settings(PTI_START_DATE=datetime(2021, 5, 24))
def test_reprocess_dataset_errored_draft():
    """
    GIVEN that the current draft is in the error status
    THEN dataset should not have been reprocessed
    """
    live_revision = DatasetRevisionFactory(
        upload_file__data=b"data",
        created=datetime(2021, 5, 1, tzinfo=pytz.utc),
    )
    dataset = live_revision.dataset
    draft = DatasetRevisionFactory(
        dataset=dataset,
        is_published=False,
        status=ERROR,
        created=datetime(2021, 5, 26, tzinfo=pytz.utc),
    )

    assert dataset.revisions.count() == 2
    with patch(PIPELINE_TASK) as task:
        task_reprocess_file_based_datasets()
        assert dataset.revisions.count() == 2
        last_revision = dataset.revisions.order_by("created").last()
        assert last_revision.id == draft.id
        task.apply_async.assert_not_called()
