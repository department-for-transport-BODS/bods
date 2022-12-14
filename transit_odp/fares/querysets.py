from transit_odp.organisation.querysets import DatasetQuerySet
from django.db import models
from django.db.models import (
    Q, F, Case, When, BooleanField
)
from transit_odp.organisation.constants import FeedStatus

class FaresDatasetQuerySet(DatasetQuerySet):
    pass


class FaresNetexFileAttributesQuerySet(models.QuerySet):
    def get_active_published_files(self):
        """
        Filter for revisions that are published and active
        """
        qs = self.filter(
            Q(revision__is_published=True) & Q(revision__status=FeedStatus.live.value)
        ).order_by("revision")
        return qs

    def add_published_date(self):
        """
        Add date published to BODS as published date
        """
        return self.annotate(
            last_updated_date=F("revision__published_at")
        )

    def add_operator_id(self):
        """
        Add operator Id to result. Dataset organisation_id used as operator_id
        """
        return self.annotate(
            operator_id=F("revision__dataset__organisation_id")
            )

    def add_organisation_name(self):
        return self.annotate(
            organisation_name=F("revision__dataset__organisation__name")
        )

    def add_compliance_status(self):
        """
        Gets compliance status from FaresValidationResult model
        """
        count = Q(revision__dataset__live_revision__fares_validation_result__count=0)
        return self.annotate(
            is_fares_compliant=Case(
                When(count, then=True),
                default=False,
                output_field=BooleanField(),
            )
        )

    def get_active_fares_files(self):
        """
        Filter for revisions that are published and active along with other added properties
        """
        return (
        self.get_active_published_files()
        .add_published_date()
        .add_operator_id()
        .add_organisation_name()
        .add_compliance_status()
        )
