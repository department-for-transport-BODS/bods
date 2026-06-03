"""
Lambda handler for NaPTAN upload to S3
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
        from transit_odp.pipelines.pipelines.weca_extract_etl.extract import get_latest_data

        weca_meta = get_latest_data()

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Latest WECA downloaded successfully",
                    "weca": weca_meta,
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
