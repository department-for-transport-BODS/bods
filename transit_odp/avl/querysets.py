from datetime import timedelta

from django.db.models import BooleanField, Q
from django.db.models.aggregates import Count, Sum
from django.db.models.expressions import (
    Case,
    Exists,
    ExpressionWrapper,
    F,
    Func,
    OuterRef,
    Subquery,
    Value,
    When,
)
from django.db.models.fields import CharField, FloatField
from django.utils import timezone

from transit_odp.avl.constants import (
    AWAITING_REVIEW,
    COMPLIANT,
    LOWER_THRESHOLD,
    MORE_DATA_NEEDED,
    NEEDS_ATTENTION_STATUSES,
    NON_COMPLIANT,
    PARTIALLY_COMPLIANT,
    UNDERGOING,
    UPPER_THRESHOLD,
    VALIDATION_TERMINATED,
)
from transit_odp.organisation.constants import ERROR, EXPIRED, INACTIVE
from transit_odp.organisation.querysets import DatasetQuerySet


class AVLDatasetQuerySet(DatasetQuerySet):
    def get_datafeeds_to_validate(self):
        excluded_status = [INACTIVE, EXPIRED]
        feeds = (
            self.add_live_data()
            .get_published()
            .exclude(status__in=excluded_status)
            .select_related("live_revision")
        )
        return feeds

    def add_has_schema_violation_reports(self):
        """
        Annotates a boolean `has_schema_violations` onto the AVLDataset if
        the live_revision has schema violations.
        """
        from transit_odp.avl.models import AVLSchemaValidationReport

        reports = AVLSchemaValidationReport.objects.filter(
            revision=OuterRef("live_revision_id")
        )
        return self.annotate(has_schema_violations=Exists(reports))

    def get_reports_weighted_avg(self, score_type: str = "critical_score"):
        """
        Returns a Subquery of the AVLValidationReport weighted average score for
        the last 7 days worth of reports.
        """
        from transit_odp.avl.models import AVLValidationReport

        last_week = timezone.now().date() - timedelta(days=7)
        reports = (
            AVLValidationReport.objects.filter(
                revision=OuterRef("live_revision_id"), created__gt=last_week
            )
            .annotate(
                total_vehicles=Func("vehicle_activity_count", function="SUM"),
                score_sum=Func(
                    ExpressionWrapper(
                        F(score_type) * F("vehicle_activity_count"),
                        output_field=FloatField(),
                    ),
                    function="SUM",
                ),
                weighted_avg=Case(
                    When(total_vehicles=0, then=Value(0.0, output_field=FloatField())),
                    default=ExpressionWrapper(
                        F("score_sum") / F("total_vehicles"), output_field=FloatField()
                    ),
                ),
            )
            .values("weighted_avg")
        )
        return Subquery(reports)

    def add_weighted_critical_score(self):
        """
        Annotates the weighted average critical score on to the dataset.
        """
        subquery = self.get_reports_weighted_avg("critical_score")
        return self.annotate(avg_critical_score=subquery)

    def add_weighted_non_critical_score(self):
        """
        Annotates the weighted average non-critical score on to the dataset.
        """
        subquery = self.get_reports_weighted_avg("non_critical_score")
        return self.annotate(avg_non_critical_score=subquery)

    def add_critical_exists(self):
        """
        Annotates True or False depending on whether any critical violations
        occur on a datasets last 7 reports.
        """
        from transit_odp.avl.models import AVLValidationReport

        last_week = timezone.now().date() - timedelta(days=7)
        critical_reports = AVLValidationReport.objects.filter(
            revision=OuterRef("live_revision_id"),
            created__gt=last_week,
            critical_count__gt=0,
        )
        return self.annotate(critical_exists=Exists(critical_reports))

    def add_non_critical_exists(self):
        """
        Annotates True or False depending on whether any non critical violations
        occur on a datasets last 7 reports.
        """
        from transit_odp.avl.models import AVLValidationReport

        last_week = timezone.now().date() - timedelta(days=7)
        critical_reports = AVLValidationReport.objects.filter(
            revision=OuterRef("live_revision_id"),
            created__gt=last_week,
            non_critical_count__gt=0,
        )
        return self.annotate(non_critical_exists=Exists(critical_reports))

    def add_avl_report_count(self):
        return self.annotate(
            avl_report_count=Count("live_revision__avl_validation_reports")
        )

    def add_last_seven_days_vehicle_activity_count(self):
        last_week = timezone.now().date() - timedelta(days=7)

        return self.annotate(
            weekly_vehicle_journey_count=Sum(
                "live_revision__avl_validation_reports__vehicle_activity_count",
                filter=Q(live_revision__avl_validation_reports__created__gt=last_week),
            )
        )

    def add_is_post_seven_days(self, from_yesterday=False):
        if not from_yesterday:
            seven_days_ago = timezone.now().date() - timedelta(days=7)
        else:
            seven_days_ago = timezone.now().date() - timedelta(days=8)

        return self.add_first_report_date().annotate(
            post_seven_days=Case(
                When(first_report_date__isnull=True, then=False),
                When(first_report_date__lte=seven_days_ago, then=True),
                default=False,
                output_field=BooleanField(),
            )
        )

    def add_critical_lower_threshold(self):
        from transit_odp.avl.models import AVLValidationReport

        last_week = timezone.now().date() - timedelta(days=7)
        critical_reports = AVLValidationReport.objects.filter(
            revision=OuterRef("live_revision_id"),
            created__gt=last_week,
            critical_score__lt=LOWER_THRESHOLD,
        )
        return self.annotate(under_lower_threshold=Exists(critical_reports))

    def add_first_report_date(self):
        """
        Adds the date that the first report with errors occurred.
        """
        from transit_odp.avl.models import AVLValidationReport

        reports = (
            AVLValidationReport.objects.filter(
                revision=OuterRef("live_revision_id"),
            )
            .order_by("created")
            .values("created")[:1]
        )
        return self.annotate(first_report_date=reports)

    def add_first_error_date(self):
        """
        Adds the date that the first report with errors occurred.
        """
        from transit_odp.avl.models import AVLValidationReport

        last_week = timezone.now().date() - timedelta(days=7)
        error_exists = Q(non_critical_count__gt=0) | Q(critical_count__gt=0)
        reports = (
            AVLValidationReport.objects.filter(
                error_exists,
                revision=OuterRef("live_revision_id"),
                created__gt=last_week,
            )
            .order_by("id")
            .values("created")[:1]
        )
        return self.annotate(first_error_date=reports)

    def add_avl_compliance_status(self):
        """
        Adds the avl compliance level to the AVLDataset based on the following rules.

        status = INACTIVE => VALIDATION_TERMINATED

        First 7 days:
            critical_count = 0 and non_critical_count = 0 => UNDERGOING
            critical_count > 0 or non_critical_count > 0 => AWAITING_REVIEW

        Day 8 onwards:
            0 vehicle journeys => MORE_DATA_NEEDED
            Any critical_score < 0.2 in the last 7 days => NON_COMPLIANT
            avg_non_critical_score and avg_critical_score > 0.7 => COMPLIANT
            avg_critical_score > 0.7 and  avg_non_critical_score < 0.7
             => PARTIALLY_COMPLIANT
            avg_critical_score < 0.7 => NON_COMPLIANT
        """
        qs = (
            self.add_avl_report_count()
            .add_is_post_seven_days()
            .add_critical_lower_threshold()
            .add_non_critical_exists()
            .add_critical_exists()
            .add_weighted_critical_score()
            .add_weighted_non_critical_score()
            .add_last_seven_days_vehicle_activity_count()
        )

        pre_7_days = Q(post_seven_days=False)
        post_7_days = Q(post_seven_days=True)
        has_errors = Q(non_critical_exists=True) | Q(critical_exists=True)
        above_critical_threshold = Q(avg_critical_score__gte=UPPER_THRESHOLD)
        above_non_critical_threshold = Q(avg_non_critical_score__gte=UPPER_THRESHOLD)
        partially_compliant = above_critical_threshold & ~above_non_critical_threshold
        compliant = above_critical_threshold & above_non_critical_threshold

        return qs.annotate(
            avl_compliance=Case(
                When(
                    Q(live_revision__status=INACTIVE),
                    then=Value(VALIDATION_TERMINATED, output_field=CharField()),
                ),
                When(
                    pre_7_days & ~has_errors,
                    then=Value(UNDERGOING, output_field=CharField()),
                ),
                When(
                    pre_7_days & has_errors,
                    then=Value(AWAITING_REVIEW, output_field=CharField()),
                ),
                When(
                    post_7_days & Q(weekly_vehicle_journey_count=0),
                    then=Value(MORE_DATA_NEEDED, output_field=CharField()),
                ),
                When(
                    post_7_days & Q(under_lower_threshold=True),
                    then=Value(NON_COMPLIANT, output_field=CharField()),
                ),
                When(
                    post_7_days & compliant,
                    then=Value(COMPLIANT, output_field=CharField()),
                ),
                When(
                    post_7_days & ~above_critical_threshold,
                    then=Value(NON_COMPLIANT, output_field=CharField()),
                ),
                When(
                    post_7_days & partially_compliant,
                    then=Value(PARTIALLY_COMPLIANT, output_field=CharField()),
                ),
                default=Value(UNDERGOING, output_field=CharField()),
                output_field=CharField(),
            )
        )

    def add_old_avl_compliance_status(self):
        """
        Adds the avl compliance level to the AVLDataset based on the following rules.

        First 7 days:
            critical_count = 0 and non_critical_count = 0 => UNDERGOING
            critical_count > 0 or non_critical_count > 0 => AWAITING_REVIEW

        Day 8 onwards:
            0 vehicle journeys => MORE_DATA_NEEDED
            Any critical_score < 0.2 in the last 7 days => NON_COMPLIANT
            avg_non_critical_score and avg_critical_score >= 0.7 => COMPLIANT
            avg_critical_score >= 0.7 and  avg_non_critical_score < 0.7
             => PARTIALLY_COMPLIANT
            avg_critical_score < 0.7 => NON_COMPLIANT
        """
        qs = (
            self.add_avl_report_count()
            .add_is_post_seven_days(from_yesterday=True)
            .add_critical_lower_threshold()
            .add_non_critical_exists()
            .add_critical_exists()
            .add_weighted_critical_score()
            .add_weighted_non_critical_score()
            .add_last_seven_days_vehicle_activity_count()
        )
        pre_7_days = Q(post_seven_days=False)
        post_7_days = Q(post_seven_days=True)
        has_errors = Q(non_critical_exists=True) | Q(critical_exists=True)
        above_critical_threshold = Q(avg_critical_score__gte=UPPER_THRESHOLD)
        above_non_critical_threshold = Q(avg_non_critical_score__gte=UPPER_THRESHOLD)
        partially_compliant = above_critical_threshold & ~above_non_critical_threshold
        compliant = above_critical_threshold & above_non_critical_threshold

        return qs.annotate(
            old_avl_compliance=Case(
                When(
                    pre_7_days & ~has_errors,
                    then=Value(UNDERGOING, output_field=CharField()),
                ),
                When(
                    pre_7_days & has_errors,
                    then=Value(AWAITING_REVIEW, output_field=CharField()),
                ),
                When(
                    post_7_days & Q(weekly_vehicle_journey_count=0),
                    then=Value(MORE_DATA_NEEDED, output_field=CharField()),
                ),
                When(
                    post_7_days & Q(under_lower_threshold=True),
                    then=Value(NON_COMPLIANT, output_field=CharField()),
                ),
                When(
                    post_7_days & compliant,
                    then=Value(COMPLIANT, output_field=CharField()),
                ),
                When(
                    post_7_days & ~above_critical_threshold,
                    then=Value(NON_COMPLIANT, output_field=CharField()),
                ),
                When(
                    post_7_days & partially_compliant,
                    then=Value(PARTIALLY_COMPLIANT, output_field=CharField()),
                ),
                default=Value(UNDERGOING, output_field=CharField()),
                output_field=CharField(),
            )
        )

    def search(self, keyword):
        from transit_odp.organisation.models import Organisation

        has_nocs = Q(nocs__noc__icontains=keyword)
        has_name = Q(name__icontains=keyword)
        has_keyword = Q(live_revision__description__icontains=keyword)
        organisations = Organisation.objects.filter(has_name | has_nocs).distinct()
        contain_org = Q(organisation__in=organisations)
        return self.filter(contain_org | has_keyword)

    def get_location_data_catalogue(self):
        return (
            self.get_published()
            .get_active()
            .add_live_name()
            .add_organisation_name()
            .add_avl_compliance_status()
        )

    def get_needs_attention_count(self) -> int:
        """
        Returns the number of AVL Datasets that have a compliance status that
        requires attention.
        """
        count = (
            self.add_avl_compliance_status()
            .filter(
                Q(avl_compliance__in=NEEDS_ATTENTION_STATUSES)
                | Q(live_revision__status=ERROR)
            )
            .count()
        )

        return count
