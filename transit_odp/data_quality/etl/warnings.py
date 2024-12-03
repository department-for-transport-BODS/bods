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
    ServiceLinkMissingStopWarning,
)

logger = getLogger(__name__)


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
