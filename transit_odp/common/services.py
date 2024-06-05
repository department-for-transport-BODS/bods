from io import BytesIO

import boto3
from django.conf import settings


def get_gtfs_bucket_service():
    """Builds an S3BucketService using Django settings."""
    aws_access_key_id = settings.ITO_GTFS_AWS_ACCESS_KEY_ID
    aws_secret_access_key = settings.ITO_GTFS_AWS_SECRET_ACCESS_KEY
    bucket_name = settings.ITO_GTFS_AWS_STORAGE_BUCKET_NAME
    region_name = settings.ITO_GTFS_AWS_REGION

    return S3BucketService(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        bucket_name=bucket_name,
        region_name=region_name,
    )


class S3BucketService:
    """Service for interacting with an S3 bucket.
    Args:
        aws_access_key_id (str): AWS Key ID
        aws_secret_access_key (str): AWS Secret Key
        bucket_name (str): Name of bucket
        region_name (str): Region bucket is found in
    """

    def __init__(
        self,
        aws_access_key_id,
        aws_secret_access_key,
        bucket_name,
        region_name="eu-west-2",
    ):
        self._key_id = aws_access_key_id
        self._secret_key = aws_secret_access_key
        self._bucket_name = bucket_name
        self._region_name = region_name

        self._s3 = self._get_s3_client()

    def _get_s3_client(self):
        """Get a Boto3 S3 resource object."""
        return boto3.Session(
            region_name=self._region_name,
            aws_access_key_id=self._key_id,
            aws_secret_access_key=self._secret_key,
        ).resource("s3")

    def get_files(self):
        """Get all the objects in an S3 bucket."""
        try:
            files = self._s3.Bucket(self._bucket_name).objects.all()
        except ValueError:
            return []

        return files

    def get_file_names(self):
        """Get all the filenames of the files in an S3 bucket."""
        return [obj.key for obj in self.get_files()]

    def get_file(self, filename) -> BytesIO:
        """Gets a file from an S3 bucket."""
        file_ = BytesIO()
        try:
            self._s3.Bucket(self._bucket_name).download_fileobj(filename, file_)
        except ValueError:
            return None
        return file_
