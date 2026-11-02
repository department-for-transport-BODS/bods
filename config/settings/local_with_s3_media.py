# MEDIA
# ------------------------------------------------------------------------------
from storages.backends.s3boto3 import S3Boto3Storage  # noqa E402

from .local import *  # noqa
from .local import env

# A settings file that allows you to use S3 as the media storage backend for
# local testing.


AWS_ACCESS_KEY_ID = env("DJANGO_AWS_ACCESS_KEY_ID")
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_SECRET_ACCESS_KEY = env("DJANGO_AWS_SECRET_ACCESS_KEY")
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_STORAGE_BUCKET_NAME = env("DJANGO_AWS_STORAGE_BUCKET_NAME")
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_QUERYSTRING_AUTH = False
# DO NOT change these unless you know what you're doing.
_AWS_EXPIRY = 60 * 60 * 24 * 7
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": f"max-age={_AWS_EXPIRY}, s-maxage={_AWS_EXPIRY}, must-revalidate"
}
# Ensure all files inherit buckets ACL
AWS_DEFAULT_ACL = None
AWS_BUCKET_ACL = None


class MediaRootS3Boto3Storage(S3Boto3Storage):
    # Prevent overwriting existing file with the same name. Unfortunately this
    # isn't the default!
    # Note we only apply this setting to Media storage, since we want static files to
    # be overwritten.
    file_overwrite = False


DEFAULT_FILE_STORAGE = "config.settings.local_with_s3_media.MediaRootS3Boto3Storage"
MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/"
