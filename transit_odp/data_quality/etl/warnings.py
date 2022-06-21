from logging import getLogger
from typing import List, Tuple

from transit_odp.data_quality.dataclasses.warnings import JourneyPartialTimingOverlap
from transit_odp.data_quality.dataclasses.warnings.base import BaseWarning
from transit_odp.data_quality.dataclasses.warnings.lines import LineBaseWarning
from transit_odp.data_quality.dataclasses.warnings.stops import StopServiceLinkMissing
from transit_odp.data_quality.models.transmodel import (
    Service,
    ServiceLink,
    StopPoint,
    TimingPattern,
    TimingPatternStop,
    VehicleJourney,
)
from transit_odp.data_quality.models.warnings import (
    DataQualityWarningBase,
    FastTimingWarning,
    JourneyConflictWarning,
    LineExpiredWarning,
    LineMissingBlockIDWarning,
    ServiceLinkMissingStopWarning,
    TimingFirstWarning,
    TimingLastWarning,
    TimingMissingPointWarning,
    TimingMultipleWarning,
)

logger = getLogger(__name__)


class JourneyPartialTimingOverlapETL:
    def __init__(self, report_id: int, warnings: List[JourneyPartialTimingOverlap]):
        self.warnings = warnings
        self.report_id = report_id
        self._vehicle_journeys = None
        self._conflicts = None
        self._stop_points = None
        self._warning_stops_map = {}

    @property
    def vehicle_journeys(self) -> List[VehicleJourney]:
        if self._vehicle_journeys:
            return self._vehicle_journeys

        ito_ids = [w.id for w in self.warnings]
        self._vehicle_journeys = list(VehicleJourney.objects.filter(ito_id__in=ito_ids))
        return self._vehicle_journeys

    def get_vehicle_journey_by_ito_id(self, ito_id: str) -> VehicleJourney:
        vehicle_journeys = [vj for vj in self.vehicle_journeys if vj.ito_id == ito_id]
        return vehicle_journeys[0]

    @property
    def conflicts(self) -> List[VehicleJourney]:
        if self._conflicts:
            return self._conflicts
        ito_ids = [w.conflict for w in self.warnings]
        self._conflicts = list(VehicleJourney.objects.filter(ito_id__in=ito_ids))
        return self._conflicts

    def get_conflict_journey_by_ito_id(self, ito_id: str) -> VehicleJourney:
        vehicle_journeys = [vj for vj in self.conflicts if vj.ito_id == ito_id]
        return vehicle_journeys[0]

    @property
    def stops(self) -> List[StopPoint]:
        if self._stop_points:
            return self._stop_points

        ito_ids = []
        for warning in self.warnings:
            ito_ids += warning.stops

        self._stop_points = list(StopPoint.objects.filter(ito_id__in=ito_ids))
        return self._stop_points

    def get_stops_by_ito_id(self, ito_ids: List[str]) -> List[StopPoint]:
        stops = [sp for sp in self.stops if sp.ito_id in ito_ids]
        return stops

    def map_stops(self, obj: JourneyConflictWarning, stops: List[StopPoint]):
        key = (obj.report_id, obj.vehicle_journey_id, obj.conflict_id)
        self._warning_stops_map[key] = stops

    def get_stops_from_map(self, obj: JourneyConflictWarning) -> List[StopPoint]:
        key = (obj.report_id, obj.vehicle_journey_id, obj.conflict_id)
        return self._warning_stops_map.get(key)

    def load(self) -> None:
        ThroughModel = JourneyConflictWarning.stops.through

        models = []
        for warning in self.warnings:
            vehicle_journey = self.get_vehicle_journey_by_ito_id(warning.id)
            conflict = self.get_conflict_journey_by_ito_id(warning.conflict)
            jcw = JourneyConflictWarning(
                report_id=self.report_id,
                vehicle_journey_id=vehicle_journey.id,
                conflict_id=conflict.id,
            )
            stops = self.get_stops_by_ito_id(warning.stops)
            self.map_stops(jcw, stops)
            models.append(jcw)
        objs = JourneyConflictWarning.objects.bulk_create(models)

        through_models = []
        for obj in objs:
            stops = self.get_stops_from_map(obj)
            for stop in stops:
                through_models.append(
                    ThroughModel(journeyconflictwarning_id=obj.id, stoppoint_id=stop.id)
                )
        ThroughModel.objects.bulk_create(through_models)


