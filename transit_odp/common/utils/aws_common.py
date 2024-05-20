import logging
import json

from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage
import boto3

logger = logging.getLogger(__name__)


def get_s3_bucket_storage() -> object:
    """
    Get AWS S3 bucker storage object
    """
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


class SQSClientWrapper:
    def __init__(self) -> object:
        """
        Initialize and return an SQS client.
        """
        self.sqs_client = boto3.client(
            "sqs",
            endpoint_url=settings.SQS_QUEUE_ENDPOINT_URL,
            region_name=settings.AWS_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

    def get_queue_name_from_url(self, queue_url: str) -> str:
        """
        Extract and return the queue name from the queue URL.
        """
        return queue_url.split("/")[-1]

    def send_message_to_queue(self, queues_payload: dict):
        """
        Send messages to SQS queues based on the provided payload.
        """

        try:
            response = self.sqs_client.list_queues()
            if "QueueUrls" in response:
                queue_urls = response["QueueUrls"]
                # Create a mapping from queue name to URL
                queue_url_map = {
                    self.get_queue_name_from_url(queue_url): queue_url
                    for queue_url in queue_urls
                }

                for queue_name, messages in queues_payload.items():
                    if queue_name in queue_url_map:
                        queue_url = queue_url_map[queue_name]
                        for message in messages:
                            try:
                                response_send = self.sqs_client.send_message(
                                    QueueUrl=queue_url, MessageBody=json.dumps(message)
                                )
                                logger.info(
                                    f"Message sent to {queue_name}: {response_send['MessageId']}"
                                )
                            except Exception as e:
                                logger.error(
                                    f"Error sending message to {queue_name}: {e}"
                                )
                                raise
                    else:
                        logger.info(f"Queue {queue_name} not found in SQS queues.")
            else:
                logger.error("No SQS queues found.")
                raise ValueError("No SQS queues found")
        except Exception as e:
            logger.error(f"Error when trying to access the queues: {e}")
            raise
