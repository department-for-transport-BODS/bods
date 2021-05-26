from django.conf import settings
from django.core.files.storage import default_storage
from storages.backends.s3boto3 import S3Boto3Storage


def get_sirivm_storage():
    if bucket_name := getattr(settings, "AWS_SIRIVM_STORAGE_BUCKET_NAME", False):
        return S3Boto3Storage(bucket_name=bucket_name)
    else:
        return default_storage
