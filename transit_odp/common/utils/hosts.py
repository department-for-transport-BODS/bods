from django.shortcuts import get_object_or_404
from django.utils.functional import LazyObject
from django_hosts import reverse_host


class LazySite(LazyObject):
    def __init__(self, request, *args, **kwargs):
        super(LazySite, self).__init__()
        self.__dict__.update(
            {"_host": {"name": request.host.name, "args": args, "kwargs": kwargs}}
        )

    def _setup(self):
        host = reverse_host(
            self._host["name"], args=self._host["args"], kwargs=self._host["kwargs"]
        )
        from django.contrib.sites.models import Site

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
