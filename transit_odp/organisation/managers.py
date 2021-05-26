import logging

from django.db import models

from transit_odp.organisation.querysets import (
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


class LiveDatasetRevisionManager(DatasetRevisionManager):
    def get_queryset(self):
        """Select the latest published revision for each dataset"""
        qs = super().get_queryset()
        return qs.get_live_revisions()
