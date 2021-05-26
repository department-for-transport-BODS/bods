from django.db import models

from transit_odp.naptan.querysets import (
    AdminAreaQuerySet,
    LocalityQuerySet,
    StopPointQuerySet,
)


class AdminAreaManager(models.Manager.from_queryset(AdminAreaQuerySet)):
    pass


class StopPointManager(models.Manager.from_queryset(StopPointQuerySet)):
    pass


class LocalityManager(models.Manager.from_queryset(LocalityQuerySet)):
    pass
