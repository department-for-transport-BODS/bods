from storages.backends.s3boto3 import S3Boto3Storage


# Note: this class is pointed to by DEFAULT_FILE_STORAGE setting in production.py
class MediaRootS3Boto3Storage(S3Boto3Storage):
    # Prevent overwriting existing file with the same name. Unfortunately this isn't
    # the default!
    # Note we only apply this setting to Media storage, since we want static files to
    # be overwritten.
    file_overwrite = False
