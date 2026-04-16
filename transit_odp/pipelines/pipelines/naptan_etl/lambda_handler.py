"""
Lambda handler for NaPTAN archiving to S3.

Local testing:
    # Option 1: Direct Python invocation
    python manage.py shell << 'EOF'
    from transit_odp.pipelines.pipelines.naptan_etl.lambda_handler import handler
    result = handler({}, {})
    print(result)
    EOF

    # Option 2: Using the test script
    python test_lambda_local.py

AWS Lambda Deployment:
    1. Package the repository with dependencies:
       zip -r naptan-lambda.zip transit_odp/ config/ manage.py requirements.txt
    
    2. Upload to AWS Lambda console or via CLI:
       aws lambda create-function --function-name naptan-archiver \\
         --zip-file fileb://naptan-lambda.zip \\
         --handler transit_odp.pipelines.pipelines.naptan_etl.lambda_handler.handler \\
         --runtime python3.11 \\
         --role arn:aws:iam::ACCOUNT_ID:role/naptan-lambda-role \\
         --timeout 300 \\
         --environment Variables={AWS_NAPTAN_RAW_STORAGE_BUCKET_NAME=your-bucket-name,...}
    
    3. Set required environment variables:
       - AWS_NAPTAN_RAW_STORAGE_BUCKET_NAME (S3 bucket for NaPTAN data)
       - DJANGO_SETTINGS_MODULE (default: config.settings.prod)
       Note: AWS credentials are provided via the Lambda execution role (IAM),
       not via environment variables. Attach a role with s3:PutObject and
       s3:GetObject permissions on the target bucket.
    
    4. Trigger via:
       - AWS Console: Test button
       - AWS CLI: aws lambda invoke --function-name naptan-archiver response.json
       - EventBridge: Create scheduled rule to invoke daily/weekly
       - Step Functions: Add to state machine
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
