from django.dispatch import Signal

# Signal to Celery subsystem to start BODS ETL pipeline
dataset_etl = Signal(["revision"])

# Signal to Celery subsystem to start DQS report ETL pipeline
dqs_report_etl = Signal(["task"])

dataset_changed = Signal(["revision"])
