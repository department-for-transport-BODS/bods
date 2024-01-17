from django.db import models
from django.db.models import Count, F


class AdminAreaQuerySet(models.QuerySet):
    def get_active_org(self):
        return self.exclude(revisions__dataset__organisation__is_active=False)

    def has_published_datasets(self):
        return self.add_published_dataset_count().filter(published_dataset_count__gt=0)

    def add_dataset_count(self):
        """Annotate queryset with the total number of unique datasets which index
        the admin area.

        Note this includes datasets where the admin area is found in previous revisions
        as well as draft revisions.
        """
        return self.annotate(dataset_count=Count("revisions__dataset", distinct=True))

    def add_published_dataset_count(self):
        """Annotate queryset with the total number of unique datasets which index the
        admin area.

        Note this only looks at the latest, published revision of the dataset.
        """
        return self.annotate(
            published_dataset_count=Count("revisions__live_revision_dataset")
        )


class StopPointQuerySet(models.QuerySet):
    def add_district_name(self):
        return self.annotate(district_name=F("locality__district__name"))


class LocalityQuerySet(models.QuerySet):
    def add_district_name(self):
        return self.annotate(district_name=F("district__name"))


class FlexibleZoneQuerySet(models.QuerySet):
    pass
