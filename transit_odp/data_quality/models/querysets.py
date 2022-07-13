from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import CharField, F, OuterRef, Subquery, TextField
from django.db.models.aggregates import Min
from django.db.models.expressions import Func, RawSQL, Value
from django.db.models.functions.comparison import Greatest
from django.db.models.functions.text import Concat


class TimingPatternStopQueryset(models.QuerySet):
    def add_stop_name(self):
        return self.select_related("service_pattern_stop__stop").annotate(
            name=F("service_pattern_stop__stop__name")
        )

    def add_position(self):
        return self.select_related("service_pattern_stop").annotate(
            position=F("service_pattern_stop__position")
        )


class TimingPatternLineQuerySet(models.QuerySet):
    def add_line(self):
        return self.annotate(line=F("timing_pattern__service_pattern__service__name"))


class VehicleJourneyQueryset(models.QuerySet):
    def add_line_name(self):
        return self.select_related("timing_pattern__service_pattern__service").annotate(
            line=F("timing_pattern__service_pattern__service__name")
        )

    def add_first_date(self):
        """Add a the earliest date in the `dates` ArrayField."""
        return self.annotate(
            first_date=RawSQL("select min(x) from unnest(dates) as x", ())
        )

    def add_first_stop(self):
        ServicePatternStop = ContentType.objects.get(
            app_label="data_quality", model="servicepatternstop"
        ).model_class()
        from_stop_name_subquery = ServicePatternStop.objects.filter(
            service_pattern_id=OuterRef("timing_pattern__service_pattern_id"),
            position=0,
        ).values_list("stop__name")
        return self.annotate(
            first_stop_name=Subquery(from_stop_name_subquery, output_field=CharField()),
        )


class DataQualityReportQueryset(models.QuerySet):
    def add_number_of_lines(self):
        return self.select_related("revision").annotate(
            no_of_lines=F("revision__num_of_lines")
        )


class IncorrectNOCQuerySet(models.QuerySet):
    def add_message(self):
        return self.annotate(
            message=Concat(
                "noc",
                Value(
                    " is specified in the dataset but not assigned to your "
                    "organisation",
                    output_field=TextField(),
                ),
            )
        )


class JourneyStopInappropriateQuerySet(models.QuerySet):
    def add_line(self):
        return self.annotate(line=Min("stop__service_patterns__service__name"))

    def add_message(self):
        message_args = (
            Value("Includes stop ", output_field=CharField()),
            "stop__name",
            Value(" of type ", output_field=CharField()),
            "stop__type",
        )
        return self.annotate(message=Concat(*message_args, output_field=CharField()))


class StopMissingNaptanQuerySet(models.QuerySet):
    def add_message(self):
        message = "There is at least one journey where stop(s) are not in NaPTAN"
        return self.annotate(message=Value(message, CharField()))

    def add_line(self):
        # Using Min to make the first line name appear
        return self.annotate(line=Min("service_patterns__service__name"))

    def exclude_null_service_patterns(self):
        return self.exclude(stop__service_patterns__isnull=True)

    def get_csv_queryset(self):
        """A queryset to be applied by only in the CSV generation code."""
        return self.exclude_null_service_patterns()


class TimingMissingPointQueryset(TimingPatternLineQuerySet):
    def add_message(self):
        return (
            self.annotate(
                message=Concat(
                    Value("Timing point after ", output_field=CharField()),
                    "timings__service_pattern_stop__stop__name",
                    Value(" is missing", output_field=CharField()),
                )
            )
            .order_by("timing_pattern_id")
            .distinct("timing_pattern_id")
        )


class TimingQuerySet(models.QuerySet):
    def add_line(self):
        return self.annotate(line=F("timing_pattern__service_pattern__service__name"))


