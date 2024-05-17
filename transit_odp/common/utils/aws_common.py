import logging

from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

logger = logging.getLogger(__name__)


def get_s3_bucket_storage():
    bucket_name = getattr(settings, "AWS_DATASET_MAINTENANCE_STORAGE_BUCKET_NAME", None)
    if not bucket_name:
        logger.error("Bucket name is not configured in settings.")
        raise ValueError("Bucket name is not configured in settings.")

    try:
        storage = S3Boto3Storage(bucket_name=bucket_name)
        logger.info(f"Successfully connected to S3 bucket: {bucket_name}")
        return storage
    except Exception as e:
        logger.error(f"Error connecting to S3 bucket {bucket_name}: {str(e)}")
        raise

def get_queue_by_name():
    sqs_queue_name = ""
    
    return SQS

def get_all_queues():
    queues=[]
    return [get_queue_by_name(queue.queue_name) for queue in queues]

def send_message_to_queue(messages):
    all_queues=get_all_queues()
    for message in messages:
        for queue in all_queues:
            queue.send_message(message)