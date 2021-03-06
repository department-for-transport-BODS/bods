import logging

from django.db import models

from transit_odp.organisation.querysets import (
    ConsumerFeedbackQuerySet,
    DatasetQuerySet,
    DatasetRevisionQuerySet,
    OrganisationQuerySet,
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
