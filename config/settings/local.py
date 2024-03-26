import os

from transit_odp.common.utils.ip_helper import get_hostname, get_ip_address

from .base import *  # noqa
from .base import ALLOWED_HOSTS, INSTALLED_APPS, MIDDLEWARE, TEMPLATES, env

# In development we want READ_DOT_ENV_FILE to default to True
os.environ["DJANGO_READ_DOT_ENV_FILE"] = os.environ.get(
    "DJANGO_READ_DOT_ENV_FILE", default="True"
)


# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="X61BMLHfhL8X8lPce9YuOVZ5N0YPfLqwFGcKJQPdZaOmBQ3MOvQQ6T3yLNvR0vCC",
)
# Set DD_TRACE_ENABLED to False for local environment
DD_TRACE_ENABLED = env.bool("DD_TRACE_ENABLED", default=False)

# URLS
# ------------------------------------------------------------------------------
# https://django-hosts.readthedocs.io/en/latest/index.html#

# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = [
    "*",
    get_hostname(),
    get_ip_address(),
    "localhost",
    "0.0.0.0",
    "127.0.0.1",
] + ALLOWED_HOSTS

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

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG  # noqa F405

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-host
EMAIL_HOST = env("EMAIL_HOST", default="mailhog")
# https://docs.djangoproject.com/en/dev/ref/settings/#email-port
EMAIL_PORT = 1025

# MIDDLEWARE
# ------------------------------------------------------------------------------
# Set the CORS 'Access-Control-Allow-Origin' header to allow django-debug-toolbar
# to work on subdomains.
CORS_ORIGIN_ALLOW_ALL = True

# django-debug-toolbar
# ------------------------------------------------------------------------------
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
INSTALLED_APPS += ["debug_toolbar"]  # noqa F405
# explicit setup, see https://django-debug-toolbar.readthedocs.io/en/1.0/
# installation.html#explicit-setup
DEBUG_TOOLBAR_PATCH_SETTINGS = False
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
# make sure django-debug-toolbar middleware comes after django-hosts middleware
# see https://django-hosts.readthedocs.io/en/latest/faq.html#does-django-hosts-work-
# with-the-django-debug-toolbar
MIDDLEWARE.insert(
    MIDDLEWARE.index("django.middleware.common.CommonMiddleware") + 1,
    "debug_toolbar.middleware.DebugToolbarMiddleware",
)
#
# MIDDLEWARE.insert(
#     MIDDLEWARE.index("corsheaders.middleware.CorsMiddleware") - 1,
#     "debug_toolbar.middleware.DebugToolbarMiddleware",
# )

# https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": [
        "debug_toolbar.panels.redirects.RedirectsPanel",
        "debug_toolbar.panels.profiling.ProfilingPanel",
    ],
    "SHOW_TEMPLATE_CONTEXT": True,
}
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]
if env("USE_DOCKER") == "yes":
    import socket

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS += [ip[:-1] + "1" for ip in ips]

# django-extensions
# ------------------------------------------------------------------------------
# https://django-extensions.readthedocs.io/en/latest/installation_instructions.html
# configuration
INSTALLED_APPS += [
    "django_extensions",
    "django.contrib.admindocs",
]  # noqa F405

# Celery
# ------------------------------------------------------------------------------
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-always-eager
CELERY_TASK_ALWAYS_EAGER = False
# http://docs.celeryproject.org/en/latest/userguide/configuration.html#task-eager-
# propagates
CELERY_TASK_EAGER_PROPAGATES = False

# Increase age of session cookies to prevent been signed out quickly in development
SESSION_COOKIE_AGE = 1314000  # set to 1 year
SESSION_COOKIE_DOMAIN = ""

# Your stuff...
# ------------------------------------------------------------------------------
DISABLE_NAPTAN_SCHEMA_VALIDATION = True

NOTIFIER = "django"

SHELL_PLUS_IMPORTS = [
    (
        "from transit_odp.users.constants import AgentUserType, DeveloperType, "
        "OrgAdminType, OrgStaffType"
    ),
    "from datetime import datetime, timedelta",
    (
        "from transit_odp.organisation.constants import TimetableType, FaresType, "
        "AVLType"
    ),
    "from transit_odp.avl.proxies import AVLDataset",
]

DATABASES["default"]["ATOMIC_REQUESTS"] = True  # noqa F405
