from logging import getLogger

from transit_odp.common.loggers import PipelineAdapter
from transit_odp.data_quality.dataclasses import Model
from transit_odp.data_quality.etl.loaders import (
    ServiceLinkLoader,
    ServicePatternLoader,
    ServicePatternServiceLinkLoader,
    ServicePatternStopLoader,
    ServicesLoader,
    StopPointLoader,
    TimingPatternLoader,
    TimingPatternStopLoader,
    VehicleJourneyLoader,
)
from transit_odp.data_quality.models.transmodel import Service
from transit_odp.timetables.loggers import DQSLoggerContext

logger = getLogger(__name__)


class DQModelPipeline:
    def __init__(self, report_id: int, model: Model):
        self.report_id = report_id
        self.model = model

    def add_report_to_services(self) -> None:
        ThroughModel = Service.reports.through
        ito_ids = [line.id for line in self.model.lines]
        services = Service.objects.filter(ito_id__in=ito_ids)
        throughs = [
            ThroughModel(dataqualityreport_id=self.report_id, service_id=s.id)
            for s in services
        ]
        ThroughModel.objects.bulk_create(throughs, ignore_conflicts=True)

    def load_stops(self) -> None:
        loader = StopPointLoader()
        loader.load(self.model.stops)

    def load_services(self) -> None:
        loader = ServicesLoader(self.model)
        loader.load(self.model.lines)

    def load_service_links(self):
        loader = ServiceLinkLoader(self.model)
        loader.load(self.model.service_links)

    def load_service_patterns(self):
        loader = ServicePatternLoader(self.model)
        loader.load(self.model.service_patterns)

    def load_service_pattern_stops(self):
        loader = ServicePatternStopLoader(self.model)
        loader.load(self.model.service_patterns)

    def load_service_pattern_service_links(self):
        loader = ServicePatternServiceLinkLoader(self.model)
        loader.load(self.model.service_patterns)

    def load_timing_patterns(self):
        loader = TimingPatternLoader(self.model)
        loader.load(self.model.timing_patterns)

    def load_timing_pattern_stops(self):
        loader = TimingPatternStopLoader(self.model)
        loader.load(self.model.timing_patterns)

    def load_vehicle_journeys(self):
        loader = VehicleJourneyLoader(self.model)
        loader.load(self.model.vehicle_journeys)

    def load(self) -> None:
        context = DQSLoggerContext(object_id=self.report_id)
        adapter = PipelineAdapter(logger, {"context": context})

        adapter.info("Loading services/lines")
        self.load_services()
        adapter.info("Loading stops.")
        self.load_stops()
        adapter.info("Loading service patterns.")
        self.load_service_patterns()
        adapter.info("Loading service links.")
        self.load_service_links()
        adapter.info("Loading pattern stops.")
        self.load_service_pattern_stops()
        adapter.info("Loading service pattern service links.")
        self.load_service_pattern_service_links()
        adapter.info("Loading timing patterns.")
        self.load_timing_patterns()
        adapter.info("Loading timing pattern stops.")
        self.load_timing_pattern_stops()
        adapter.info("Loading vehicle journeys.")
        self.load_vehicle_journeys()
        # TODO when pandas is removed manually add report to services
        adapter.info("Transmodel successfully loaded.")
