# WECA Data Ingest Pipeline

This pipeline fetches data from the WECA API. There are 2 types of request that are made to the same API with different parameters:

- Services
- Registrations

The parameters for each request are stored in secrets in the AWS environment.

## Secrets

The following structure is used in the secrets storing the parameters used in this pipeline:

```json
{
    "api_key": "value",
    "param_c": "param_c",
    "param_t": "param_t",
    "param_r": "param_r",
    "url": "url"
}
```

*Note* the api key is not the same for the two types of request! The URL is the same for both types of request.

## Environment Varaibles

The following enviornment variables are required for this pipeline.

- AWS_WECA_SERVICES_SECRET = Name/ARN for the services request parameters secret.
- AWS_WECA_REGISTRATIONS_SECRET = Name/ARN for the registrations request parameters secret.
- AWS_WECA_RAW_STORAGE_BUCKET_NAME = S3 Bucket name for storage of WECA data.

### Optional Environment Variables

These environment variables may be set to override the default values.

- LOG_LEVEL [*optional*] = Set the log level, defaults to `WARNING`
- WECA_S3_KEY_METADATA [*optional*] = Optional S3 key for WECA Metadata JSON file, defaults to `raw/weca/weca_metadata_latest.json`
- WECA_S3_KEY_SERVICES [*optional*] = Optional S3 key for WECA Services JSON file, defaults to `raw/weca/weca_services_latest.json`
- WECA_S3_KEY_SERVICES_VALID [*optional*] = Optional S3 key for WECA Metadata JSON file, defaults to `raw/weca/weca_services_validated_latest.json`
- WECA_S3_KEY_REGISTRATIONS [*optional*] = Optional S3 key for WECA Metadata JSON file, defaults to `raw/weca/weca_registrations_latest.json`
- WECA_S3_KEY_REGISTRATIONS_VALID [*optional*] = Optional S3 key for WECA Metadata JSON file, defaults to `raw/weca/weca_registrations_validated_latest.json`

## Testing

Create and run the following Python script from the terminal:

```py
import os
import json
import dotenv
import logging

dotenv.load_dotenv(".env.weca_local")

import django
from django.conf import settings

# Configure Django for Lambda environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

# Django bootstrap - required for Lambda to load models and utilities
if not settings.configured:
    django.setup()

from transit_odp.pipelines.pipelines.weca_extract_etl.extract import get_latest_data

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

if __name__ == "__main__":

    test_services = {
        "url": "<in SM BODS>",
        "api_key": "<in SM BODS>",
        "param_c": "<in SM BODS>",
        "param_t": "<in SM BODS>",
        "param_r": "<in SM BODS>",
    }
    test_registrations = {
        "url": "<in SM PDBRD>",
        "api_key": "<in SM PDBRD>",
        "param_c": "<in SM PDBRD>",
        "param_t": "<in SM PDBRD>",
        "param_r": "<in SM PDBRD>",
    }

    logger.info("Starting WECA Test")
    metadata = get_latest_data(test_services, test_registrations)

    logger.info(f"Results: {json.dumps(metadata, indent=4)}")
```