class TimingBaseETL:
    """A class for loading timing warnings."""

    WarningClass = None
    ThroughClass = None
    parent_through_name = None

    def __init__(self, report_id: int, warnings: List[BaseWarning]):
        self.warnings = warnings
        self.report_id = report_id
        self._timing_patterns = None
        self._timing_pattern_stops = None
        self._cache = {}

    def get_parent_through_name(self):
        """
        Gets the name of the attribute that links the warning class with a through
        class.
        In most cases this is just the warning class name in lower case with `_id` added
        to the end.
        """
        if self.parent_through_name:
            return self.parent_through_name
        name = self.WarningClass.__name__.lower() + "_id"
        return name

    @property
    def timing_patterns(self) -> List[TimingPattern]:
        """Returns a list of TimingPatterns."""
        if self._timing_patterns:
            return self._timing_patterns

        ito_ids = [w.id for w in self.warnings]
        self._timing_patterns = TimingPattern.objects.filter(ito_id__in=ito_ids)
        return self._timing_patterns

    @property
    def timing_pattern_stops(self) -> List[TimingPatternStop]:
        """Returns a list of TiminingPatternStops."""
        if self._timing_pattern_stops:
            return self._timing_pattern_stops

        pattern_ids = [pattern.id for pattern in self.timing_patterns]
        timing_pattern_stops = list(
            TimingPatternStop.objects.filter(
                timing_pattern_id__in=pattern_ids
            ).select_related("service_pattern_stop")
        )
        return timing_pattern_stops

    def get_timing_pattern_by_ito_id(self, ito_id: int) -> TimingPattern:
        """Get a TimingPattern by its ito id."""
        return [tp for tp in self.timing_patterns if tp.ito_id == ito_id][0]

    def get_timing_pattern_stops(
        self, tp_ito_id: int, positions: List[int]
    ) -> List[TimingPatternStop]:
        """
        Get a list of TimingPatternStops from a TimingPattern ito_id and the position
        of the stop in the ServicePatternStop.
        """
        pattern = self.get_timing_pattern_by_ito_id(tp_ito_id)
        stops = [
            stop
            for stop in self.timing_pattern_stops
            if stop.timing_pattern_id == pattern.id
        ]
        stops = [
            stop for stop in stops if stop.service_pattern_stop.position in positions
        ]
        return stops

    def get_cache_key(self, warning: DataQualityWarningBase) -> Tuple[int]:
        """
        Returns a unique tuple key based on warnings report id and timing
        pattern id.
        """
        return (warning.report_id, warning.timing_pattern_id)

    def add_to_cache(
        self, warning: DataQualityWarningBase, timings: List[TimingPatternStop]
    ) -> None:
        """
        Caches a list of TimingPatternStops in a dict using a tuple containing
        the report_id and timing_pattern_id of a TimingFirstWarning.
        """
        key = self.get_cache_key(warning)
        self._cache[key] = timings

    def get_from_cache(
        self, warning: DataQualityWarningBase
    ) -> List[TimingPatternStop]:
        """
        Returns a list of TimingPatternStops from the ETL pipeline cache.
        """
        key = self.get_cache_key(warning=warning)
        return self._cache[key]

    def load_warnings(self) -> List[TimingFirstWarning]:
        """
        Loads a list of TimingFirst warnings into the database.
        """
        models = []
        for warning in self.warnings:
            timing_pattern = self.get_timing_pattern_by_ito_id(warning.id)
            model = self.WarningClass(
                report_id=self.report_id, timing_pattern_id=timing_pattern.id
            )
            positions = warning.indexes
            timing_pattern_stops = self.get_timing_pattern_stops(warning.id, positions)
            self.add_to_cache(model, timing_pattern_stops)
            models.append(model)

        objs = self.WarningClass.objects.bulk_create(models)
        return list(objs)

    def load_through_models(self, warnings: List[DataQualityWarningBase]) -> None:
        """Adds the through models on to a data quality warning."""
        through_models = []
        for warning in warnings:
            features = self.get_from_cache(warning)
            for feature in features:
                model = self.ThroughClass(timingpatternstop_id=feature.id)
                name = self.get_parent_through_name()
                setattr(model, name, warning.id)
                through_models.append(model)

        self.ThroughClass.objects.bulk_create(through_models)

    def load(self):
        warnings = self.load_warnings()
        self.load_through_models(warnings=warnings)


