import uuid

import numpy as np
from django.db import models
from django_hosts import reverse

import config.hosts

from transit_odp.data_quality.models.querysets import (
    IncorrectNOCQuerySet,
    ServiceLinkMissingStopQuerySet,
)
from transit_odp.data_quality.models.report import DataQualityReport
from transit_odp.data_quality.models.transmodel import TimingPatternStop
from transit_odp.organisation.models.data import TXCFileAttributes


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


class BadTimingsMixin(models.Model):
    # Note each bad 'timing' should belong to the same 'timing_pattern'
    # (declared in the parent model). However, this type of constraint
    # is not possible without composite keys in Django.
    timings = models.ManyToManyField("data_quality.TimingPatternStop")

    class Meta:
        abstract = True

    def get_effected_stops(self):
        return self.timings.add_position().add_stop_name().order_by("position")


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

WARNING_MODELS = []
