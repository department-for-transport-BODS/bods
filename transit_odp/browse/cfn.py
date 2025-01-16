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
    pem_data = """-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDuK2siSasajxKX
fus/6uNSsjXGTZyqwK9OitRJ8TwkexviRHAnPVXqjy4rH3WlrngaXOnb4jPBIB3R
jQFVNY29tA+a6OkAaicryGX/8jCd60ebsBUZpX0hsZh1YyBPvm0P67i86zmUVH5Y
uZG1nnz68a9YiPvSwnJSWC8y4k4urn87IrElif76I0t/42iSR0J+ZsbTVLR2LpQc
4c3QkqFzHip1enJFkYL3c2VEW84clepcmSYW6zs/Nix+ktBejla2qz1XgMmQfjB3
mkwYv5dJ1pTFKDmfkhUG85WcLG+qHmgZDokZHBCtH80cbJcOeOjXkg4sbcC2G9TF
IV0WE5/LAgMBAAECggEAGSSHQk7hm8On1EtnPU+oINZEXANceyAtQY7hW072qOlA
J9JOvq24cLMdzhqbmlqBPlM5suc9zHD+BN2sWtj09iZYkWNuGYebTAFzVyIzpLAu
Vo6vo433WEO90wKcah6xt8EMNxFj+jczQV2Rtskc64bxGlkXsIerdurtTKNcWowI
KpkkByVev5iKJ6RSqy7dvztqRMYKePDiywiw2Frwy1fIqyloOb0Iw/Kz0dx8ku7L
ZV5HYmVS/NRcvoLCUV0KA1Xb91tIazHBmGWEwPm9neEHxsFnKIoG6HGXNXH8/YQU
icbcmd/+e5wnMIdsNHNff4esB5IzCpcoetzZddcgJQKBgQD43BXLb8tvDonpf00r
/ttncmJ8h4t1J97mRJZLbByrXibik/Sgy3lHg1u7E9dXl6EnXEwM6oAES177x1lZ
mFpos32xbCRH7irAQot6Lxhii7odUChvU0twc4p4eseprd+2n0R+i1TMpK65WvAb
kpNFbCTI0znkKcRcVKiIRgIqfQKBgQD1ANAUVzUaT1i2TiA5mNKFXVd4omWcEjmP
w9oQoJjsP0/mleflmcvEWAvCOFm/C/axMnOEDEsLp3k4arjjNGtYXIsFhO4QIWwS
MombOT7Dh6Nx7uC/n/yVuHMsOd0DuTG403MI9DcvLakyz/yq/+GR69F9P/Vlx18S
Yuq/zpW95wKBgAKVBgTeXBYC6JtrnrleI5inLy5rmZ7VkxKAk66kqId+qpifQGKK
ue9sBX+jbRCTmjB2XLOlmz5wKcQjBWJQml+LvToiDR5R8k+cYSYbZv1exceYFVNS
Ye4AxOcLHxc7np6eeG93sqGM8+ModmVS2ARYYulSh78+T7NFjZocX9lhAoGBANS3
6PHQKb33KFnYiSgY5KeAPILz1O7l7+4/qKSJG1z7N19HxjjWCFIn88WkcV9rfruo
xxzeI4Yx2RC/sFksWQs2Bko7eQquSguer1UDJdhUevdf5Ojbek1wASdj8d3avC3y
AM3EY+llZqNEa+b4FZxBN/jcQC8nJAdttM3mCqL/AoGAEJRsnVXuNr2YuCTu38Gp
Nv9HmIDvcKQpBNlJrFhyCRdu8E0m500+Wm6DsWqFDTiuaEZIqvM1Ji7KvqaQltSL
cYSMZFdhH6kWWjViPwou2KoUqwHjjIu9WL6U5PagcfnI1BFvi/L59aEkOcAZtK0J
YMlan3LFQ7YgtqneaU/lZBs=
-----END PRIVATE KEY-----"""
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
