import json
import logging
import re
import time
from datetime import datetime

import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

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
            raise
        try:
            if "QueueUrls" in response:
                queue_urls = response["QueueUrls"]
                # Create a mapping from queue name to URL
                queue_url_map = {
                    self.get_queue_name_from_url(queue_url): queue_url
                    for queue_url in queue_urls
                }
                batch_size = 10
                for queue_name, messages in queues_payload.items():
                    if queue_name in queue_url_map:
                        queue_url = queue_url_map[queue_name]
                        try:
                            # Max allowed batch size by SQS is 10
                            for i in range(0, len(messages), batch_size):
                                batch = messages[i : i + batch_size]
                                response_send_messages = (
                                    self.sqs_client.send_message_batch(
                                        QueueUrl=queue_url, Entries=batch
                                    )
                                )

                                for success in response_send_messages.get(
                                    "Successful", []
                                ):
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


class StepFunctionsClientWrapper:
    """Initialize Step Functions client, execute Step Functions and check for status"""

    def __init__(self) -> None:
        """
        Initialize and return an Step Functions client.
        """
        try:
            if settings.AWS_ENVIRONMENT == "LOCAL":
                self.step_function_client = boto3.client(
                    "stepfunctions",
                    region_name=settings.AWS_REGION_NAME,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                )
            else:
                self.step_function_client = boto3.client(
                    "stepfunctions",
                )
        except NoCredentialsError as e:
            logger.error("AWS Step Functions: Missing AWS credentials")
            raise
        except PartialCredentialsError as e:
            logger.error("AWS Step Functions: Incomplete AWS credentials")
            raise
        except Exception as e:
            logger.error(f"AWS Step Functions: Error initializing client: {e}")
            raise

    # Initialize and call AWS Step Functions
    def start_step_function(
        self, input_payload: str, step_function_arn: str, name: str = ""
    ):
        try:
            if not name:
                name = self.clean_state_machine_name(input_payload)
            # Invoke the Step Function
            response = self.step_function_client.start_execution(
                stateMachineArn=step_function_arn,
                name=name,
                input=input_payload,
            )
            self.execution_arn = response["executionArn"]
        except Exception as e:
            logger.exception(
                f"AWS Step Functions: General exception when starting Step Functions: {e}"
            )
            raise

    def clean_state_machine_name(self, input_payload: str) -> str:
        """
        Statemachine Names much only contain: 0-9, A-Z, a-z, - and _
        If not, Cloudwatch Logging is disabled
        """
        try:
            input_payload_dict = json.loads(input_payload)
            if not isinstance(input_payload_dict, dict):  # Ensure it's a dictionary
                raise ValueError("Invalid JSON payload: Expected a dictionary")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON input: {e}")
            raise ValueError("Invalid JSON payload")

        revision_id = input_payload_dict.get("datasetRevisionId", "unknown")
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        execution_name = f"{revision_id}_{now}"

        cleaned = re.sub(r"[^a-zA-Z0-9\-_]", "", execution_name)

        if cleaned != execution_name:
            logger.warning(
                f"Name contained invalid characters: '{execution_name}' -> '{cleaned}'"
            )

        # AWS Step Function execution name max length is 80 characters
        MAX_NAME_LENGTH = 80
        if len(cleaned) > MAX_NAME_LENGTH:
            cleaned = cleaned[:MAX_NAME_LENGTH]
            logger.warning(f"Execution name truncated to: {cleaned}")

        return cleaned

    def wait_for_completion(self, poll_interval=5):
        while True:
            response = self.step_function_client.describe_execution(
                executionArn=self.execution_arn
            )
            status = response["status"]
            if status in ["SUCCEEDED", "FAILED", "TIMED_OUT", "ABORTED"]:
                return status, response
            time.sleep(poll_interval)
