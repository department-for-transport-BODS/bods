from unittest.mock import Mock, call, patch

from transit_odp.pipelines.pipelines.dataset_etl import main


def test_run_reports_initial_progress_before_pipeline_initialization():
    revision = object()
    task = Mock()
    pipeline = Mock()

    def create_pipeline(_revision):
        task.update_progress.assert_called_once_with(10)
        return pipeline

    with patch.object(
        main, "TransXChangePipeline", side_effect=create_pipeline
    ) as pipeline_class:
        pipeline.extract.return_value = object()
        pipeline.transform.return_value = object()

        main.run(revision, task)

    assert task.update_progress.call_args_list == [
        call(10),
        call(70),
        call(80),
        call(90),
    ]
    pipeline_class.assert_called_once_with(revision)
