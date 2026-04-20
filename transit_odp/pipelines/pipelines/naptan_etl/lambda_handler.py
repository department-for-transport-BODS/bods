"""
Lambda handler for NaPTAN archiving to S3.

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
    AWS Lambda handler for NaPTAN archiving.
    
    Downloads latest NaPTAN XML from DfT API, archives the previous copy in S3,
    and saves new file at raw/naptan/latest.xml for ETL to consume.
    
    NOTE: SSL/TLS setup:
    - LOCAL TESTING: Mount custom CA cert via docker -v and set SSL_CERT_FILE/REQUESTS_CA_BUNDLE env vars.
    - PROD LAMBDA: Uses AWS Lambda execution role + standard AWS CA bundles. No custom cert needed.
    
    Args:
        event: Lambda event (unused for this function)
        context: Lambda context (unused for this function)
    
    Returns:
        dict: Response with statusCode and body containing result or error
    """
    try:
        from transit_odp.pipelines.pipelines.naptan_etl.extract import (
            get_latest_naptan_to_s3,
        )

        naptan_key = get_latest_naptan_to_s3()
        
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "NaPTAN archived successfully",
                    "s3_key": naptan_key,
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
