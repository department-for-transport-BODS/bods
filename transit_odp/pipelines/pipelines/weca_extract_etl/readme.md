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

- WECA_S3_KEY_METADATA [*optional*] = Optional S3 key for WECA Metadata JSON file, defaults to `raw/weca/weca_metadata_latest.json`
- WECA_S3_KEY_SERVICES [*optional*] = Optional S3 key for WECA Services JSON file, defaults to `raw/weca/weca_services_latest.json`
- WECA_S3_KEY_SERVICES_VALID [*optional*] = Optional S3 key for WECA Metadata JSON file, defaults to `raw/weca/weca_services_validated_latest.json`
- WECA_S3_KEY_REGISTRATIONS [*optional*] = Optional S3 key for WECA Metadata JSON file, defaults to `raw/weca/weca_registrations_latest.json`
- WECA_S3_KEY_REGISTRATIONS_VALID [*optional*] = Optional S3 key for WECA Metadata JSON file, defaults to `raw/weca/weca_registrations_validated_latest.json`