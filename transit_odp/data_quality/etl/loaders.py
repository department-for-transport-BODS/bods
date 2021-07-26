from typing import Dict, List, Optional

from transit_odp.data_quality.dataclasses import Model, features
from transit_odp.data_quality.models.transmodel import (
    Service,
    ServiceLink,
    ServicePattern,
    ServicePatternServiceLink,
    ServicePatternStop,
    StopPoint,
    TimingPattern,
    TimingPatternStop,
    VehicleJourney,
)

BATCH_SIZE = 10000


class SimpleFeatureLoader:
    model = None

    def get_from_feature_kwargs(self, feature: features.Feature) -> Dict:
        return {}

    def get_missing_ito_ids(self, features: List[features.Feature]) -> List[str]:
        ito_ids = set(item.id for item in features)
        db_ito_ids = set(
            self.model.objects.filter(ito_id__in=ito_ids).values_list(
                "ito_id", flat=True
            )
        )
        missing_ito_ids = ito_ids - db_ito_ids
        return missing_ito_ids

    def load(self, features: List[features.Feature]) -> None:
        missing_ito_ids = self.get_missing_ito_ids(features)
        missing_items = [
            self.model.from_feature(feature, **self.get_from_feature_kwargs(feature))
            for feature in features
            if feature.id in missing_ito_ids
        ]
        self.model.objects.bulk_create(missing_items)


class TransModelMapper:
    """
    A class for mapping the BODS transmodel Django models to the features from
    the data quality report.
    """

    def __init__(self, dq_model: Model):
        self._dq_model = dq_model
        self._stops = None
        self._services = None
        self._service_patterns = None
        self._service_links = None
        self._timing_patterns = None
        self._service_pattern_stops = None
        self._timing_pattern_stops = None

    @property
    def stops(self) -> Dict[str, StopPoint]:
        if self._stops is not None:
            return self._stops

        ito_ids = [st.id for st in self._dq_model.stops]
        stop_points = StopPoint.objects.filter(ito_id__in=ito_ids)
        self._stops = {st.ito_id: st for st in stop_points}
        return self._stops

    def get_stop_by_ito_id(self, ito_id: str) -> Optional[StopPoint]:
        return self.stops.get(ito_id, None)

    @property
    def services(self) -> Dict[str, Service]:
        if self._services is not None:
            return self._services

        ito_ids = [li.id for li in self._dq_model.lines]
        services = Service.objects.filter(ito_id__in=ito_ids)
        self._services = {sv.ito_id: sv for sv in services}
        return self._services

    def get_service_by_ito_id(self, ito_id: str) -> Optional[Service]:
        return self.services.get(ito_id, None)

    @property
    def service_patterns(self) -> Dict[str, ServicePattern]:
        if self._service_patterns is not None:
            return self._service_patterns

        ito_ids = [sp.id for sp in self._dq_model.service_patterns]
        service_patterns = ServicePattern.objects.filter(ito_id__in=ito_ids)
        self._service_patterns = {sp.ito_id: sp for sp in service_patterns}
        return self._service_patterns

    def get_service_pattern_by_ito_id(self, ito_id: str) -> Optional[ServicePattern]:
        return self.service_patterns.get(ito_id, None)

    @property
    def service_links(self) -> Dict[str, ServiceLink]:
        if self._service_links is not None:
            return self._service_links

        ito_ids = [sl.id for sl in self._dq_model.service_links]
        service_links = ServiceLink.objects.filter(ito_id__in=ito_ids)
        self._service_links = {sl.ito_id: sl for sl in service_links}
        return self._service_links

    def get_service_link_by_ito_id(self, ito_id: str) -> Optional[ServiceLink]:
        return self.service_links.get(ito_id, None)

    @property
    def timing_patterns(self) -> Dict[str, TimingPattern]:
        if self._timing_patterns is not None:
            return self._timing_patterns

        ito_ids = [tp.id for tp in self._dq_model.timing_patterns]
        timing_patterns = TimingPattern.objects.filter(ito_id__in=ito_ids)
        self._timing_patterns = {tp.ito_id: tp for tp in timing_patterns}
        return self._timing_patterns

    def get_timing_pattern_by_ito_id(self, ito_id: str) -> Optional[TimingPattern]:
        return self.timing_patterns.get(ito_id, None)

    @property
    def service_pattern_stops(self) -> Dict[str, ServicePatternStop]:
        if self._service_pattern_stops is not None:
            return self._service_pattern_stops

        # Load all the ServicePatternStops with service_pattern__ito_id from the model
        ito_ids = [tp.id for tp in self._dq_model.service_patterns]
        service_pattern_stops = ServicePatternStop.objects.filter(
            service_pattern__ito_id__in=ito_ids
        ).select_related("service_pattern")

        # We will be searching for ServicePatternStops using a combination of
        # ServicePattern.ito_id and ServicePatternStop.position so lets just
        # key our dict on (service_pattern.ito_id, position)
        self._service_pattern_stops = {
            (sps.service_pattern.ito_id, sps.position): sps
            for sps in service_pattern_stops
        }
        return self._service_pattern_stops

    def get_service_pattern_stop(
        self, service_pattern_ito_id: str, position: int
    ) -> Optional[ServicePatternStop]:
        """
        Get a ServicePatternStop by its service patterns ito id and position in the
        service pattern.
        """
        key = (service_pattern_ito_id, position)
        return self.service_pattern_stops.get(key, None)

    @property
    def timing_pattern_stops(self):
        if self._timing_pattern_stops is not None:
            return self._timing_pattern_stops

        tp_ids = [tp.id for tp in self.timing_patterns.values()]
        tp_stops = list(
            TimingPatternStop.objects.filter(
                timing_pattern_id__in=tp_ids,
            ).order_by("id")
        )

        self._timing_pattern_stops = {}
        duplicates = []
        for tps in tp_stops:
            key = (tps.timing_pattern_id, tps.service_pattern_stop_id)
            if key in self._timing_pattern_stops:
                duplicates.append(tps)
            else:
                self._timing_pattern_stops[key] = tps

        # delete [TimingPatternStops, TimingPatternStops]
        TimingPatternStop.objects.filter(id__in=[tp.id for tp in duplicates]).delete()

        return self._timing_pattern_stops

    def get_timing_pattern_stop_by_keys(
        self, timing_pattern_id, service_pattern_stop_id
    ):
        key = (timing_pattern_id, service_pattern_stop_id)
        return self.timing_pattern_stops.get(key, None)


