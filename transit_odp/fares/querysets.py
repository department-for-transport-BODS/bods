from django.db import models
from django.db.models import (
    BooleanField,
    Case,
    CharField,
    F,
    Func,
    Q,
    Subquery,
    Value,
    When,
)

from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.querysets import DatasetQuerySet


class FaresDatasetQuerySet(DatasetQuerySet):
    pass


class FaresNetexFileAttributesQuerySet(models.QuerySet):
    def get_active_published_files(self):
        """
        Filter for revisions that are published and active
        """
        qs = self.filter(
            Q(fares_metadata_id__revision__is_published=True)
            & Q(fares_metadata_id__revision__status=FeedStatus.live.value)
        ).order_by("fares_metadata_id")
        return qs

    def get_filtered_fares(self):
        from transit_odp.fares.models import FaresMetadata

        qs = self.filter(
            fares_metadata_id__in=Subquery(
                FaresMetadata.objects.values_list("datasetmetadata_ptr", flat=True)
            )
        ).order_by("fares_metadata_id")

        return qs

    def add_published_date(self):
        """
        Add date published to BODS as published date
        """
        return self.annotate(
            last_updated_date=F("fares_metadata_id__revision__published_at")
        )

    def add_operator_id(self):
        """
        Add operator Id to result. Dataset organisation_id used as operator_id
        """
        return self.annotate(
            operator_id=F("fares_metadata_id__revision__dataset__organisation_id")
        )

    def add_organisation_name(self):
        """
        Add organisation name to the result
        """
        return self.annotate(
            organisation_name=F(
                "fares_metadata_id__revision__dataset__organisation__name"
            )
        )

    def add_compliance_status(self):
        """
        Gets compliance status from FaresValidationResult model
        """
        count = Q(
            fares_metadata_id__revision__dataset__live_revision__fares_validation_result__count=0
        )
        return self.annotate(
            is_fares_compliant=Case(
                When(count, then=True),
                default=False,
                output_field=BooleanField(),
            )
        )

    def get_active_fares_files(self):
        """
        Filter for revisions that are published and active along
        with other added properties
        """
        return (
            self.get_active_published_files()
            .add_published_date()
            .add_operator_id()
            .add_organisation_name()
            .add_compliance_status()
        )

    def add_revision_and_dataset(self):
        return self.annotate(revision_id=F("fares_metadata_id__revision__id")).annotate(
            dataset_id=F("fares_metadata_id__revision__dataset_id")
        )

    def get_live_revision_data(self):
        return self.filter(
            revision_id=F("fares_metadata_id__revision__dataset__live_revision")
        )

    def add_string_lines(self):
        return self.annotate(
            string_lines=Func(
                F("line_name"),
                Value(";", output_field=CharField()),
                Value("", output_field=CharField()),
                function="array_to_string",
                output_field=CharField(),
            )
        )

    def add_nocs_string(self, delimiter=","):
        return self.annotate(
            nocs_string=Func(
                F("national_operator_code"),
                Value(";", output_field=CharField()),
                Value("", output_field=CharField()),
                function="array_to_string",
                output_field=CharField(),
            )
        )

    def get_fares_overall_catalogue(self):
        return (
            self.add_revision_and_dataset()
            .get_live_revision_data()
            .add_string_lines()
            .add_nocs_string()
        )
