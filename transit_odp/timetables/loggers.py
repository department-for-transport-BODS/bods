from transit_odp.common.loggers import LoggerContext


class TaskLoggerContext(LoggerContext):
    component_name = "TransXChange"
    class_name = "Task"


class RevisionLoggerContext(TaskLoggerContext):
    class_name = "DatasetRevision"


class DQSLoggerContext(LoggerContext):
    component_name = "DQS"
    class_name = "DataQualityReport"


class DQSTaskLogger(DQSLoggerContext):
    class_name = "DataQualityTask"
