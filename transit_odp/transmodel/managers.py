from django.db import models

from transit_odp.transmodel.querysets import (
    ServicePatternQuerySet,
    ServicePatternStopQuerySet,
)


class ServicePatternStopManager(
    models.Manager.from_queryset(ServicePatternStopQuerySet)
):
    pass


class ServicePatternManager(models.Manager.from_queryset(ServicePatternQuerySet)):
    pass