class StopPointLoader(SimpleFeatureLoader):
    model = StopPoint


class ServicesLoader(SimpleFeatureLoader):
    model = Service


class ServiceLinkLoader(TransModelMapper, SimpleFeatureLoader):
    model = ServiceLink

    def get_from_feature_kwargs(self, feature: features.ServiceLink) -> Dict[str, int]:
        from_stop = self.get_stop_by_ito_id(feature.properties.from_stop)
        to_stop = self.get_stop_by_ito_id(feature.properties.to_stop)
        return {"from_stop_id": from_stop.id, "to_stop_id": to_stop.id}


class ServicePatternLoader(TransModelMapper, SimpleFeatureLoader):
    model = ServicePattern

    def get_from_feature_kwargs(
        self, feature: features.ServicePattern
    ) -> Dict[str, int]:
        service = self.get_service_by_ito_id(feature.properties.line)
        return {"service_id": service.id}


class ServicePatternStopLoader(TransModelMapper):
    """
    This loader creates a link between a ServicePattern and the list of StopPoints
    within that ServicePattern.
    The order is important so a position field is used.
    """

    def load(self, features: List[features.ServicePattern]) -> None:
        service_pattern_stops = []
        for feature in features:
            service_pattern = self.get_service_pattern_by_ito_id(feature.id)
            for position, stop in enumerate(feature.properties.stops):
                stop_point = self.get_stop_by_ito_id(stop)
                service_pattern_stops.append(
                    ServicePatternStop(
                        service_pattern_id=service_pattern.id,
                        stop_id=stop_point.id,
                        position=position,
                    )
                )

        # If we ignore conflicts missing data will be populated and existing
        # data will not be touched
        ServicePatternStop.objects.bulk_create(
            service_pattern_stops, ignore_conflicts=True, batch_size=BATCH_SIZE
        )


class ServicePatternServiceLinkLoader(TransModelMapper):
    """
    This loader creates a link between a ServicePattern and a list of ServiceLinks.
    The position of the ServiceLink is also inserted into the database.
    """

    def load(self, features: List[features.ServicePattern]) -> None:
        items = []
        for feature in features:
            service_pattern = self.get_service_pattern_by_ito_id(feature.id)
            for position, ito_id in enumerate(feature.properties.service_links):
                service_link = self.get_service_link_by_ito_id(ito_id)
                items.append(
                    ServicePatternServiceLink(
                        service_pattern_id=service_pattern.id,
                        service_link_id=service_link.id,
                        position=position,
                    )
                )

        # If we ignore conflicts missing data will be populated and existing
        # data will not be touched
        ServicePatternServiceLink.objects.bulk_create(
            items, ignore_conflicts=True, batch_size=BATCH_SIZE
        )


class TimingPatternLoader(TransModelMapper, SimpleFeatureLoader):
    model = TimingPattern

    def get_from_feature_kwargs(self, feature: features.TimingPattern) -> None:
        service_pattern = self.get_service_pattern_by_ito_id(feature.service_pattern)
        return {"service_pattern_id": service_pattern.id}


class TimingPatternStopLoader(TransModelMapper):
    """
    This loader creates a link between a TimingPattern and a ServicePatternStop.
    We then also add in timing information such as arrival, departure, pickup_allowed,
    etc.
    """

    def load(self, features: List[features.TimingPattern]) -> None:
        items = []
        for timing_pattern in features:
            db_timing_pattern = self.get_timing_pattern_by_ito_id(timing_pattern.id)
            for position, timing in enumerate(timing_pattern.timings):
                db_service_pattern_stop = self.get_service_pattern_stop(
                    timing_pattern.service_pattern, position
                )
                db_timing_pattern_stop = self.get_timing_pattern_stop_by_keys(
                    db_timing_pattern.id, db_service_pattern_stop.id
                )
                if db_timing_pattern_stop is None:
                    items.append(
                        TimingPatternStop.from_feature(
                            feature=timing,
                            timing_pattern_id=db_timing_pattern.id,
                            service_pattern_stop_id=db_service_pattern_stop.id,
                        )
                    )

        TimingPatternStop.objects.bulk_create(
            items, ignore_conflicts=True, batch_size=BATCH_SIZE
        )


class VehicleJourneyLoader(TransModelMapper, SimpleFeatureLoader):
    """
    Loads in a VehicleJourney from the DataQualityReport vehicle journey.
    """

    model = VehicleJourney

    def get_from_feature_kwargs(
        self, feature: features.VehicleJourney
    ) -> Dict[str, id]:
        timing_pattern = self.get_timing_pattern_by_ito_id(feature.timing_pattern)
        return {"timing_pattern_id": timing_pattern.id}
