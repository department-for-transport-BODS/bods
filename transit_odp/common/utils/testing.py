import config.hosts
import django_hosts
from django_hosts import reverse_host
from rest_framework.test import APITestCase as BaseAPITestCase


class APITestCase(BaseAPITestCase):
    def __init__(self, host_name=config.hosts.ROOT_HOST):
        super().__init__()
        self.host_name = host_name
        self.HTTP_HOST = reverse_host(host_name)

    @property
    def client(self):
        return self._client

    @client.setter
    def client(self, value):
        value.defaults.setdefault("SERVER_NAME", self.HTTP_HOST)
        self._client = value


def reverse(*args, **kwargs):
    kwargs.setdefault("host", config.hosts.ROOT_HOST)
    return django_hosts.resolvers.reverse(*args, **kwargs)
