from transit_odp.common.loggers import LoggerContext


class TaskLoggerContext(LoggerContext):
    component_name = "TransXChange"
    class_name = "Task"


class RevisionLoggerContext(TaskLoggerContext):
    class_name = "DatasetRevision"
