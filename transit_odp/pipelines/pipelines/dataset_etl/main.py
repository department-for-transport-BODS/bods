from transit_odp.organisation.models import DatasetRevision
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.timetables.etl import TransXChangePipeline


def run(revision: DatasetRevision, task: DatasetETLTaskResult) -> DatasetRevision:
    try:
        pipeline = TransXChangePipeline(revision)
        extracted = pipeline.extract()
        task.update_progress(70)
        transformed = pipeline.transform(extracted)
        task.update_progress(80)
        pipeline.load(transformed)
        task.update_progress(90)

    except Exception:
        # Treat unhandled exception as a system error
        task.to_error("dataset_etl", task.SYSTEM_ERROR)
        raise

    return revision
