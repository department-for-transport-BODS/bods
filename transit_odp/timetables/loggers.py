from transit_odp.common.loggers import LoggerContext


class TaskLoggerContext(LoggerContext):
    component_name: str = "TransXChange"
    class_name: str = "Task"


class RevisionLoggerContext(TaskLoggerContext):
    class_name: str = "DatasetRevision"


class DQSLoggerContext(LoggerContext):
    component_name: str = "DQS"
    class_name: str = "DataQualityReport"


class DQSTaskLogger(DQSLoggerContext):
    class_name: str = "DataQualityTask"
