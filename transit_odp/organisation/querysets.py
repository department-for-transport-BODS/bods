from datetime import date, datetime, timedelta
from typing import TypeVar

import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.aggregates.general import ArrayAgg, StringAgg
from django.db import models
from django.db.models import (
    Avg,
    BooleanField,
    Case,
    CharField,
    Count,
    DateField,
    ExpressionWrapper,
    F,
    FloatField,
    Func,
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
from django.db.models.expressions import Exists
from django.db.models.functions import (
    Cast,
    Coalesce,
    Concat,
    Floor,
    Substr,
    TruncDate,
    Upper,
)
from django.db.models.query import Prefetch
from django.utils import timezone

from config.hosts import DATA_HOST
from transit_odp.avl.constants import MORE_DATA_NEEDED
from transit_odp.avl.post_publishing_checks.constants import NO_PPC_DATA
from transit_odp.common.utils import reverse_path
from transit_odp.organisation.constants import (
    EXPIRED,
    INACTIVE,
    LIVE,
    ORG_ACTIVE,
    ORG_INACTIVE,
    ORG_NOT_YET_INVITED,
    ORG_PENDING_INVITE,
    AVLType,
    DatasetType,
    FaresType,
    FeedStatus,
    TimetableType,
)
from transit_odp.organisation.view_models import GlobalFeedStats
from transit_odp.users.constants import AccountType

User = get_user_model()
ANONYMOUS = "Anonymous"
GENERAL_LEVEL = "General"
DATASET_LEVEL = "Data set level"

TSeasonalServiceQuerySet = TypeVar(
    "TSeasonalServiceQuerySet", bound="SeasonalServiceQuerySet"
)
TServiceCodeExemptionQuerySet = TypeVar(
    "TServiceCodeExemptionQuerySet", bound="ServiceCodeExemptionQuerySet"
)
TBODSLicenceQuerySet = TypeVar("TBODSLicenceQuerySet", bound="BODSLicenceQuerySet")


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
                User.objects.filter(organisations=OuterRef("id"))
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
        dataset_types = (TimetableType, AVLType, FaresType)
        timetable_count, avl_count, fares_count = [
            Count(
                "dataset",
                filter=Q(
                    dataset__dataset_type=dataset_type,
                    dataset__live_revision__isnull=False,
                ),
                distinct=True,
            )
            for dataset_type in dataset_types
        ]
        return self.annotate(
            published_timetable_count=timetable_count,
            published_avl_count=avl_count,
            published_fares_count=fares_count,
        )

    def add_live_published_dataset_count_types(self):
        """Annotates queryset with a set of total numbers of related published datasets,
        for Timetables, AVLs and Fares
        """
        dataset_types = (TimetableType, AVLType, FaresType)
        timetable_count, avl_count, fares_count = [
            Count(
                "dataset",
                filter=Q(
                    dataset__dataset_type=dataset_type,
                    dataset__live_revision__isnull=False,
                    dataset__live_revision__status="live",
                ),
                distinct=True,
            )
            for dataset_type in dataset_types
        ]
        return self.annotate(
            published_timetable_count=timetable_count,
            published_avl_count=avl_count,
            published_fares_count=fares_count,
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
        qs = self.annotate(
            total_users=Count("users", distinct=True),
            total_invitations=Count("invitation", distinct=True),
        )
        is_inactive = Q(is_active=False) & Q(total_users__gt=0)
        is_pending = Q(is_active=False) & Q(total_users=0) & Q(total_invitations__gt=0)
        is_not_yet_invited = (
            Q(is_active=False) & Q(total_users=0) & Q(total_invitations=0)
        )
        return qs.annotate(
            status=Case(
                When(is_active=True, then=Value(ORG_ACTIVE, output_field=CharField())),
                When(is_inactive, then=Value(ORG_INACTIVE, output_field=CharField())),
                When(
                    is_pending, then=Value(ORG_PENDING_INVITE, output_field=CharField())
                ),
                When(
                    is_not_yet_invited,
                    then=Value(ORG_NOT_YET_INVITED, output_field=CharField()),
                ),
                output_field=CharField(),
            )
        )

    def add_first_letter(self):
        return self.annotate(first_letter=Upper(Substr("name", 1, 1)))

    def add_unregistered_service_count(self):
        unregistered_service_count = Count(
            "dataset",
            filter=Q(
                dataset__live_revision__txc_file_attributes__service_code__startswith="UZ"  # noqa: E501
            ),
        )
        return self.annotate(unregistered_service_count=unregistered_service_count)

    def add_invite_accepted(self):
        return self.annotate(invite_accepted=Min("users__date_joined"))

    def add_number_of_fare_products(self):
        return self.annotate(
            total_fare_products=Coalesce(
                Sum(
                    "dataset__live_revision__metadata__faresmetadata__"
                    "num_of_fare_products",
                    filter=Q(dataset__live_revision__status="live"),
                ),
                Value(0, output_field=IntegerField()),
            )
        )

    def add_number_of_services_valid_operating_date(self):
        today = datetime.today()
        valid_today = Q(
            dataset__live_revision__txc_file_attributes__operating_period_start_date__lte=today,  # noqa: E501
            dataset__live_revision__txc_file_attributes__operating_period_end_date__gte=today,  # noqa: E501
        )
        return self.annotate(
            number_of_services_valid_operating_date=Count(
                "dataset__live_revision__txc_file_attributes__service_code",
                filter=valid_today,
            )
        )

    def add_published_services_with_future_start_date(self):
        today = datetime.today()
        future_start = Q(
            dataset__live_revision__txc_file_attributes__operating_period_start_date__gt=today  # noqa: E501
        )
        return self.annotate(
            published_services_with_future_start_date=Count(
                "dataset", filter=future_start
            )
        )

    def add_nocs_string(self, delimiter=","):
        return self.annotate(
            nocs_string=StringAgg(
                "nocs__noc",
                delimiter,
                distinct=True,
            )
        )

    def add_licence_string(self, delimiter=","):
        return self.annotate(
            licence_string=StringAgg(
                "licences__number",
                delimiter,
                distinct=True,
            )
        )

    def add_number_of_licences(self):
        return self.annotate(number_of_licences=Count("licences", distinct=True))

    def add_permit_holder(self):
        """
        This can really confusing on the frontend when the checkbox is ticked then
        licence_required=False.
        Therefore
        | licence_number | checkbox | licence_required | permit_holder |
        | -------------- | -------- | ---------------- | ------------- |
        | PD0000000136   | empty    | False            | TRUE          |
        | -------------- | -------- | ---------------- | ------------- |
        |                | checked  | True             | FALSE         |
        | -------------- | -------- | ---------------- | ------------- |
        |                | empty    | True/None        | UNKNOWN       |
        | -------------- | -------- | ---------------- | ------------- |
        """
        checked = Q(licence_required=False)
        unchecked = Q(licence_required=True)
        return self.add_number_of_licences().annotate(
            permit_holder=Case(
                When(
                    unchecked & Q(number_of_licences__gt=0),
                    then=Value("TRUE", output_field=CharField()),
                ),
                When(checked, then=Value("FALSE", output_field=CharField())),
                default=Value("UNKNOWN", output_field=CharField()),
                output_field=CharField(),
            )
        )

    def add_total_subscriptions(self):
        """
        Annotates the total number of subscribers onto an organisation.
        * Be careful * with this qs when using in conjunction with other annotations.
        It joins through to organisation -> dataset -> subscribers which are all many
        to many relations. so this will rapidly increase the number of rows in
        interesting ways.
        """
        return self.annotate(total_subscriptions=Count("dataset__subscribers"))

    def get_overall_ppc_score_subquery(self):
        from transit_odp.avl.proxies import AVLDataset

        avl_datasets = (
            AVLDataset.objects.filter(
                organisation=OuterRef("id"),
                dataset_type=AVLType,
            )
            .select_related("organisation")
            .select_related("live_revision")
            .add_avl_compliance_status_cached()
            .add_post_publishing_check_stats()
            .get_active()
            .exclude(avl_compliance_status_cached__in=[MORE_DATA_NEEDED])
            .exclude(percent_matching=NO_PPC_DATA)
            .values("organisation")
            .annotate(
                overall_ppc_score=Avg("percent_matching", output_field=FloatField())
            )
            .values("overall_ppc_score")
        )

        return avl_datasets

    def add_avl_stats(self):
        overall_ppc_score_subquery = self.get_overall_ppc_score_subquery()

        return self.annotate(
            operator_avl_to_timtables_matching_score=Floor(
                Subquery(overall_ppc_score_subquery)
            )
        )

    def add_data_catalogue_fields(self):
        return (
            self.add_status()
            .add_invite_accepted()
            .add_invite_sent()
            .add_last_active()
            .add_permit_holder()
            .add_nocs_string(delimiter=";")
            .add_licence_string(delimiter=";")
            .add_number_of_licences()
            .add_live_published_dataset_count_types()
        )

    def get_organisation_name(self, licence_number):
        from transit_odp.organisation.models import Licence as BODSLicence

        try:
            org_id_list = BODSLicence.objects.filter(number=licence_number).values_list(
                "organisation_id", flat=True
            )
            return (
                self.filter(id__in=org_id_list).values_list("name", flat=True).first()
            )
        except BODSLicence.DoesNotExist:
            return None


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

    def add_modified_status_for_error(self):
        """Annotates the queryset with 'live' status if the status is 'error'"""
        return self.annotate(
            status=Case(
                When(
                    Q(live_revision__status="error"),
                    then=Value("live", output_field=CharField()),
                ),
                default=F("live_revision__status"),
                output_field=CharField(),
            )
        )

    def add_pretty_status(self):
        return self.annotate(
            status=Case(
                When(
                    Q(live_revision__status="live"),
                    then=Value("published", output_field=CharField()),
                ),
                When(
                    Q(live_revision__status="error", dataset_type=AVLType),
                    then=Value("published", output_field=CharField()),
                ),
                default=F("live_revision__status"),
                output_field=CharField(),
            )
        )

    def add_pretty_dataset_type(self):
        # Cant call the attribute pretty_dataset_type because it clashes with model
        # property
        return self.annotate(
            dataset_type_pretty=Case(
                When(
                    Q(dataset_type=TimetableType),
                    then=Value("Timetables", output_field=CharField()),
                ),
                When(
                    Q(dataset_type=AVLType),
                    then=Value("Automatic Vehicle Locations", output_field=CharField()),
                ),
                When(
                    Q(dataset_type=FaresType),
                    then=Value("Fares", output_field=CharField()),
                ),
                output_field=CharField(),
            )
        )

    def add_last_updated_including_avl(self):
        return self.annotate(
            last_updated=Case(
                When(Q(dataset_type=AVLType), then=F("avl_feed_last_checked")),
                default=F("live_revision__published_at"),
            )
        )

    def add_admin_area_names(self):
        """Annotate queryset with the comma-separated list of admin names of the
        live revision"""
        return self.annotate(
            admin_area_names=StringAgg(
                "live_revision__admin_areas__name", ", ", distinct=True
            )
        )

    def add_admin_areas_from_naptan(self):
        return self.annotate(admin_areas=ArrayAgg(""))

    def add_organisation_name(self):
        return self.annotate(organisation_name=F("organisation__name"))

    def add_live_name(self):
        return self.annotate(name=F("live_revision__name"))

    def add_live_filename(self):
        return self.annotate(upload_filename=F("live_revision__upload_file"))

    def add_last_published_by_email(self):
        from transit_odp.organisation.models import DatasetRevision

        subquery = (
            DatasetRevision.objects.get_published()
            .filter(published_by__isnull=False)
            .filter(dataset_id=OuterRef("id"))
            .order_by("-created")
            .values("published_by__email")[:1]
        )
        return self.annotate(last_published_by_email=Subquery(subquery))

    def add_draft_revisions(self):
        from transit_odp.organisation.models import DatasetRevision

        return self.prefetch_related(
            Prefetch(
                "revisions",
                queryset=DatasetRevision.objects.get_draft(),
                to_attr="draft_revisions",
            ),
        )

    def add_errored_draft_flag(self):
        from transit_odp.organisation.models import DatasetRevision

        subquery = (
            DatasetRevision.objects.get_draft()
            .filter(dataset_id=OuterRef("id"))
            .order_by("-created")
            .values("status")[:1]
        )
        qs = self.annotate(
            draft_status=Subquery(subquery),
            has_errored_draft=Case(
                When(draft_status="error", then=Value(True, BooleanField())),
                default=Value(False, BooleanField()),
                output_field=BooleanField(),
            ),
        )
        return qs

    def add_draft_revision_data(self, organisation, dataset_type):
        """
        Adds extra draft revision data to OrganisationDataset used on feed list view
        """
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
                    WHERE ("organisation_dataset".dataset_type = %s)
                    GROUP BY "organisation_dataset"."modified", "organisation_dataset"."created", "organisation_dataset".id, b."id", b."status", b.name, b.first_expiring_service, b.num_of_lines, b.short_description, b.published_at
                    ORDER BY "organisation_dataset"."modified" DESC, "organisation_dataset"."created" DESC

                """,  # noqa: E501
            [organisation.id, dataset_type],
        )

    def add_nocs(self, delimiter=", "):
        return self.annotate(
            nocs=StringAgg(
                "live_revision__txc_file_attributes__national_operator_code",
                delimiter,
                distinct=True,
            )
        )

    def add_profile_nocs(self, delimiter=", "):
        return self.annotate(
            profile_nocs=StringAgg(
                "organisation__nocs__noc",
                delimiter,
                distinct=True,
            )
        )

    def add_service_code(self, delimiter=", "):
        return self.annotate(
            service_codes=StringAgg(
                "live_revision__txc_file_attributes__service_code",
                delimiter,
                distinct=True,
            )
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
            value=Coalesce(
                Sum("live_revision__num_of_lines"),
                Value(0, output_field=IntegerField()),
            )
        )["value"]

        fare_product_count = active.aggregate(
            value=Coalesce(
                Sum("live_revision__metadata__faresmetadata__num_of_fare_products"),
                Value(0, output_field=IntegerField()),
            )
        )["value"]

        return GlobalFeedStats(
            line_count=line_count,
            feed_warnings=feed_warnings,
            total_dataset_count=total_datasets["dataset_count"],
            total_fare_products=fare_product_count,
        )

    def get_published(self):
        """Filter queryset to datasets which have a live_revision,
        i.e. a published revision"""

        return self.filter(live_revision__isnull=False)

    def get_only_active_datasets_bulk_archive(self):
        """
        Filter queryset to exclude datasets which have an inactive status
        """
        exclude_status = FeedStatus.inactive.value
        qs = self.get_published().exclude(live_revision__status=exclude_status)

        return qs

    def get_live_dq_score(self):
        from transit_odp.data_quality.models.report import DataQualityReport

        latest_score_subquery = (
            DataQualityReport.objects.filter(revision_id=OuterRef("live_revision__id"))
            .order_by("-id")
            .values_list("score")[:1]
        )
        return self.annotate(score=Subquery(latest_score_subquery))

    def get_active_org(self):
        return self.exclude(organisation__is_active=False)

    def get_viewable_statuses(self):
        """
        Returns only the statuses that can be viewable by a consumer of BODS,
        e.g. "live" and "inactive" (N.B. only applies to Fares and Timetables).
        """
        return self.get_published().filter(live_revision__status__in=[LIVE, INACTIVE])

    def get_dataset_type(self, dataset_type: DatasetType):
        return self.filter(dataset_type=dataset_type)

    def get_active(self, dataset_type=None):
        """Filter queryset to datasets which have a published revision in a
        non-expired state"""
        exclude_status = [FeedStatus.expired.value, FeedStatus.inactive.value]
        qs = self.get_published().exclude(live_revision__status__in=exclude_status)
        if dataset_type is not None:
            qs = qs.filter(dataset_type=dataset_type)

        return qs

    def search(self, keywords):
        """Searches the dataset and live_revision using keywords"""
        from transit_odp.organisation.models import DatasetRevision

        # The important part is to ensure no duplicate datasets are returned due
        # to search over this many-to-many
        # TODO - add expression indexes to AdminArea name for efficient icontains
        # search, e.g. `CREATE INDEX admin_area_lower_email ON admin_area(upper(name));`
        fares_icontains = Q(
            metadata__faresmetadata__stops__admin_area__name__icontains=keywords
        )
        timetables_icontains = Q(admin_areas__name__icontains=keywords)
        revisions = (
            DatasetRevision.objects.get_live_revisions()
            .filter(timetables_icontains | fares_icontains)
            .order_by("id")
            .distinct("id")
            .values("id")
        )

        location_contains_keywords = Q(live_revision__in=revisions)
        desc_contains_keywords = Q(live_revision__description__icontains=keywords)
        org_name_contains_keywords = Q(organisation__name__icontains=keywords)
        noc_contains_keywords = Q(organisation__nocs__noc__icontains=keywords)

        qs = self.filter(
            location_contains_keywords
            | desc_contains_keywords
            | org_name_contains_keywords
            | noc_contains_keywords
        ).distinct()

        return qs

    def get_remote(self):
        # Note we only want to consider the live_revision's data when determining if
        # its remote. Therefore, exclude any draft revisions
        return self.get_published().exclude(live_revision__url_link="")

    def get_local(self):
        # Note we only want to consider the live_revision's data when determining if
        # its local. Therefore, exclude any draft revisions
        return self.get_published().filter(live_revision__url_link="")

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

    def get_active_remote_datasets(self, dataset_type=None):
        """Return a list of all the datasets that were uploaded via url."""
        qs = (
            self.select_related("organisation")
            .select_related("live_revision")
            .select_related("live_revision__availability_retry_count")
            .get_active()
            .get_remote()
        )
        if dataset_type is not None:
            qs = qs.filter(dataset_type=dataset_type)
        return qs

    def add_fares_report_exists(self):
        from transit_odp.fares_validator.models import FaresValidationResult

        faresReport = FaresValidationResult.objects.filter(
            revision=OuterRef("live_revision_id")
        )

        return self.annotate(has_validation_report=Exists(faresReport))

    def get_existing_fares_dataset_with_no_validation_report(self):
        qs = (
            self.get_active()
            .filter(dataset_type=FaresType)
            .add_fares_report_exists()
            .filter(has_validation_report=False)
        )
        return qs

    def get_existing_fares_dataset(self):
        qs = self.get_active().filter(dataset_type=FaresType)
        return qs

    def get_local_timetables(self):
        return self.get_local().get_active().filter(dataset_type=TimetableType)

    def get_remote_timetables(self):
        return self.get_active_remote_datasets(dataset_type=TimetableType)

    def get_available_remote_timetables(self):
        count_is_zero = Q(live_revision__availability_retry_count__count=0)
        count_is_null = Q(live_revision__availability_retry_count__isnull=True)
        return self.get_remote_timetables().filter(count_is_zero | count_is_null)

    def get_unavailable_remote_timetables(self):
        """Return a list of all the Timetable datasets that were uploaded via url and
        have a retry count greater than zero (have been unavailable)."""
        count_gt_zero = Q(live_revision__availability_retry_count__count__gt=0)
        return self.get_remote_timetables().filter(count_gt_zero)

    def get_remote_fares(self):
        """Return a list of all the Fares datasets that were uploaded via url."""
        return self.get_active_remote_datasets(dataset_type=FaresType)

    def get_available_remote_fares(self):
        count_is_zero = Q(live_revision__availability_retry_count__count=0)
        count_is_null = Q(live_revision__availability_retry_count__isnull=True)
        return self.get_remote_fares().filter(count_is_zero | count_is_null)

    def get_unavailable_remote_fares(self):
        """Return a list of all the Timetable datasets that were uploaded via url and
        have a retry count greater than zero (have been unavailable)."""
        count_gt_zero = Q(live_revision__availability_retry_count__count__gt=0)
        return self.get_remote_fares().filter(count_gt_zero)

    def add_pti_exists(self):
        from transit_odp.data_quality.models.report import PTIObservation

        observations = PTIObservation.objects.filter(
            revision=OuterRef("live_revision_id")
        )
        non_zero_count = Q(live_revision__pti_result__count__gt=0)
        qs = self.annotate(has_pti_observations=Exists(observations))
        return qs.annotate(
            pti_exists=Case(
                When(has_pti_observations=True, then=True),
                When(non_zero_count, then=True),
                default=False,
                output_field=BooleanField(),
            )
        )

    def add_is_after_pti_compliance_date(self):
        filter_date = settings.PTI_START_DATE.replace(tzinfo=pytz.utc)
        is_after_pti_compliance_date = Q(live_revision__created__gt=filter_date)
        return self.annotate(
            is_after_pti_compliance_date=Case(
                When(is_after_pti_compliance_date, then=True),
                default=False,
                output_field=BooleanField(),
            )
        )

    def add_is_live_pti_compliant(self):
        return (
            self.add_pti_exists()
            .add_is_after_pti_compliance_date()
            .annotate(
                is_pti_compliant=Case(
                    When(
                        Q(pti_exists=False, is_after_pti_compliance_date=True),
                        then=True,
                    ),
                    When(
                        Q(pti_exists=True, is_after_pti_compliance_date=True),
                        then=False,
                    ),
                    default=None,
                    output_field=BooleanField(),
                ),
            )
        )

    def add_dataset_download_url(self):
        """
        Annotates the download url to the dataset
        """
        key = 9999999999
        timetables_url = reverse_path(
            "feed-download", kwargs={"pk": key}, host=DATA_HOST
        )
        fares_url = reverse_path(
            "fares-feed-download", kwargs={"pk": key}, host=DATA_HOST
        )
        prefix_timetable_url, suffix_timetable_url = timetables_url.split(str(key))
        prefix_fares_url, suffix_fares_url = fares_url.split(str(key))
        return self.annotate(
            dataset_download_url=Case(
                When(
                    Q(dataset_type=TimetableType),
                    then=Concat(
                        Value(prefix_timetable_url),
                        F("id"),
                        Value(suffix_timetable_url),
                    ),
                ),
                When(
                    Q(dataset_type=FaresType),
                    then=Concat(
                        Value(prefix_fares_url), F("id"), Value(suffix_fares_url)
                    ),
                ),
                default=None,
                output_field=CharField(null=True),
            )
        )

    def add_api_url(self):
        """
        Annotates the v1 api url to the dataset
        """
        key = 9999999999
        timetables_url = reverse_path(
            "api:feed-detail", kwargs={"pk": key}, host=DATA_HOST
        )
        avls_url = reverse_path(
            "api:avldetaildatafeedapi", kwargs={"pk": key}, host=DATA_HOST
        )
        fares_url = reverse_path(
            "api:fares-api-detail", kwargs={"pk": key}, host=DATA_HOST
        )
        prefix_timetable_url, suffix_timetable_url = timetables_url.split(str(key))
        prefix_avl_url, suffix_avl_url = avls_url.split(str(key))
        prefix_fares_url, suffix_fares_url = fares_url.split(str(key))

        return self.annotate(
            api_detail_url=Case(
                When(
                    Q(dataset_type=TimetableType),
                    then=Concat(
                        Value(prefix_timetable_url),
                        F("id"),
                        Value(suffix_timetable_url),
                    ),
                ),
                When(
                    Q(dataset_type=AVLType),
                    then=Concat(
                        Value(prefix_avl_url),
                        F("id"),
                        Value(suffix_avl_url),
                    ),
                ),
                When(
                    Q(dataset_type=FaresType),
                    then=Concat(
                        Value(prefix_fares_url), F("id"), Value(suffix_fares_url)
                    ),
                ),
                default=None,
                output_field=CharField(null=True),
            )
        )

    def add_total_subscriptions(self):
        return self.annotate(total_subscriptions=Count("subscribers"))

    def filter_pti_compliant(self):
        return self.add_is_live_pti_compliant().filter(is_pti_compliant=True)

    def get_compliant_timetables(self):
        qs = (
            self.get_active_org()
            .get_active()
            .select_related("live_revision")
            .filter(dataset_type=TimetableType)
            .filter_pti_compliant()
        )
        return qs

    def get_compliant_fares_validation(self):
        non_zero_count = Q(live_revision__fares_validation_result__count=0)
        return self.annotate(
            is_fares_compliant=Case(
                When(non_zero_count, then=True),
                default=False,
                output_field=BooleanField(),
            )
        )

    def add_ppc_stats(self):
        from transit_odp.avl.models import PostPublishingCheckReport, PPCReportType

        created_at = (
            PostPublishingCheckReport.objects.filter(
                granularity=PPCReportType.WEEKLY.value
            )
            .filter(dataset=OuterRef("pk"))
            .order_by("-created")
        )

        return self.annotate(
            vehicles_completely_matching=Coalesce(
                Subquery(
                    created_at.values("vehicle_activities_completely_matching")[:1]
                ),
                Value(NO_PPC_DATA),
            ),
            vehicles_analysed=Coalesce(
                Subquery(created_at.values("vehicle_activities_analysed")[:1]),
                Value(NO_PPC_DATA),
            ),
            avl_to_timtables_matching_score=Case(
                When(
                    Q(dataset_type=AVLType) & ~Q(live_revision__status=INACTIVE),
                    then=Case(
                        When(
                            vehicles_analysed__gt=0,
                            then=Floor(
                                ExpressionWrapper(
                                    F("vehicles_completely_matching")
                                    * 100.0
                                    / F("vehicles_analysed"),
                                    output_field=FloatField(),
                                )
                            ),
                        ),
                        default=Value(None, output_field=FloatField()),
                    ),
                )
            ),
        )

    def get_overall_data_catalogue_annotations(self):
        return (
            self.get_published()
            .add_organisation_name()
            .add_live_filename()
            .add_live_name()
            .add_profile_nocs(delimiter="; ")
            .add_pretty_status()
            .add_pretty_dataset_type()
            .add_last_updated_including_avl()
            .add_ppc_stats()
            .exclude(live_revision__status=EXPIRED)
        )

    def add_post_publishing_check_stats(self):
        from transit_odp.avl.models import PostPublishingCheckReport, PPCReportType

        created_at = (
            PostPublishingCheckReport.objects.filter(
                granularity=PPCReportType.WEEKLY.value
            )
            .filter(dataset=OuterRef("pk"))
            .order_by("-created")
        )
        return self.annotate(
            vehicles_completely_matching=Coalesce(
                Subquery(
                    created_at.values("vehicle_activities_completely_matching")[:1]
                ),
                Value(NO_PPC_DATA),
            ),
            vehicles_analysed=Coalesce(
                Subquery(created_at.values("vehicle_activities_analysed")[:1]),
                Value(NO_PPC_DATA),
            ),
            percent_matching=Case(
                When(
                    vehicles_analysed__gt=0,
                    then=ExpressionWrapper(
                        F("vehicles_completely_matching")
                        * 100.0
                        / F("vehicles_analysed"),
                        output_field=FloatField(),
                    ),
                ),
                default=float(NO_PPC_DATA),
            ),
        )


class DatasetRevisionQuerySet(models.QuerySet):
    def get_live_revisions(self):
        # This uses a correlated subquery to select the latest published revision
        # for each dataset. This approach
        # is the best compromise between optimal SQL and expressibility in Django.
        # Other methods such as a self-JOIN on
        # a GROUP BY would be very difficult to achieve as you would need a separate
        # view/ORM binding as well as a proxy
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
            admin_area_names=StringAgg("admin_areas__name", ", ", distinct=True)
        )

    def add_error_code(self):
        from transit_odp.pipelines.models import DatasetETLTaskResult

        subquery = (
            DatasetETLTaskResult.objects.filter(revision=OuterRef("id"))
            .order_by("-created")
            .values("error_code")[:1]
        )
        return self.annotate(
            error_code=Coalesce(Subquery(subquery), Value("", output_field=CharField()))
        )

    def add_latest_task_progress(self):
        from transit_odp.pipelines.models import DatasetETLTaskResult

        subquery = Subquery(
            DatasetETLTaskResult.objects.filter(revision=OuterRef("id"))
            .order_by("-created")
            .values("progress")[:1]
        )
        return self.annotate(latest_task_progress=subquery)

    def add_latest_task_status(self):
        from transit_odp.pipelines.models import DatasetETLTaskResult

        subquery = Subquery(
            DatasetETLTaskResult.objects.filter(revision=OuterRef("id"))
            .order_by("-created")
            .values("status")[:1]
        )
        return self.annotate(latest_task_status=subquery)

    def get_stuck_revisions(self):
        now = timezone.now()
        yesterday = now - timedelta(days=1)
        return (
            self.add_latest_task_status()
            .add_latest_task_progress()
            .filter(
                dataset__dataset_type=TimetableType,
                latest_task_progress__lt=100,
                created__lt=yesterday,
            )
            .exclude(
                latest_task_status__in=["FAILURE", "SUCCESS"],
            )
        )


class TXCFileAttributesQuerySet(models.QuerySet):
    def get_active_revisions(self):
        """
        Filter for revisions that are published and not expired or inactive.
        """
        exclude_status = [FeedStatus.expired.value, FeedStatus.inactive.value]
        qs = self.exclude(revision__status__in=exclude_status).filter(
            revision__is_published=True
        )
        return qs

    def get_active_live_revisions(self):
        """
        Filter for revisions that are currently live and are not expired or inactive
        """
        return self.get_active_revisions().filter(
            revision__dataset__live_revision_id=F("revision_id")
        )

    def add_dq_score(self):
        from transit_odp.data_quality.models.report import DataQualityReport

        latest_score_subquery = (
            DataQualityReport.objects.filter(revision_id=OuterRef("revision_id"))
            .order_by("-id")
            .values_list("score")[:1]
        )
        return self.annotate(score=Subquery(latest_score_subquery))

    def add_pti_exists(self):
        from transit_odp.data_quality.models.report import PTIObservation

        observations = PTIObservation.objects.filter(revision=OuterRef("revision_id"))
        non_zero_count = Q(revision__pti_result__count__gt=0)
        qs = self.annotate(has_pti_observations=Exists(observations))
        return qs.annotate(
            pti_exists=Case(
                When(has_pti_observations=True, then=True),
                When(non_zero_count, then=True),
                default=False,
                output_field=BooleanField(),
            )
        )

    def add_is_after_pti_compliance_date(self):
        filter_date = settings.PTI_START_DATE.replace(tzinfo=pytz.utc)
        is_after_pti_compliance_date = Q(revision__created__gt=filter_date)
        return self.annotate(
            is_after_pti_compliance_date=Case(
                When(is_after_pti_compliance_date, then=True),
                default=False,
                output_field=BooleanField(),
            )
        )

    def add_bods_compliant(self):
        return (
            self.add_pti_exists()
            .add_is_after_pti_compliance_date()
            .annotate(
                bods_compliant=Case(
                    When(
                        Q(pti_exists=False, is_after_pti_compliance_date=True),
                        then=True,
                    ),
                    When(
                        Q(pti_exists=True, is_after_pti_compliance_date=True),
                        then=False,
                    ),
                    default=None,
                    output_field=BooleanField(),
                ),
            )
        )

    def add_organisation_name(self):
        return self.annotate(
            organisation_name=F("revision__dataset__organisation__name")
        )

    def add_organisation_id(self):
        organisation_id = F("revision__dataset__organisation_id")
        return self.annotate(organisation_id=organisation_id)

    def add_revision_details(self):
        return self.annotate(
            dataset_id=F("revision__dataset_id"),
            last_updated_date=F("revision__published_at"),
        )

    def add_string_lines(self):
        return self.annotate(
            string_lines=Func(
                F("line_names"),
                Value(" ", output_field=CharField()),
                Value("", output_field=CharField()),
                function="array_to_string",
                output_field=CharField(),
            )
        )

    def get_organisation_data_catalogue(self):
        return (
            self.get_active_live_revisions()
            .add_organisation_id()
            .add_bods_compliant()
            .distinct("service_code")
        )

    def get_active_txc_files(self):
        return (
            self.get_active_live_revisions()
            .add_bods_compliant()
            .add_dq_score()
            .add_revision_details()
            .add_organisation_name()
            .add_string_lines()
            .order_by(
                "service_code",
                "-revision__published_at",
                "-revision_number",
                "-modification_datetime",
                "-operating_period_start_date",
                "-filename",
            )
            .distinct("service_code")
        )

    def get_overall_data_catalogue(self):
        return (
            self.filter(revision=F("revision__dataset__live_revision"))
            .annotate(dataset_id=F("revision__dataset_id"))
            .add_string_lines()
        )

    def filter_by_noc_and_line_name(self, noc, line_name):
        return self.filter(national_operator_code=noc, line_names__contains=[line_name])

    def add_effective_stale_date_last_modified_date(self):
        """Adds the Effective Stale Date: Last Modified Date of file + 1 year."""
        return self.annotate(
            effective_stale_date_last_modified_date=TruncDate(
                ExpressionWrapper(
                    F("modification_datetime") + timedelta(days=365),
                    output_field=DateField(),
                )
            )
        )

    def add_effective_stale_date_end_date(self):
        """Adds the Effective Stale Date: Operating Period End Date - 42 days."""
        return self.annotate(
            effective_stale_date_end_date=TruncDate(
                ExpressionWrapper(
                    F("operating_period_end_date") - timedelta(days=42),
                    output_field=DateField(),
                )
            )
        )

    def add_staleness_dates(self):
        """Adds Effective Stale dates for live revisions."""
        return (
            self.add_effective_stale_date_last_modified_date().add_effective_stale_date_end_date()  # noqa: E501
        )

    def for_revision(self, revision_id: int) -> list:
        """Returns TXCFileAttributes objects for a revision."""
        # today = datetime.today()
        # return self.filter(
        #     Q(revision_id=revision_id)
        #     & Q(operating_period_start_date__lte=today)
        #     & (
        #         Q(operating_period_end_date__isnull=True)
        #         | Q(operating_period_end_date__gte=today)
        #     )
        # )
        return self.filter(
            service_txcfileattributes__revision_id=revision_id
        ).distinct()

        # # Subquery to get the service code of the file with the highest revision number
        # higher_revision_service_code = self.filter(
        #     revision_id=revision_id,
        #     operating_period_start_date__lte=today
        # ).order_by('service_code', '-revision_number').values_list('service_code', flat=True).first()
        # print("Higher revision service code:", higher_revision_service_code)
        # queryset = self.filter(
        #     revision_id=revision_id,
        #     operating_period_start_date__lte=today,
        #     operating_period_end_date__isnull=True
        # )
        # print("Queryset count after filtering by start date and null end date:", queryset.count())

        # queryset = queryset.exclude(service_code=higher_revision_service_code)
        # print("Queryset count after excluding higher revision service code:", queryset.count())

        # return queryset


class ConsumerFeedbackQuerySet(models.QuerySet):
    def add_feedback_type(self):
        return self.annotate(
            feedback_type=Case(
                When(
                    Q(dataset__isnull=True),
                    then=Value(GENERAL_LEVEL, output_field=CharField()),
                ),
                default=Value(DATASET_LEVEL, output_field=CharField()),
            )
        )

    def add_consumer_details(self):
        return self.annotate(
            username=Case(
                When(
                    Q(consumer__isnull=True),
                    then=Value(ANONYMOUS),
                ),
                default=F("consumer__username"),
                output_field=CharField(),
            ),
            email=Case(
                When(
                    Q(consumer__isnull=True),
                    then=Value(ANONYMOUS),
                ),
                default=F("consumer__email"),
                output_field=CharField(),
            ),
        )

    def add_date(self):
        return self.annotate(date=TruncDate("created"))

    def add_total_issues_per_dataset(self):
        counter_subquery = (
            self.values("dataset_id")
            .annotate(count=Count("dataset_id"))
            .filter(dataset_id=OuterRef("dataset_id"))
            .values("count")
        )

        return self.annotate(count=Subquery(counter_subquery))

    def add_dataset_type(self):
        return self.select_related("dataset").annotate(
            dataset_type=Case(
                When(
                    Q(dataset__dataset_type=TimetableType),
                    then=Value("Timetables", output_field=CharField()),
                ),
                When(
                    Q(dataset__dataset_type=AVLType),
                    then=Value("Automatic Vehicle Locations", output_field=CharField()),
                ),
                When(
                    Q(dataset__dataset_type=FaresType),
                    then=Value("Fares", output_field=CharField()),
                ),
                output_field=CharField(),
            )
        )

    def add_organisation_name(self):
        return self.annotate(organisation_name=F("organisation__name"))


class ServiceCodeExemptionQuerySet(models.QuerySet):
    def add_registration_number(self) -> TServiceCodeExemptionQuerySet:
        """Annotate the complete service code including licence prefix"""
        return self.annotate(
            registration_number=Concat(
                "licence__number",
                Value("/"),
                Cast("registration_code", output_field=CharField()),
                output_field=CharField(),
            )
        )

    def add_service_code(self) -> TServiceCodeExemptionQuerySet:
        return self.annotate(
            service_code=Concat(
                "licence__number",
                Value(":"),
                Cast("registration_code", output_field=CharField()),
                output_field=CharField(),
            )
        )

    def add_organisation_id(self) -> TServiceCodeExemptionQuerySet:
        return self.annotate(org_id=F("licence__organisation"))


class BODSLicenceQuerySet(models.QuerySet):
    def add_exempted_service_codes(self) -> TBODSLicenceQuerySet:
        """
        This annotation simply does JOIN on ServiceCodeExemption.
        Be aware that Licence objects in the query will be duplicated
        by each ServiceCodeExemption related.
        """
        self.prefetch_related("service_code_exemptions")
        return self.annotate(
            exempted_service_code=Concat(
                "number",
                Value(":"),
                "service_code_exemptions__registration_code",
                output_field=CharField(),
            )
        )


class SeasonalServiceQuerySet(models.QuerySet):
    def add_registration_number(self) -> TSeasonalServiceQuerySet:
        """The registration number comprises the licence prefix plus
        registration code. This is sometimes referred to as the
        service code.
        """
        return self.annotate(
            registration_number=Concat(
                "licence__number",
                Value("/"),
                Cast("registration_code", output_field=CharField()),
                output_field=CharField(),
            )
        )

    def add_seasonal_status(self) -> TSeasonalServiceQuerySet:
        """Adds whether or not a seasonal service is in season."""
        today = date.today()
        return self.annotate(
            seasonal_status=Case(
                When(
                    Q(start__lte=today) & Q(end__gte=today),
                    then=Value(True, output_field=BooleanField()),
                ),
                default=Value(False, output_field=BooleanField()),
            )
        )

    def get_count_in_organisation(self, org_id: int) -> int:
        """The number of Seasonal services per organisation."""
        return self.filter(licence__organisation_id=org_id).count()