class TimingFirstETL(TimingBaseETL):
    WarningClass = TimingFirstWarning
    ThroughClass = TimingFirstWarning.timings.through


class TimingLastETL(TimingBaseETL):
    WarningClass = TimingLastWarning
    ThroughClass = TimingLastWarning.timings.through


class TimingMultipleETL(TimingBaseETL):
    WarningClass = TimingMultipleWarning
    ThroughClass = TimingMultipleWarning.timings.through


class TimingMissingPointETL(TimingBaseETL):
    WarningClass = TimingMissingPointWarning
    ThroughClass = TimingMissingPointWarning.timings.through


class FastTimingETL(TimingBaseETL):
    WarningClass = FastTimingWarning
    ThroughClass = FastTimingWarning.timings.through


class LineWarningETL:
    """A base class for loading LineBaseWarnings into BODS."""

    WarningClass = None
    ThroughClass = None
    parent_through_name = None

    def __init__(self, report_id: int, warnings: List[LineBaseWarning]):
        self.warnings: List[LineBaseWarning] = warnings
        self.report_id: int = report_id
        self._services = None
        self._vehicle_journeys = None
        self._vehicle_journey_map = {}

    def get_parent_through_name(self):
        """Gets the name of the attribute that links the warning class with a through class.
        In most cases this is just the warning class name in lower case with `_id` added
        to the end.
        """
        if self.parent_through_name:
            return self.parent_through_name
        name = self.WarningClass.__name__.lower() + "_id"
        return name

    @property
    def services(self) -> List[Service]:
        """
        Returns all the Services associated with the list of LineExpired warnings.
        """
        if self._services:
            return self._services

        ito_ids = [w.id for w in self.warnings]
        self._services = list(Service.objects.filter(ito_id__in=ito_ids))
        return self._services

    @property
    def vehicle_journeys(self) -> List[VehicleJourney]:
        """
        Returns a list of VehicleJourneys associated with all the
        LineExpired warnings.
        """
        if self._vehicle_journeys:
            return self._vehicle_journeys

        ito_ids = []
        for warning in self.warnings:
            ito_ids += warning.journeys

        self._vehicle_journeys = list(VehicleJourney.objects.filter(ito_id__in=ito_ids))
        return self._vehicle_journeys

    def get_service_by_ito_id(self, ito_id: str) -> Service:
        """Get a Service by ito_id."""
        return [s for s in self.services if s.ito_id == ito_id][0]

    def get_vehicle_journeys_by_ito_ids(
        self, ito_ids: List[str]
    ) -> List[VehicleJourney]:
        return [v for v in self.vehicle_journeys if v.ito_id in ito_ids]

    def add_to_cache(
        self, warning: DataQualityWarningBase, vjs: List[VehicleJourney]
    ) -> None:
        """
        Caches a list of vehicle journeys in a dict using a tuple containing
        the report_id and service_id of a line warning.
        """
        key = (warning.report_id, warning.service_id)
        self._vehicle_journey_map[key] = vjs

    def get_from_cache(self, warning: DataQualityWarningBase) -> List[VehicleJourney]:
        """
        Gets a list of VehicleJourneys from a cache.
        """
        key = (warning.report_id, warning.service_id)
        return self._vehicle_journey_map[key]

    def load_through_models(self, warnings: List[DataQualityWarningBase]) -> None:
        """Adds the through models on to a data quality warning."""
        through_models = []
        for warning in warnings:
            journeys = self.get_from_cache(warning)
            for journey in journeys:
                model = self.ThroughClass(vehiclejourney_id=journey.id)
                name = self.get_parent_through_name()
                setattr(model, name, warning.id)
                through_models.append(model)

        self.ThroughClass.objects.bulk_create(through_models)

    def load_warnings(self) -> List[DataQualityWarningBase]:
        """
        Loads and returns list of data quality warnings into the database.
        """
        models = []
        for warning in self.warnings:
            service = self.get_service_by_ito_id(warning.id)
            vehicle_journeys = self.get_vehicle_journeys_by_ito_ids(warning.journeys)
            model = self.WarningClass(report_id=self.report_id, service_id=service.id)
            self.add_to_cache(model, vehicle_journeys)
            models.append(model)

        objs = self.WarningClass.objects.bulk_create(models)
        return list(objs)

    def load(self):
        warnings = self.load_warnings()
        self.load_through_models(warnings)


