"""
Lambda handler for WECA upload to S3
"""
import json
import os
import boto3

from celery.utils.log import get_task_logger
import django
from django.conf import settings

# Configure Django for Lambda environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

# Django bootstrap - required for Lambda to load models and utilities
if not settings.configured:
    django.setup()

logger = get_task_logger(__name__)
logger.setLevel(os.getenv("LOG_LEVEL", "WARNING").upper())


class GetSecretWrapper:
    def __init__(self, sm_client):
        self.client = sm_client

    def get_secret(self, secret_name) -> dict[str, str]:

        try:
            get_secret_value_response = self.client.get_secret_value(
                SecretId=secret_name
            )
            logger.info("Secret retrieved successfully.")
            return get_secret_value_response["SecretString"]
        except self.client.exceptions.ResourceNotFoundException:
            msg = f"The requested secret {secret_name} was not found."
            logger.info(msg)
            return msg
        except Exception as e:
            logger.error(f"An unknown error occurred: {str(e)}.")
            raise


def handler(event, context):
    """
    AWS Lambda handler for WECA file download.

    Downloads latest WECA files from DfT API,
    and saves them under raw/weca for ETL to consume.

    Args:
        event: Lambda event (unused for this function)
        context: Lambda context (unused for this function)

    Returns:
        dict: Response with statusCode and body containing result or error
    """
    try:
        from transit_odp.pipelines.pipelines.weca_extract_etl.extract import (
            get_latest_data,
        )

        sm_client = boto3.client("secretsmanager")
        sm_wrapper = GetSecretWrapper(sm_client)
        services_secret = json.loads(
            sm_wrapper.get_secret(os.getenv("AWS_WECA_SERVICES_SECRET"))
        )
        resgistrations_secret = json.loads(
            sm_wrapper.get_secret(os.getenv("AWS_WECA_REGISTRATIONS_SECRET"))
        )

        weca_meta = get_latest_data(services_secret, resgistrations_secret)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Latest WECA downloaded successfully",
                    "metadata": weca_meta,
                }
            ),
        }
    except Exception as e:
        import traceback

        error_msg = str(e)
        error_trace = traceback.format_exc()

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": error_msg,
                    "trace": error_trace,
                }
            ),
        }
