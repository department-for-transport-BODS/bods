from django.dispatch import Signal

# Signal to Celery subsystem to start BODS ETL pipeline
dataset_etl = Signal()

# Signal to Celery subsystem to start DQS report ETL pipeline
dqs_report_etl = Signal()

dataset_changed = Signal()