class LineExpiredETL(LineWarningETL):
    WarningClass = LineExpiredWarning
    ThroughClass = LineExpiredWarning.vehicle_journeys.through


class LineMissingBlockIDETL(LineWarningETL):
    WarningClass = LineMissingBlockIDWarning
    ThroughClass = LineMissingBlockIDWarning.vehicle_journeys.through


class ServiceLinkMissingStopsETL:
    def __init__(self, report_id: int, warnings: List[StopServiceLinkMissing]):
        self.warnings = warnings
        self.report_id = report_id
        self._service_links = None
        self._stop_points = None
        self._warning_stops_map = {}

    @property
    def service_links(self) -> List[ServiceLink]:
        """
        Returns all the ServiceLinks associated with the list of warnings.
        """
        if self._service_links:
            return self._service_links

        ito_ids = [w.id for w in self.warnings]
        self._service_links = list(ServiceLink.objects.filter(ito_id__in=ito_ids))
        return self._service_links

    def get_service_link_by_ito_id(self, ito_ids: List[str]) -> List[ServiceLink]:
        service_links = [sl for sl in self.service_links if sl.ito_id in ito_ids]
        return service_links[0]

    @property
    def stops(self) -> List[StopPoint]:
        if self._stop_points:
            return self._stop_points

        ito_ids = []
        for warning in self.warnings:
            ito_ids += warning.stops

        self._stop_points = list(StopPoint.objects.filter(ito_id__in=ito_ids))
        return self._stop_points

    def get_stops_by_ito_id(self, ito_ids: List[str]) -> List[StopPoint]:
        stops = [sp for sp in self.stops if sp.ito_id in ito_ids]
        return stops

    def map_stops(self, obj: ServiceLinkMissingStopWarning, stops: List[StopPoint]):
        key = (obj.report_id, obj.service_link_id)
        self._warning_stops_map[key] = stops

    def get_stops_from_map(self, obj: ServiceLinkMissingStopWarning) -> List[StopPoint]:
        key = (obj.report_id, obj.service_link_id)
        return self._warning_stops_map.get(key)

    def load(self) -> None:
        ThroughModel = ServiceLinkMissingStopWarning.stops.through

        models = []
        for warning in self.warnings:
            model = ServiceLinkMissingStopWarning(
                report_id=self.report_id,
                service_link=self.get_service_link_by_ito_id(warning.id),
            )
            stops = self.get_stops_by_ito_id(warning.stops)
            self.map_stops(model, stops)
            models.append(model)
        objs = ServiceLinkMissingStopWarning.objects.bulk_create(models)

        through_models = []
        for obj in objs:
            stops = self.get_stops_from_map(obj)
            for stop in stops:
                through_models.append(
                    ThroughModel(
                        servicelinkmissingstopwarning_id=obj.id, stoppoint_id=stop.id
                    )
                )
        ThroughModel.objects.bulk_create(through_models)
