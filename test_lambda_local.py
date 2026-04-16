#!/usr/bin/env python
"""
Local test script for NaPTAN Lambda handler.

Usage (from repo root, with docker-compose services running):
    docker-compose run --rm $(grep -v '^#\|^$' .env.naptan-test | sed 's/^/-e /') django python test_lambda_local.py
"""
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
django.setup()

# Import Lambda handler
from transit_odp.pipelines.pipelines.naptan_etl.lambda_handler import handler


if __name__ == "__main__":
    print("=" * 70)
    print("Testing NaPTAN Lambda Handler Locally")
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
            print("✅ SUCCESS: NaPTAN archived to S3")
            print(f"   Location: {body.get('s3_key')}")
        else:
            print()
            print("❌ FAILED: Lambda returned error")
            print(f"   Error: {body.get('error')}")
            if 'trace' in body:
                print(f"   Traceback:\n{body.get('trace')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print()
    print("=" * 70)
