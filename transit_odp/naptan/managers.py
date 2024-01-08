from django.db import models

from transit_odp.naptan.querysets import (
    AdminAreaQuerySet,
    LocalityQuerySet,
    StopPointQuerySet,
    FlexibleZoneQuerySet
)


class AdminAreaManager(models.Manager.from_queryset(AdminAreaQuerySet)):
    pass


class StopPointManager(models.Manager.from_queryset(StopPointQuerySet)):
    pass


class LocalityManager(models.Manager.from_queryset(LocalityQuerySet)):
    pass


class FlexibleZoneManager(models.Manager.from_queryset(FlexibleZoneQuerySet)):
    pass
