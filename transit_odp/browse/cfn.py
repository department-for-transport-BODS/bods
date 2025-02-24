from datetime import datetime, timedelta, timezone
from django.conf import settings
from botocore.signers import CloudFrontSigner
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from os import environ
import logging

logger = logging.getLogger(__name__)


def get_private_key():
    pem_data = environ.get("CLOUDFRONT_PRIVATE_KEY_SSM_PARAMETER")
    if pem_data is None:
        logger.error("Private key not found in environment variables.")
        raise ValueError("Private key not found in environment variables.")
    logger.info("Private key retrieved from environment variables.")
    if isinstance(pem_data, str):
        return pem_data.encode("utf-8")
    return pem_data


def rsa_signer(message):
    try:
        private_key = serialization.load_pem_private_key(
            get_private_key(), password=None, backend=default_backend()
        )
    except ValueError as e:
        logger.error(f"Could not deserialize key data: {e}")
        raise
    return private_key.sign(message, padding.PKCS1v15(), hashes.SHA1())


def generate_signed_url(file_key):
    cloudfront_signer = CloudFrontSigner(settings.CLOUDFRONT_PUBLIC_KEY_ID, rsa_signer)
    expiration = datetime.now(timezone.utc) + timedelta(
        minutes=settings.S3_PRESIGNED_URL_TTL
    )

    url = f"https://{settings.CLOUDFRONT_CUSTOM_DOMAIN}/{file_key}"
    signed_url = cloudfront_signer.generate_presigned_url(
        url, date_less_than=expiration
    )
    return signed_url


def generate_signed_url_without(file_key):
    expiration = datetime.now(datetime.timezone.utc) + timedelta(
        minutes=settings.S3_PRESIGNED_URL_TTL
    )
    url = f"https://{settings.CLOUDFRONT_CUSTOM_DOMAIN}/{file_key}"
    signed_url = f"{url}?Expires={int(expiration.timestamp())}&Key-Pair-Id={settings.CLOUDFRONT_PUBLIC_KEY_ID}&Signature={settings.CLOUDFRONT_SIGNATURE}"
    return signed_url
