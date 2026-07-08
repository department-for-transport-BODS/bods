# Testing in a Lambda

Create a python test script as detailed below:

```py
#!/usr/bin/env python
"""
Local test script for bank holidays Lambda handler.

Usage (from repo root, with docker-compose services running):
    docker compose run --rm $(grep -v '^#\|^$' .env.bank-holidays-test | sed 's/^/-e /') -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e BANK_HOLIDAYS_BUCKET_NAME -e AWS_SESSION_TOKEN -e AWS_DEFAULT_REGION  django python test_bank_holidays_lambda_local.py
"""
import json
import os
import sys

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
django.setup()

# Import Lambda handler
from transit_odp.pipelines.pipelines.bank_holidays_extract_etl.lambda_handler import (
    handler,
)

if __name__ == "__main__":
    print("=" * 70)
    print("Testing bank holidays Lambda Handler Locally")
    print("=" * 70)
    print()

    # Test the handler
    print("Invoking handler(event={}, context={})...")
    print()

    try:
        result = handler({}, {})

        status_code = result.get("statusCode")
        body = json.loads(result.get("body", "{}"))

        print(f"Status Code: {status_code}")
        print(f"Response Body:")
        print(json.dumps(body, indent=2))

        if status_code == 200:
            print()
            print("✅ SUCCESS: bank holidays archived to S3")
            print(f"   bank holidays: {body.get('bank_holidays')}")
        else:
            print()
            print("❌ FAILED: Lambda returned error")
            print(f"   Error: {body.get('error')}")
            if "trace" in body:
                print(f"   Traceback:\n{body.get('trace')}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    print()
    print("=" * 70)
```

Execute with AWS credentials:

```sh
# Optionally with `--use-device-code` in WSL environments
aws sso login --profile <profile name>

# Export as environment variables
export $(aws configure export-credentials --profile <profile name> --format env)

# Set bucket name - this could be any bucket, but this works as a default
export BANK_HOLIDAYS_BUCKET_NAME=bods-1297-data-landing-zone

# Execute test lambda
docker compose run --rm $(grep -v '^#\|^$' .env.bank-holidays-test | sed 's/^/-e /') -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e BANK_HOLIDAYS_BUCKET_NAME -e AWS_SESSION_TOKEN -e AWS_DEFAULT_REGION  django python test_bank_holidays_lambda_local.py
```