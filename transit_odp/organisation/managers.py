import logging

from django.db import models

from transit_odp.organisation.querysets import (
    BODSLicenceQuerySet,
    ConsumerFeedbackQuerySet,
    DatasetQuerySet,
    DatasetRevisionQuerySet,
    OrganisationQuerySet,
    SeasonalServiceQuerySet,
    ServiceCodeExemptionQuerySet,
)

logger = logging.getLogger(__name__)


class OrganisationManager(models.Manager.from_queryset(OrganisationQuerySet)):
    pass


class DatasetManager(models.Manager.from_queryset(DatasetQuerySet)):
    pass


class DatasetRevisionManager(models.Manager.from_queryset(DatasetRevisionQuerySet)):
    pass


class ConsumerFeedbackManager(models.Manager.from_queryset(ConsumerFeedbackQuerySet)):
    pass


class ServiceCodeExemptionManager(
    models.Manager.from_queryset(ServiceCodeExemptionQuerySet)
):
    pass


class BODSLicenceManager(models.Manager.from_queryset(BODSLicenceQuerySet)):
    pass


class SeasonalServiceManager(models.Manager.from_queryset(SeasonalServiceQuerySet)):
    pass
