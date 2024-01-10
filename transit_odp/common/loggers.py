from logging import LoggerAdapter

from pydantic import BaseModel


class LoggerContext(BaseModel):
    component_name: str = ""
    class_name: str = ""
    object_id: int = -1


class PipelineAdapter(LoggerAdapter):
    def process(self, msg, kwargs):
        if "context" in self.extra:
            context: LoggerContext = kwargs.pop("context", self.extra["context"])

            prefix = "[{component_name}] {class_name} {object_id} => ".format(
                **context.model_dump()
            )
            msg = prefix + msg
        return msg, kwargs


class LoaderAdapter(LoggerAdapter):
    def __init__(self, pipeline, logger, extra=None):
        self.pipeline = pipeline
        super().__init__(logger, extra)

    def process(self, msg, kwargs):
        msg: str = f"[{self.pipeline}] => {msg}"
        return msg, kwargs


class MonitoringLoggerContext(LoggerContext):
    class_name: str = "Dataset"
    component_name: str = "DatasetMonitoring"


class DatasetPipelineLoggerContext(LoggerContext):
    class_name: str = "Dataset"
    component_name: str = "TimetablePipeline"


class DatafeedPipelineLoggerContext(LoggerContext):
    class_name: str = "AVLDataset"
    component_name: str = "AVLPipeline"


def get_dataset_adapter_from_revision(logger, revision) -> PipelineAdapter:
    context: DatafeedPipelineLoggerContext = DatasetPipelineLoggerContext(
        object_id=revision.dataset_id
    )
    adapter: PipelineAdapter = PipelineAdapter(logger, {"context": context})
    return adapter


def get_datafeed_adapter(logger, feed_id: int) -> PipelineAdapter:
    context: DatafeedPipelineLoggerContext = DatafeedPipelineLoggerContext(
        object_id=feed_id
    )
    adapter: PipelineAdapter = PipelineAdapter(logger, {"context": context})
    return adapter
