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
    """Initialize SQS client, get queue names and send messages to the queues"""

    def __init__(self) -> object:
        """
        Initialize and return an SQS client.
        """
        try:
            self.endpoint_url = settings.SQS_QUEUE_ENDPOINT_URL

            if settings.AWS_ENVIRONMENT == "LOCAL":
                self.sqs_client = boto3.client(
                    "sqs",
                    endpoint_url=self.endpoint_url,
                    region_name=settings.AWS_REGION_NAME,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                )
            else:
                self.sqs_client = boto3.client(
                    "sqs",
                    endpoint_url=self.endpoint_url,
                )
        except Exception as e:
            logger.info(
                f"DQS-SQS:General exception when initialising SQS client wrapper: {e}"
            )
            raise

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

        except Exception as e:
            logger.info(f"DQS-SQS:General exception when listing queues: {e}")

        try:
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
                        try:
                            response_send_messages = self.sqs_client.send_message_batch(
                                QueueUrl=queue_url, Entries=messages
                            )

                            for success in response_send_messages.get("Successful", []):
                                logger.info(
                                    f"DQS-SQS:Message sent to {queue_url}: {success['MessageId']}"
                                )

                            for error in response_send_messages.get("Failed", []):
                                logger.info(
                                    f"DQS-SQS:Failed to send message to {queue_url}: {error['MessageId'] if 'MessageId' in error else error['Id']} - {error['Message']}"
                                )

                        except Exception as e:
                            logger.error(
                                f"DQS-SQS:Error sending message to {queue_name}: {e}"
                            )
                            raise
                    else:
                        logger.info(
                            f"DQS-SQS:Queue {queue_name} not found in SQS queues."
                        )
            else:
                raise ValueError("DQS-SQS:No SQS queues found")
        except Exception as e:
            logger.error(f"DQS-SQS:Error when trying to access the queues: {e}")
            raise
