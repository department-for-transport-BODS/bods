import logging
from typing import Dict

import config.hosts
from django.conf import settings
from django.contrib.sites.models import Site
from django_hosts import host as Host
from django_hosts import reverse

logger = logging.getLogger(__name__)


def site(request):
    """
    Add site and root site objects as context variables.
    """
    site = root_site = request.site
    if site.id != settings.ROOT_SITE_ID:
        try:
            root_site = Site.objects.get(id=settings.ROOT_SITE_ID)
        except Site.DoesNotExist:
            logger.critical("Root site could not be added to context!")
    return {"site": site, "root_site": root_site}


def host(request):
    """
    Add host and map of host names to the context.
    """
    host: Host = request.host
    hosts: Dict[str, str] = {
        "root": config.hosts.ROOT_HOST,
        "data": config.hosts.DATA_HOST,
        "publish": config.hosts.PUBLISH_HOST,
        "admin": config.hosts.ADMIN_HOST,
    }
    parent_host = settings.PARENT_HOST
    return {"host": host, "hosts": hosts, "parent_host": parent_host}


def js_bundle_init(request):
    """
    Pass init options to JavaScript bundle
    """
    return {
        "js_bundle_init": {
            # Pass api_root since the Django Docker image is being deployed to
            # multiple hosts (we don't know the API root when building the bundle)
            "api_root": reverse("api:api-root", host=config.hosts.DATA_HOST)
        }
    }


def global_settings(request):
    # return any necessary values
    return {
        "GOOGLE_ANALYTICS_KEY": settings.GOOGLE_ANALYTICS_KEY,
        "MAPBOX_KEY": settings.MAPBOX_KEY,
    }
