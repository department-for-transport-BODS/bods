from django.conf import settings
from django_hosts import host, patterns

ROOT_HOST: str = "www"
DATA_HOST: str = "data"
PUBLISH_HOST: str = "publish"
ADMIN_HOST: str = "admin"

host_patterns = patterns(
    "",
    host(
        rf"{settings.ROOT_SUBDOMAIN}",
        settings.ROOT_URLCONF,
        name=ROOT_HOST,
        callback="transit_odp.common.utils.hosts.host_site",
    ),
    host(
        rf"{settings.DATA_SUBDOMAIN}",
        settings.DATA_URLCONF,
        name=DATA_HOST,
        callback="transit_odp.common.utils.hosts.host_site",
    ),
    host(
        rf"{settings.PUBLISH_SUBDOMAIN}",
        settings.PUBLISH_URLCONF,
        name=PUBLISH_HOST,
        callback="transit_odp.common.utils.hosts.host_site",
    ),
    host(
        rf"{settings.ADMIN_SUBDOMAIN}",
        settings.ADMIN_URLCONF,
        name=ADMIN_HOST,
        callback="transit_odp.common.utils.hosts.host_site",
    ),
)
