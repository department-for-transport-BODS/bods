from transit_odp.pipelines.models import DataQualityTask


class TestDataQualityTaskManager:
    def test_get_unfinished(self, mocker):
        # Setup

        # mock out QS methods
        objects = DataQualityTask.objects
        mocked_exclude = mocker.patch.object(objects, "exclude", return_value=objects)
        mocked_filter = mocker.patch.object(objects, "filter", return_value=objects)

        # Test
        DataQualityTask.objects.get_unfinished()

        # Assert
        mocked_filter.assert_called_with(task_id__isnull=False)
        mocked_exclude.assert_called_with(
            status__in=[DataQualityTask.SUCCESS, DataQualityTask.FAILURE, DataQualityTask.RECEIVED],
        )
