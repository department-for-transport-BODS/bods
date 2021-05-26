import uuid

from django.db import models
from django_hosts import reverse

import config.hosts
from transit_odp.data_quality.models.managers import TimingMissingPointManager
from transit_odp.data_quality.models.querysets import (
    FastLinkQuerySet,
    FastTimingQuerySet,
    IncorrectNOCQuerySet,
    JourneyConflictQuerySet,
    JourneyDateRangeBackwardsQuerySet,
    JourneyDuplicateQuerySet,
    JourneyStopInappropriateQuerySet,
    JourneyWithoutHeadsignQuerySet,
    LineExpiredQuerySet,
    LineMissingBlockIDQuerySet,
    MissingNOCQuerySet,
    ServiceLinkMissingStopQuerySet,
    SlowLinkQuerySet,
    SlowTimingQuerySet,
    StopMissingNaptanQuerySet,
    TimingDropOffQuerySet,
    TimingFirstQuerySet,
    TimingLastQuerySet,
    TimingPatternLineQuerySet,
    TimingPickUpQuerySet,
)
from transit_odp.data_quality.models.report import DataQualityReport
from transit_odp.data_quality.models.transmodel import TimingPatternStop


class DataQualityWarningBase(models.Model):
    viewname = ""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(DataQualityReport, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def get_absolute_url(self):
        return reverse(
            self.viewname,
            kwargs={
                "pk": self.report.revision.dataset.id,
                "warning_pk": self.id,
                "pk1": self.report.revision.dataset.organisation_id,
                "report_id": self.report.id,
            },
            host=config.hosts.PUBLISH_HOST,
        )

    def get_timing_pattern(self):
        raise NotImplementedError(
            """Route from warning to get_timing_pattern varies, so model must
            implement get_timing_pattern"""
        )

    # once we can get to timing_pattern, the logic to get tps ids is the same
    def get_stop_ids(self):
        timing_pattern_stops = self.get_timing_pattern().timing_pattern_stops
        stop_ids = set(
            timing_pattern_stops.values_list("service_pattern_stop__stop_id", flat=True)
        )
        return stop_ids

    def get_effected_stops(self):
        raise NotImplementedError(
            """Route from warning to effected stops varies, so model must
            implement get_effected_stops"""
        )

    # once we can get effected stops, the logic to get tps positions is the same
    def get_effected_stop_positions(self):
        stops = self.get_effected_stops()
        return stops.values_list("position", flat=True)

    # once we can get effected stops, the logic to get stop point ids is the same
    def get_effected_stop_ids(self):
        effected_stop_ids = set(
            self.get_effected_stops().values_list(
                "service_pattern_stop__stop_id", flat=True
            )
        )

        return effected_stop_ids


class JourneyWarningBase(DataQualityWarningBase):
    vehicle_journey = models.ForeignKey(
        "data_quality.VehicleJourney", on_delete=models.CASCADE
    )

    class Meta:
        abstract = True

    def get_timing_pattern(self):
        return self.vehicle_journey.timing_pattern

    # route to vehicle_journey varies, so views often use warning.get_vehicle_journey()
    # the route happens to be very simple in this case!
    def get_vehicle_journey(self):
        return self.vehicle_journey


class JourneyDuplicateWarning(JourneyWarningBase):
    viewname = "dq:duplicate-journey-detail"
    duplicate = models.ForeignKey(
        "data_quality.VehicleJourney",
        related_name="duplicate",
        on_delete=models.CASCADE,
        null=False,
    )

    objects = JourneyDuplicateQuerySet.as_manager()


class JourneyConflictWarning(JourneyWarningBase):
    viewname = "dq:journey-overlap-detail"
    conflict = models.ForeignKey(
        "data_quality.VehicleJourney",
        related_name="conflict",
        on_delete=models.CASCADE,
        null=False,
    )

    stops = models.ManyToManyField("data_quality.StopPoint")
    objects = JourneyConflictQuerySet.as_manager()

    def get_affected_stops(self):
        affected_stops = self.stops.all()
        affected_tps = self.vehicle_journey.timing_pattern.timing_pattern_stops.filter(
            service_pattern_stop__stop__in=affected_stops
        )
        return affected_tps.add_position().add_stop_name().order_by("position")

    def get_effected_stops(self):
        return self.get_affected_stops()


class JourneyWithoutHeadsignWarning(JourneyWarningBase):
    viewname = "dq:missing-headsign-detail"

    objects = JourneyWithoutHeadsignQuerySet.as_manager()


class JourneyDateRangeBackwardsWarning(JourneyWarningBase):
    viewname = "dq:backward-date-range-detail"
    start = models.DateField()
    end = models.DateField()

    objects = JourneyDateRangeBackwardsQuerySet.as_manager()


class ServiceLinkMissingStopWarning(DataQualityWarningBase):
    viewname = "dq:service-link-missing-stops-detail"
    service_link = models.ForeignKey(
        "data_quality.ServiceLink", on_delete=models.CASCADE
    )
    stops = models.ManyToManyField("data_quality.StopPoint")

    objects = ServiceLinkMissingStopQuerySet.as_manager()

    # choose one arbitrary service pattern and timing pattern for use in frontend
    def get_service_pattern(self):
        return self.service_link.service_patterns.earliest("ito_id")

    def get_timing_pattern(self):
        return self.get_service_pattern().timing_patterns.earliest("ito_id")

    def get_vehicle_journeys(self):
        return self.get_timing_pattern().vehicle_journeys.all()

    def get_effected_stops(self):
        effected_stop_points = self.stops.all()
        effected_tps = self.get_timing_pattern().timing_pattern_stops.filter(
            service_pattern_stop__stop__in=effected_stop_points
        )
        return effected_tps.add_position().add_stop_name().order_by("position")


class IncorrectNOCWarning(DataQualityWarningBase):
    noc = models.TextField()

    objects = IncorrectNOCQuerySet.as_manager()

    class Meta(DataQualityWarningBase.Meta):
        unique_together = (("report", "noc"),)


class SchemaNotTXC24Warning(DataQualityWarningBase):
    schema = models.TextField()

    class Meta(DataQualityWarningBase.Meta):
        unique_together = (("schema", "report"),)


class MissingNOCWarning(DataQualityWarningBase):
    objects = MissingNOCQuerySet.as_manager()

    class Meta(DataQualityWarningBase.Meta):
        pass


class TimingPatternWarningBase(DataQualityWarningBase):
    timing_pattern = models.ForeignKey(
        "data_quality.TimingPattern", on_delete=models.CASCADE
    )

    class Meta:
        abstract = True

    def get_timing_pattern(self):
        return self.timing_pattern

    def get_vehicle_journeys(self):
        return self.get_timing_pattern().vehicle_journeys.all()

    objects = TimingPatternLineQuerySet.as_manager()


class BadTimingsMixin(models.Model):
    # Note each bad 'timing' should belong to the same 'timing_pattern'
    # (declared in the parent model). However, this type of constraint
    # is not possible without composite keys in Django.
    timings = models.ManyToManyField("data_quality.TimingPatternStop")

    class Meta:
        abstract = True

    def get_effected_stops(self):
        return self.timings.add_position().add_stop_name().order_by("position")


class TimingPatternTimingWarningBase(BadTimingsMixin, TimingPatternWarningBase):
    service_links = models.ManyToManyField("data_quality.ServiceLink")

    class Meta:
        abstract = True


class FastLinkWarning(TimingPatternTimingWarningBase):
    viewname = "dq:fast-link-detail"

    objects = FastLinkQuerySet.as_manager()


class FastTimingWarning(TimingPatternTimingWarningBase):
    viewname = "dq:fast-timings-detail"

    objects = FastTimingQuerySet.as_manager()


class SlowLinkWarning(TimingPatternTimingWarningBase):
    viewname = "dq:slow-link-detail"

    objects = SlowLinkQuerySet.as_manager()


class SlowTimingWarning(TimingPatternTimingWarningBase):
    viewname = "dq:slow-timings-detail"

    objects = SlowTimingQuerySet.as_manager()


class TimingFirstWarning(TimingPatternTimingWarningBase):
    viewname = "dq:first-stop-not-timing-point-detail"

    objects = TimingFirstQuerySet.as_manager()


class TimingLastWarning(TimingPatternTimingWarningBase):
    viewname = "dq:last-stop-not-timing-point-detail"

    objects = TimingLastQuerySet.as_manager()


class TimingBackwardsWarning(TimingPatternTimingWarningBase):
    viewname = "dq:backward-timing-detail"

    from_stop = models.ForeignKey(
        "data_quality.TimingPatternStop",
        related_name="from_stop",
        on_delete=models.CASCADE,
    )
    to_stop = models.ForeignKey(
        "data_quality.TimingPatternStop",
        related_name="to_stop",
        on_delete=models.CASCADE,
    )

    def get_effected_stops(self):
        effected_tps = TimingPatternStop.objects.filter(
            id__in=[self.from_stop_id, self.to_stop_id]
        )
        return effected_tps.add_position().add_stop_name().order_by("position")


class TimingPickUpWarning(TimingPatternTimingWarningBase):
    viewname = "dq:first-stop-set-down-only-detail"

    objects = TimingPickUpQuerySet.as_manager()


class TimingDropOffWarning(TimingPatternTimingWarningBase):
    viewname = "dq:last-stop-pick-up-only-detail"

    objects = TimingDropOffQuerySet.as_manager()


class TimingMissingPointWarning(TimingPatternTimingWarningBase):
    viewname = "dq:missing-stops-detail"
    objects = TimingMissingPointManager()


class TimingMultipleWarning(BadTimingsMixin, TimingPatternWarningBase):
    viewname = "dq:stop-repeated-detail"


class StopWarningBase(DataQualityWarningBase):
    stop = models.ForeignKey("data_quality.StopPoint", on_delete=models.CASCADE)

    class Meta:
        abstract = True

    # choose one arbitrary service pattern and timing pattern for use in frontend
    def get_service_pattern(self):
        return self.stop.service_patterns.earliest("ito_id")

    def get_timing_pattern(self):
        return self.get_service_pattern().timing_patterns.earliest("ito_id")

    def get_vehicle_journeys(self):
        return self.get_timing_pattern().vehicle_journeys.all()

    def get_effected_stops(self):
        effected_stop_point = self.stop
        timing_pattern = self.get_timing_pattern()
        effected_tps = TimingPatternStop.objects.filter(
            timing_pattern=timing_pattern,
            service_pattern_stop__stop=effected_stop_point,
        )
        return effected_tps.add_position().add_stop_name().order_by("position")


class StopMissingNaptanWarning(StopWarningBase):
    viewname = "dq:stop-missing-naptan-detail"
    service_patterns = models.ManyToManyField("data_quality.ServicePattern")

    objects = StopMissingNaptanQuerySet.as_manager()


# TODO: delete warning? seemingly replaced by JourneyStopInappropriateWarning
# though possibly still being used in dqs_report_tel/transform_warnings.py
class StopIncorrectTypeWarning(StopWarningBase):
    viewname = "dq:incorrect-stop-type-detail"
    stop_type = models.TextField()
    service_patterns = models.ManyToManyField("data_quality.ServicePattern")


class JourneyStopInappropriateWarning(StopWarningBase):
    viewname = "dq:incorrect-stop-type-detail"
    stop_type = models.TextField()
    vehicle_journeys = models.ManyToManyField("data_quality.VehicleJourney")

    def get_vehicle_journeys(self):
        return self.vehicle_journeys.all()

    objects = JourneyStopInappropriateQuerySet.as_manager()


class LineExpiredWarning(DataQualityWarningBase):
    service = models.ForeignKey("data_quality.Service", on_delete=models.CASCADE)
    vehicle_journeys = models.ManyToManyField("data_quality.VehicleJourney")

    objects = LineExpiredQuerySet.as_manager()

    class Meta:
        unique_together = (("report", "service"),)


class LineMissingBlockIDWarning(DataQualityWarningBase):
    viewname = "dq:line-missing-block-id-detail"
    service = models.ForeignKey("data_quality.Service", on_delete=models.CASCADE)
    vehicle_journeys = models.ManyToManyField("data_quality.VehicleJourney")

    objects = LineMissingBlockIDQuerySet.as_manager()

    class Meta:
        unique_together = (("report", "service"),)

    def get_vehicle_journeys(self):
        return self.vehicle_journeys.all()


WARNING_MODELS = [
    FastLinkWarning,
    FastTimingWarning,
    LineExpiredWarning,
    LineMissingBlockIDWarning,
    IncorrectNOCWarning,
    JourneyConflictWarning,
    JourneyDateRangeBackwardsWarning,
    JourneyDuplicateWarning,
    JourneyStopInappropriateWarning,
    JourneyWithoutHeadsignWarning,
    MissingNOCWarning,
    SchemaNotTXC24Warning,
    ServiceLinkMissingStopWarning,
    SlowLinkWarning,
    SlowTimingWarning,
    StopIncorrectTypeWarning,
    StopMissingNaptanWarning,
    TimingBackwardsWarning,
    TimingDropOffWarning,
    TimingFirstWarning,
    TimingLastWarning,
    TimingMissingPointWarning,
    TimingMultipleWarning,
    TimingPickUpWarning,
]
