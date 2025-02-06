import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.shortcuts import get_object_or_404
from django.urls import NoReverseMatch
from django.utils.functional import LazyObject
from django_hosts import reverse_host

logger = logging.getLogger(__name__)


class LazySite(LazyObject):
    def __init__(self, request, *args, **kwargs):
        super(LazySite, self).__init__()
        self.__dict__.update(
            {
                "_host": {
                    "name": request.host.name,
                    "args": args,
                    "kwargs": kwargs,
                    "url": request.build_absolute_uri(),
                }
            }
        )

    def _setup(self):
        host = settings.DEFAULT_HOST
        try:
            host = reverse_host(
                self._host["name"], args=self._host["args"], kwargs=self._host["kwargs"]
            )
        except NoReverseMatch as e:
            logger.error("Reverse url %s not found. Error %s", self._host["url"], e)

        site = get_object_or_404(Site, domain__iexact=host)
        self._wrapped = site


def host_site(request, *args, **kwargs):
    """
    Callback for django-hosts:
    see https://django-hosts.readthedocs.io/en/latest/callbacks.html#
    django_hosts.callbacks.host_site

    Replacing callback 'django_hosts.callbacks.host_site' as their LazySite object
    shadows Site.name
    """
    request.site = LazySite(request, *args, **kwargs)
