"""
Lambda handler for OTC upload to S3
"""
import json
import os
import django
from django.conf import settings

# Configure Django for Lambda environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

# Django bootstrap - required for Lambda to load models and utilities
if not settings.configured:
    django.setup()


def handler(event, context):
    """
    AWS Lambda handler for OTC file download.

    Downloads latest OTC data from the source,
    and saves new file at raw/otc/otc_latest.xml for ETL to consume.

    Args:
        event: Lambda event (unused for this function)
        context: Lambda context (unused for this function)

    Returns:
        dict: Response with statusCode and body containing result or error
    """
    try:
        from transit_odp.pipelines.pipelines.otc_etl.extract import (
            get_latest_otc_to_s3,
        )

        otc_key = get_latest_otc_to_s3()

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Latest OTC data downloaded successfully",
                    "s3_key": otc_key,
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