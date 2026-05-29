"""
Lambda handler for NPTG upload to S3.
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
    AWS Lambda handler for NPTG file download.

    Downloads latest NPTG file from DfT API and saves it under raw/nptg for ETL to consume.

    Args:
        event: Lambda event (unused for this function)
        context: Lambda context (unused for this function)

    Returns:
        dict: Response with statusCode and body containing result or error
    """
    try:
        from transit_odp.pipelines.pipelines.nptg_extract_etl.extract import (
            get_latest_nptg_to_s3,
        )

        nptg_key = get_latest_nptg_to_s3()

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Latest NPTG downloaded successfully",
                    "nptg": nptg_key,
                }
            ),
        }
    except Exception as exc:
        import traceback

        error_msg = str(exc)
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
