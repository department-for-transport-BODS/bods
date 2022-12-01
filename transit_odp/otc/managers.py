from django.db import models

from transit_odp.otc.querysets import LicenceQuerySet, OperatorQuerySet, ServiceQuerySet


class ServiceManager(models.Manager.from_queryset(ServiceQuerySet)):
    pass


class LicenceManager(models.Manager.from_queryset(LicenceQuerySet)):
    pass


class OperatorManager(models.Manager.from_queryset(OperatorQuerySet)):
    pass