class JourneyQuerySet(models.QuerySet):
    def add_first_stop(self):
        from transit_odp.data_quality.models import VehicleJourney

        vj_subquery = (
            VehicleJourney.objects.filter(id=OuterRef("vehicle_journey_id"))
            .add_first_stop()
            .values_list("first_stop_name", flat=True)
        )
        return self.annotate(first_stop_name=Subquery(vj_subquery))

    def add_line(self):
        return self.annotate(
            line=F("vehicle_journey__timing_pattern__service_pattern__service__name")
        )

    def add_first_date(self):
        from transit_odp.data_quality.models import VehicleJourney

        subquery = (
            VehicleJourney.objects.filter(id=OuterRef("vehicle_journey_id"))
            .add_first_date()
            .values_list("first_date", flat=True)
        )
        return self.annotate(first_date=Subquery(subquery))


class TimingDropOffQuerySet(TimingQuerySet):
    def add_message(self):
        return self.annotate(
            message=Value(
                "There is at least one journey where the last stop is designated as "
                "pick up only",
                output_field=CharField(),
            )
        )


class TimingPickUpQuerySet(TimingQuerySet):
    def add_message(self):
        return self.annotate(
            message=Value(
                "There is at least one journey where the first stop is designated as "
                "set down only",
                output_field=CharField(),
            )
        )


class FastTimingQuerySet(TimingPatternLineQuerySet):
    def add_message(self):
        message = (
            "There is at least one journey with fast timing link between timing points"
        )

        return self.annotate(message=Value(message, CharField()))


class SlowTimingQuerySet(TimingPatternLineQuerySet):
    def add_message(self):
        message = (
            "There is at least one journey with slow timing link between timing points"
        )
        return self.annotate(
            message=Value(message, CharField()),
        )


class JourneyDateRangeBackwardsQuerySet(JourneyQuerySet):
    def add_message(self):
        return self.add_first_stop().annotate(
            message=Concat(
                Func(
                    F("vehicle_journey__start_time"),
                    Value("HH24:MI", output_field=CharField()),
                    function="to_char",
                ),
                Value(" from ", output_field=CharField()),
                "first_stop_name",
                Value(" on ", output_field=CharField()),
                Func(
                    F("start"),
                    Value("DD/MM/YYYY", output_field=CharField()),
                    function="to_char",
                ),
                Value(" has a backwards date range", output_field=CharField()),
                output_field=CharField(),
            )
        )


class JourneyWithoutHeadsignQuerySet(JourneyQuerySet):
    def add_message(self):
        return (
            self.add_first_stop()
            .add_first_date()
            .annotate(
                message=Concat(
                    Func(
                        F("vehicle_journey__start_time"),
                        Value("HH24:MI", output_field=CharField()),
                        function="to_char",
                    ),
                    Value(" from ", output_field=CharField()),
                    "first_stop_name",
                    Value(" on ", output_field=CharField()),
                    Func(
                        F("first_date"),
                        Value("DD/MM/YYYY", output_field=CharField()),
                        function="to_char",
                    ),
                    Value(
                        " is missing a destination display", output_field=CharField()
                    ),
                    output_field=CharField(),
                ),
            )
        )


class ServiceLinkMissingStopQuerySet(models.QuerySet):
    def add_message(self):
        return self.annotate(
            message=Concat(
                Value("Might have a missing stop between ", output_field=CharField()),
                "service_link__from_stop__name",
                Value(" and ", output_field=CharField()),
                "service_link__to_stop__name",
                output_field=CharField(),
            )
        )

    def add_line(self):
        from transit_odp.data_quality.models import ServicePattern

        subquery = (
            ServicePattern.objects.filter(id=OuterRef("service_link__service_patterns"))
            .order_by("ito_id")
            .values_list("service__name")[:1]
        )

        return self.annotate(line=Subquery(subquery)).distinct("id")


class TimingFirstQuerySet(TimingPatternLineQuerySet):
    def add_message(self):
        return self.annotate(
            message=Value(
                "There is at least one journey where the first stop is not a timing "
                "point",
                output_field=CharField(),
            )
        )


