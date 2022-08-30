from transit_odp.browse.tasks import (
    task_create_bulk_data_archive,
    task_create_change_data_archive,
)

ARCHIVE_MUT = "transit_odp.browse.tasks"


class TestTaskDataArchive:
    def test_task_create_bulk_data_archive(self, mocker):
        mocked = mocker.patch(f"{ARCHIVE_MUT}.bulk_data_archive")
        task_create_bulk_data_archive()
        mocked.run.assert_called_once_with()

    def test_task_create_change_data_archive(self, mocker):
        mocked = mocker.patch(f"{ARCHIVE_MUT}.change_data_archive")
        task_create_change_data_archive()
        mocked.run.assert_called_once_with()
