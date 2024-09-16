import pandas as pd
from celery.utils.log import get_task_logger

from transit_odp.common.loggers import get_dataset_adapter_from_revision
from transit_odp.transmodel.models import (
    BookingArrangements,
    FlexibleServiceOperationPeriod,
    NonOperatingDatesExceptions,
    OperatingDatesExceptions,
    OperatingProfile,
    Service,
    ServicedOrganisations,
    ServicedOrganisationVehicleJourney,
    ServicedOrganisationWorkingDays,
    ServiceLink,
    ServicePattern,
    ServicePatternStop,
    VehicleJourney,
)

logger = get_task_logger(__name__)


class TransmodelDataLoader:
    def __init__(self, file_hash):
        self.file_hash = file_hash

    def load(self, live_revision_id):
        # adapter = get_dataset_adapter_from_revision(logger, revision)
        # adapter.info("Loading TransXChange queryset.")

        print("Loading services.")
        services_df = self.services_from_db_to_df(live_revision_id)
        print("services_df>>> ", list(services_df))
        print("Finished loading services.")

        print("Loading service patterns.")
        service_patterns_df = self.service_patterns_db_to_df(live_revision_id)
        print("service_patterns_df>>> ", list(service_patterns_df))
        print("Finished loading service patterns.")

        service_pattern_id = []
        if not service_patterns_df.empty:
            service_pattern_id = service_patterns_df["id"].to_list()

        print("Loading vehicle journeys.")
        vehicle_journeys_df = self.vehicle_journey_db_to_df(
            live_revision_id, service_pattern_id
        )
        print("vehicle_journeys_df>>> ", list(vehicle_journeys_df))
        print("Finished vehicle journeys.")

        vehicle_journeys_id = []
        if not vehicle_journeys_df.empty:
            vehicle_journeys_id = vehicle_journeys_df["id"].to_list()

        print("Loading service pattern stops.")
        servicepattern_stops_df = self.servicepattern_stops_db_to_df(
            live_revision_id, service_pattern_id, vehicle_journeys_id
        )
        print("servicepattern_stops_df>>> ", list(servicepattern_stops_df))
        print("Finished service pattern stops.")

    def services_from_db_to_df(self, revision_id):
        return pd.DataFrame.from_records(
            Service.objects.filter(revision_id=revision_id).values()
        )

    def service_patterns_db_to_df(self, revision_id):
        columns = [
            "id",
            "revision",
            "service_pattern_id",
            "geom",
            "line_name",
            "description",
        ]
        return pd.DataFrame.from_records(
            ServicePattern.objects.filter(revision_id=revision_id).values()
        )

    def vehicle_journey_db_to_df(self, revision_id, service_pattern_id):

        return pd.DataFrame.from_records(
            VehicleJourney.objects.filter(
                service_pattern_id__in=service_pattern_id
            ).values()
        )

    def servicepattern_stops_db_to_df(
        self, revision_id, service_pattern_id, vehicle_journeys_id
    ):
        return pd.DataFrame.from_records(
            ServicePatternStop.objects.filter(
                service_pattern_id__in=service_pattern_id,
                vehicle_journey_id__in=vehicle_journeys_id,
            ).values()
        )