class TimingLastQuerySet(TimingPatternLineQuerySet):
    def add_message(self):
        return self.annotate(
            message=Value(
                "There is at least one journey where the last stop is not a timing "
                "point",
                output_field=CharField(),
            )
        )


class SlowLinkQuerySet(TimingPatternLineQuerySet):
    def add_message(self):
        return self.annotate(
            message=Concat(
                Value("Slow running time between ", output_field=CharField()),
                "service_links__from_stop__name",
                Value(" and ", output_field=CharField()),
                "service_links__to_stop__name",
                output_field=CharField(),
            ),
        )


class FastLinkQuerySet(TimingPatternLineQuerySet):
    def add_message(self):
        return self.annotate(
            message=Concat(
                Value("Fast running time between ", output_field=CharField()),
                "service_links__from_stop__name",
                Value(" and ", output_field=CharField()),
                "service_links__to_stop__name",
                output_field=CharField(),
            ),
        )


class JourneyDuplicateQuerySet(JourneyQuerySet):
    def add_message(self):
        return (
            self.add_first_stop()
            .add_first_date()
            .annotate(
                message=Concat(
                    Func(
                        F("vehicle_journey__start_time"),
                        Value("HH24:MI", output_field=CharField()),
                        function="to_char",
                    ),
                    Value(" from ", output_field=CharField()),
                    "first_stop_name",
                    Value(" on ", output_field=CharField()),
                    Func(
                        F("first_date"),
                        Value("DD/MM/YYYY", output_field=CharField()),
                        function="to_char",
                    ),
                    Value(
                        " has at least one duplicate journey", output_field=CharField()
                    ),
                    output_field=CharField(),
                ),
            )
        )

    def apply_deduplication(self):
        # TODO de-duplication needs to be done in pipeline adding count to the model
        #  -------------------
        # | id | x | y | max |
        # |-------------------
        # | 1  | 2 | 3 |  3  |
        # | 2  | 3 | 2 |  3  |
        #
        # To perform the deduplication we annotate the query set with the max of
        # x and y this means we can then use distinct to give us only one vehicle
        # journey.
        # see #BODP-2237 for more details.
        return self.annotate(
            max=Greatest(F("duplicate_id"), F("vehicle_journey_id")),
        ).distinct("max")


class JourneyConflictQuerySet(JourneyQuerySet):
    def add_conflict_stop(self):
        from transit_odp.data_quality.models import VehicleJourney

        vj_subquery = (
            VehicleJourney.objects.filter(id=OuterRef("conflict_id"))
            .add_first_stop()
            .values_list("first_stop_name", flat=True)
        )
        return self.annotate(conflict_stop_name=Subquery(vj_subquery))

    def add_message(self):
        return (
            self.add_first_stop()
            .add_conflict_stop()
            .annotate(
                message=Concat(
                    Func(
                        F("vehicle_journey__start_time"),
                        Value("HH24:MI", output_field=CharField()),
                        function="to_char",
                    ),
                    Value(" from ", output_field=CharField()),
                    "first_stop_name",
                    Value(" and ", output_field=CharField()),
                    Func(
                        F("conflict__start_time"),
                        Value("HH24:MI", output_field=CharField()),
                        function="to_char",
                    ),
                    Value(" from ", output_field=CharField()),
                    "conflict_stop_name",
                    Value(" overlaps", output_field=CharField()),
                    output_field=CharField(),
                ),
            )
        )


class LineExpiredQuerySet(models.QuerySet):
    def add_line(self):
        return self.annotate(line=F("service__name"))

    def add_message(self):
        message = "There is at least one journey that has expired."
        return self.annotate(message=Value(message, output_field=CharField()))


class LineMissingBlockIDQuerySet(models.QuerySet):
    def add_line(self):
        return self.annotate(line=F("service__name"))

    def add_message(self):
        message = "There is at least one journey which has missing block number"
        return self.annotate(message=Value(message, output_field=CharField()))
