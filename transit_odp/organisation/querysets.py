from django.contrib.auth import get_user_model
from django.contrib.postgres.aggregates.general import ArrayAgg
from django.db import models
from django.db.models import (
    Case,
    CharField,
    Count,
    F,
    IntegerField,
    Max,
    Min,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.expressions import Exists, RawSQL
from django.db.models.functions import Coalesce, Lower, Substr
from django.db.models.query import Prefetch
from django_hosts import reverse

from config import hosts
from transit_odp.organisation.constants import (
    AVLType,
    DatasetType,
    FaresType,
    FeedStatus,
    TimetableType,
)
from transit_odp.organisation.view_models import GlobalFeedStats
from transit_odp.users.constants import AccountType

User = get_user_model()
# flake8: noqa: E501


class OrganisationQuerySet(models.QuerySet):
    def has_published_datasets(self):
        return self.add_published_dataset_count().filter(published_dataset_count__gt=0)

    def add_org_admin_count(self):
        return self.annotate(
            org_admin_count=Count(
                "user", filter=Q(user__account_type=AccountType.org_admin.value)
            )
        )

    def add_org_staff_count(self):
        return self.annotate(
            org_staff_count=Count(
                "user", filter=Q(user__account_type=AccountType.org_staff.value)
            )
        )

    def add_key_contact_email(self):
        return self.annotate(key_contact_email=F("key_contact__email"))

    def add_registration_complete(self):
        """Annotates queryset with `registration_complete` as `True` if there are active
        users in the organisation or `False` if there are no users.

        Note - this method does not check if there are any actual pending invitations.
        This is assumed to be the case if there are no users.
        """
        return self.annotate(
            registration_complete=Exists(
                User.objects.filter(organisations__in=OuterRef("id"))
            )
        )

    def add_dataset_count(self):
        """Annotates queryset with the total number of related datasets,
        including drafts."""
        return self.annotate(dataset_count=Count("dataset"))

    def add_published_dataset_count_types(self):
        """Annotates queryset with a set of total numbers of related published datasets,
        for Timetables, AVLs and Fares
        """
        from transit_odp.organisation.models import Dataset

        # Need to import here to avoid circular dependency due to
        # organisation and dataset belonging to the organisation app
        base_query = Dataset.objects.filter(
            organisation_id=OuterRef("id"), live_revision__isnull=False
        )

        dataset_type = "dataset_type"
        dataset_types = (TimetableType, AVLType, FaresType)
        timetable_subquery, avl_subquery, fares_subquery = [
            Subquery(
                base_query.filter(dataset_type=type_)
                .values(dataset_type)
                .annotate(total=Count(dataset_type))
                .order_by(dataset_type)
                .values_list("total"),
                output_field=IntegerField(),
            )
            for type_ in dataset_types
        ]

        return self.annotate(
            published_timetable_count=timetable_subquery,
            published_avl_count=avl_subquery,
            published_fares_count=fares_subquery,
        )

    def add_published_dataset_count(self):
        """Annotates queryset with the total number of related datasets,
        excluding drafts."""
        return self.annotate(
            published_dataset_count=Count(
                "dataset", filter=Q(dataset__live_revision__isnull=False)
            )
        )

    def add_last_active(self):
        """Adds the most recent user login datetime."""
        return self.annotate(last_active=Max("users__last_login"))

    def add_invite_sent(self):
        """Adds the datetime that the first invitation was sent to an organisation."""
        return self.annotate(invite_sent=Min("invitation__sent"))

    def add_status(self):
        qs = self.annotate(total_users=Count("users"))
        is_inactive = Q(is_active=False) & Q(total_users__gt=0)
        is_pending = Q(is_active=False) & Q(total_users=0)
        return qs.annotate(
            status=Case(
                When(is_active=True, then=Value("active")),
                When(is_inactive, then=Value("inactive")),
                When(is_pending, then=Value("pending")),
                output_field=CharField(),
            )
        )

    def add_first_letter(self):
        return self.annotate(first_letter=Lower(Substr("name", 1, 1)))


class DatasetQuerySet(models.QuerySet):
    def add_live_data(self):
        """Annotates the queryset with the live revision data"""
        return self.annotate(
            name=F("live_revision__name"),
            description=F("live_revision__description"),
            short_description=F("live_revision__short_description"),
            comment=F("live_revision__comment"),
            upload_file=F("live_revision__upload_file"),
            url_link=F("live_revision__url_link"),
            status=F("live_revision__status"),
            num_of_lines=F("live_revision__num_of_lines"),
            num_of_operators=F("live_revision__num_of_operators"),
            num_of_bus_stops=F("live_revision__num_of_bus_stops"),
            transxchange_version=F("live_revision__transxchange_version"),
            imported=F("live_revision__imported"),
            bounding_box=F("live_revision__bounding_box"),
            publisher_creation_datetime=F("live_revision__publisher_creation_datetime"),
            publisher_modified_datetime=F("live_revision__publisher_modified_datetime"),
            first_expiring_service=F("live_revision__first_expiring_service"),
            last_expiring_service=F("live_revision__last_expiring_service"),
            first_service_start=F("live_revision__first_service_start"),
            last_modified_user=F("live_revision__last_modified_user"),
            published_at=F("live_revision__published_at"),
        )

    def add_admin_area_names(self):
        """Annotate queryset with the comma-separated list of admin names of the
        live revision"""
        # Approach 3 - Couldn't get the window approach to work as the DISTINCT ON
        # clause does not affect the window
        return self.annotate(
            admin_area_names=RawSQL(
                """
                SELECT STRING_AGG(DSQ1A."name", ', ') OVER () AS "admin_area_names"
                FROM (
                    SELECT DISTINCT ON (DSQ1B."name") DSQ1B.name
                    FROM "naptan_adminarea" DSQ1B
                           INNER JOIN "organisation_datasetrevision_admin_areas" DSQ1C
                           ON (DSQ1B."id" = DSQ1C."adminarea_id")
                    WHERE DSQ1C."datasetrevision_id" = ("organisation_dataset"."live_revision_id")
                    ORDER BY DSQ1B."name" ASC
                ) DSQ1A
                LIMIT 1
                """,
                [],
            )
        )

    def add_admin_areas_from_naptan(self):
        return self.annotate(admin_areas=ArrayAgg(""))

    def add_organisation_name(self):
        return self.annotate(organisation_name=F("organisation__name"))

    def add_draft_revisions(self):
        from transit_odp.organisation.models import DatasetRevision

        return self.prefetch_related(
            Prefetch(
                "revisions",
                queryset=DatasetRevision.objects.get_draft(),
                to_attr="draft_revisions",
            ),
        )

    def add_draft_revision_data(self, organisation, dataset_types=None):
        """ Adds """

        if dataset_types is None:
            dataset_types = [DatasetType.TIMETABLE]

        types = ",".join(str(type_.value) for type_ in dataset_types)
        return self.raw(
            """
                SELECT "organisation_dataset".*,
                    b."id" as draft_revision_id,
                    b."status" as status,
                    b."name" as name,
                    b."first_expiring_service" as first_expiring_service,
                    b."num_of_lines" as num_of_lines,
                    b."short_description" as short_description,
                    b."published_at" as published_at
                        FROM "organisation_dataset"
                    JOIN "organisation_organisation"
                        ON ("organisation_dataset"."organisation_id" = %s)
                    CROSS JOIN LATERAL (SELECT *
                       FROM "organisation_datasetrevision"
                        WHERE ("organisation_datasetrevision".is_published = False)
                         and (dataset_id = "organisation_dataset".id)
                         and ("organisation_datasetrevision".status != 'inactive')
                         and ("organisation_datasetrevision".status != 'expired')
                        ) b
                    WHERE ("organisation_dataset".dataset_type IN (%s))
                    GROUP BY "organisation_dataset"."modified", "organisation_dataset"."created", "organisation_dataset".id, b."id", b."status", b.name, b.first_expiring_service, b.num_of_lines, b.short_description, b.published_at
                    ORDER BY "organisation_dataset"."modified" DESC, "organisation_dataset"."created" DESC

                """,
            [organisation.id, types],
        )

    def agg_global_feed_stats(self, dataset_type: DatasetType, organisation_id: int):
        active = self.get_active()

        # count total number of feeds that have expired or soon to expire
        is_expiring = Q(live_revision__status=FeedStatus.expiring.value)
        is_errored = Q(live_revision__status=FeedStatus.error.value)
        feed_warnings = active.filter(is_expiring | is_errored).count()

        # Count total number of datasets (excludes deleted datasets)
        from transit_odp.organisation.models import DatasetRevision

        total_datasets = (
            DatasetRevision.objects.filter(dataset__organisation_id=organisation_id)
            .filter(dataset__dataset_type=dataset_type)
            .aggregate(dataset_count=Count("dataset_id", distinct=True))
        )

        # sum total number of lines across all feeds
        line_count = active.aggregate(
            value=Coalesce(Sum("live_revision__num_of_lines"), Value(0))
        )["value"]

        fare_product_count = active.aggregate(
            value=Coalesce(
                Sum("live_revision__metadata__faresmetadata__num_of_fare_products"),
                Value(0),
            )
        )["value"]

        return GlobalFeedStats(
            line_count=line_count,
            feed_warnings=feed_warnings,
            total_dataset_count=total_datasets["dataset_count"],
            total_fare_products=fare_product_count,
        )

    # Filters

    def get_published(self):
        """Filter queryset to datasets which have a live_revision,
        i.e. a published revision"""

        return self.filter(live_revision__isnull=False)

    def get_active_org(self):
        return self.exclude(organisation__is_active=False)

    def get_dataset_type(self, dataset_type: DatasetType):
        return self.filter(dataset_type=dataset_type)

    def get_active(self):
        """Filter queryset to datasets which have a published revision in a
        non-expired state"""
        exclude_status = [FeedStatus.expired.value, FeedStatus.inactive.value]
        return self.get_published().exclude(live_revision__status__in=exclude_status)

    def search(self, keywords):
        """Searches the dataset and live_revision using keywords"""
        from transit_odp.organisation.models import DatasetRevision

        # The important part is to ensure no duplicate datasets are returned due
        # to search over this many-to-many
        # TODO - add expression indexes to AdminArea name for efficient icontains
        # search, e.g. `CREATE INDEX admin_area_lower_email ON admin_area(upper(name));`
        revisions = (
            DatasetRevision.objects.get_live_revisions()
            .filter(admin_areas__name__icontains=keywords)
            .order_by("id")
            .distinct("id")
            .values("id")
        )

        in_revisions = Q(live_revision__in=revisions)
        name_contains_keywords = Q(live_revision__name__icontains=keywords)
        desc_contains_keywords = Q(live_revision__description__icontains=keywords)
        org_name_contains_keywords = Q(organisation__name__icontains=keywords)

        qs = self.filter(
            in_revisions
            | name_contains_keywords
            | desc_contains_keywords
            | org_name_contains_keywords
        )
        return qs

    def get_remote(self):
        # Note we only want to consider the live_revision's data when determining if
        # its remote. Therefore, exclude any draft revisions
        return self.get_published().exclude(live_revision__url_link="")

    def get_local(self):
        # Note we only want to consider the live_revision's data when determining if
        # its local. Therefore, exclude any draft revisions
        return self.get_published().filter(live_revision__url_link="")

    # Other

    def select_related_live_revision(self, qs=None):
        """
        Prefetch each dataset's live revision for efficient access, i.e.
        when iterating over datasets.

        This method uses prefetch_related under the hood as there is a many-to-one
        rel between Dataset and
        DatasetRevision. However, we use the LiveDatasetRevision proxy model to
        filter this down essentially to a
        one-to-one relationship. The prefetched results are assigned to the
        `_live_revision` attribute. Since this
        contains a result set, the Dataset model defines a property, `live_revision`,
        which returns the first or none.

        :type qs: DatasetRevisionQuerySet Allows prefetch of `DataRevision`s with
        user-supplied annotations.
        """
        from transit_odp.organisation.models import DatasetRevision

        if qs is None:
            qs = DatasetRevision.objects.all()

        # This allows prefetching live revisions with user-provided annotations
        qs = qs.get_live_revisions()

        # we assign it to 'hidden' attribute, '_live_revision', so we can hide the
        # list with a property to return just a single object
        return self.prefetch_related(
            Prefetch("revisions", queryset=qs, to_attr="_live_revision")
        )


class DatasetRevisionQuerySet(models.QuerySet):
    def get_live_revisions(self):
        # This uses a correlated subquery to select the latest published revision
        # for each dataset. This approach
        # is the best compromise between optimal SQL and expressibility in Django.
        # Other methods such as a self-JOIN on
        # a GROUP BY would be very difficult to achieve as you would need a separate
        # view/ORM binding as well as a proxy

        # The generated SQL looks like:
        """
        SELECT *
        FROM "organisation_datasetrevision"
        WHERE "organisation_datasetrevision"."created" = (
            SELECT U0."created"
            FROM "organisation_datasetrevision" U0
            WHERE (U0."dataset_id" = ("organisation_datasetrevision"."dataset_id") AND U0."is_published" = True)
            ORDER BY U0."created" DESC
            LIMIT 1
        )
        """
        return self.filter(dataset__live_revision=F("id"))

    def get_published(self):
        return self.filter(is_published=True)

    def get_live_or_expiring(self):
        # TODO - remove expiring state
        return self.filter(
            Q(status=FeedStatus.live.value) | Q(status=FeedStatus.expiring.value)
        )

    def get_live(self):
        return self.filter(status=FeedStatus.live.value)

    def get_expiring(self):
        return self.filter(status=FeedStatus.expiring.value)

    def get_draft(self):
        return self.filter(is_published=False)

    def get_remote(self):
        return self.exclude(url_link="")

    def get_local(self):
        return self.filter(url_link="")

    def add_stop_count(self, distinct=True):
        """Adds the total number of unique stops served by service patterns when
        distinct=True, else the total number of times a stop is served. Note, using
        distinct=True cannot be used with other aggregations"""
        return self.annotate(
            stop_count=Count("service_patterns__stops", distinct=distinct)
        )

    def add_bus_stop_count(self, distinct=True):
        """Adds the total number of unique stops served by service patterns when
        distinct=True, else the total number of times a stop is served. Note, using
        distinct=True cannot be used with other aggregations"""
        return self.update(
            num_of_bus_stops=Count("service_patterns__stops", distinct=distinct)
        )

    def add_publisher_email(self):
        return self.annotate(user_email=F("published_by__email"))

    def add_admin_area_names(self):
        """Annotate queryset with the comma-separated list of admin names of the
        live revision"""
        return self.annotate(
            admin_area_names=RawSQL(
                """
                SELECT STRING_AGG(DSQ1A."name", ', ') OVER () AS "admin_area_names"
                FROM (
                    SELECT DISTINCT ON (DSQ1B."name") DSQ1B.name
                    FROM "naptan_adminarea" DSQ1B
                           INNER JOIN "organisation_datasetrevision_admin_areas" DSQ1C
                           ON (DSQ1B."id" = DSQ1C."adminarea_id")
                    WHERE DSQ1C."datasetrevision_id" = ("organisation_datasetrevision"."id")
                    ORDER BY DSQ1B."name" ASC
                ) DSQ1A
                LIMIT 1
                """,
                [],
            )
        )

    def add_error_code(self):
        from transit_odp.pipelines.models import DatasetETLTaskResult

        subquery = (
            DatasetETLTaskResult.objects.filter(revision=OuterRef("id"))
            .order_by("-created")
            .values("error_code")[:1]
        )
        return self.annotate(error_code=Coalesce(Subquery(subquery), Value("")))
