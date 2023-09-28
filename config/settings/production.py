# MEDIA
# ------------------------------------------------------------------------------
from .base import *  # noqa
from .base import DATABASES, INSTALLED_APPS, MIDDLEWARE, env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env("DJANGO_SECRET_KEY")
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHE_TIMEOUT = 60 * 55  # 55 minutes
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "TIMEOUT": CACHE_TIMEOUT,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": "cache",
    }
}

# DATABASES
# ------------------------------------------------------------------------------
DATABASES["default"] = env.db("DATABASE_URL")  # noqa F405
DATABASES["default"]["ATOMIC_REQUESTS"] = True  # noqa F405
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=60)  # noqa F405


# SECURITY CONFIGURATION
# ------------------------------------------------------------------------------
# See https://docs.djangoproject.com/en/dev/ref/middleware/#module-django.middleware.security # NOQA: E501
# and https://docs.djangoproject.com/en/dev/howto/deployment/checklist/#run-manage-py-check-deploy # NOQA: E501

# Django is deployed behind a frontend proxy server which does SSL termination
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-ssl-redirect
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=False)
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-secure
SESSION_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/3.0/ref/settings/#std:setting-SESSION_COOKIE_AGE
SESSION_COOKIE_AGE = 30 * 60  # set to 30 minutes
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-secure
CSRF_COOKIE_SECURE = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = True

# https://docs.djangoproject.com/en/dev/topics/security/#ssl-https
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-seconds
SECURE_HSTS_SECONDS = 365 * 24 * 60 * 60  # set to 1 year
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-include-subdomains
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False
)
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-hsts-preload
SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=False)
# https://docs.djangoproject.com/en/dev/ref/middleware/#x-content-type-options-nosniff
SECURE_CONTENT_TYPE_NOSNIFF = env.bool(
    "DJANGO_SECURE_CONTENT_TYPE_NOSNIFF", default=False
)
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-browser-xss-filter
SECURE_BROWSER_XSS_FILTER = False
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = "DENY"

AWS_ACCESS_KEY_ID = env("DJANGO_AWS_ACCESS_KEY_ID", default=None)
# https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html#settings
AWS_SECRET_ACCESS_KEY = env("DJANGO_AWS_SECRET_ACCESS_KEY", default=None)
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

# Bucket for SIRI VM cached files
AWS_SIRIVM_STORAGE_BUCKET_NAME = env("DJANGO_AWS_SIRIVM_STORAGE_BUCKET_NAME")

# Bucket for SIRI SX cached files
AWS_SIRISX_STORAGE_BUCKET_NAME = env("DJANGO_AWS_SIRISX_STORAGE_BUCKET_NAME")

# Bucket for intended dataset maintenance files
AWS_DATASET_MAINTENANCE_STORAGE_BUCKET_NAME = env("AWS_DATASET_MAINTENANCE_STORAGE_BUCKET_NAME")


# STATIC
# ------------------------
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_FILE_STORAGE = "config.custom_storage.MediaRootS3Boto3Storage"
MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/"

# WhiteNoise
# ------------------------------------------------------------------------------
# http://whitenoise.evans.io/en/latest/django.html#enable-whitenoise
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa F405


# EMAIL
# ------------------------------------------------------------------------------
# GB - setting to DummyBackend to disable SMTP in production
# (all messages sent via GovUK Notify)
EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"

# # SMTP Backend: https://docs.djangoproject.com/en/2.1/topics/email/#smtp-backend
# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# # https://docs.djangoproject.com/en/dev/ref/settings/#email-host
# EMAIL_HOST = env("DJANGO_EMAIL_HOST")
# # https://docs.djangoproject.com/en/dev/ref/settings/#email-port
# EMAIL_PORT = env("DJANGO_EMAIL_PORT")
# # https://docs.djangoproject.com/en/2.1/ref/settings/#std:setting-EMAIL_HOST_USER
# EMAIL_HOST_USER = env("DJANGO_EMAIL_HOST_USER")
# # https://docs.djangoproject.com/en/2.1/ref/settings/#std:setting-EMAIL_HOST_PASSWORD
# EMAIL_HOST_PASSWORD = env("DJANGO_EMAIL_HOST_PASSWORD")
# # https://docs.djangoproject.com/en/2.1/ref/settings/#std:setting-EMAIL_USE_TLS
# EMAIL_USE_TLS = True


# Gunicorn
# ------------------------------------------------------------------------------
INSTALLED_APPS += ["gunicorn"]  # noqa F405


# Your stuff...
# ------------------------------------------------------------------------------
NOTIFIER = "govuk-notify"
GENERIC_TEMPLATE_ID = env("GENERIC_TEMPLATE_ID")

if env.bool("DJANGO_SHOW_DEBUG_TOOLBAR", default=False):
    # django-debug-toolbar
    # ------------------------------------------------------------------------------
    # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites # NOQA: E501

    # Enable DDT from production server
    # see https://stackoverflow.com/a/40165867/5221078

    INTERNAL_IPS = env.list("DJANGO_INTERNAL_IPS", default=[])
    # put your client IP address(es) here (not server IP!),
    # e.g. `DJANGO_INTERNAL_IPS=IP1,IP2,IP3`

    def show_toolbar_callback(request):
        """Allows DDT to be displayed without DEBUG mode being turned on.
        The toolbar is only displayed if the request
        address is found in INTERNAL_IPS.
        You can add your own IP with the DJANGO_INTERNAL_IPS env variable
        """
        return True
        # return (
        #     not request.is_ajax()
        #     and request.META.get("REMOTE_ADDR", None) in INTERNAL_IPS
        # )

    INSTALLED_APPS += ["debug_toolbar"]  # noqa F405
    # explicit setup,
    # see https://django-debug-toolbar.readthedocs.io/en/1.0/installation.html#explicit-setup # NOQA: E501
    DEBUG_TOOLBAR_PATCH_SETTINGS = False
    # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
    # make sure django-debug-toolbar middleware comes after django-hosts middleware
    # see https://django-hosts.readthedocs.io/en/latest/faq.html#does-django-hosts-work-with-the-django-debug-toolbar # NOQA: E501
    MIDDLEWARE.insert(
        MIDDLEWARE.index("django.middleware.common.CommonMiddleware") + 1,
        "debug_toolbar.middleware.DebugToolbarMiddleware",
    )

    # https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config # NOQA: E501
    DEBUG_TOOLBAR_CONFIG = {
        "DISABLE_PANELS": ["debug_toolbar.panels.redirects.RedirectsPanel"],
        "SHOW_TEMPLATE_CONTEXT": True,
        "SHOW_TOOLBAR_CALLBACK": show_toolbar_callback,
    }
