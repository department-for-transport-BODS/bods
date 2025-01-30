import factory
from factory.django import DjangoModelFactory
from transit_odp.transmodel.factories import (
    VehicleJourneyFactory,
    ServicePatternStopFactory,
)
from transit_odp.organisation.factories import TXCFileAttributesFactory
from transit_odp.dqs.models import Checks, ObservationResults, TaskResults

from transit_odp.dqs.constants import TaskResultsStatus
from transit_odp.transmodel.factories import ServicedOrganisationVehicleJourneyFactory


class ChecksFactory(DjangoModelFactory):
    class Meta:
        model = Checks

    observation = "Sample observation"
    importance = "Medium"
    category = "Sample category"
    queue_name = factory.Faker("word")


class TaskResultsFactory(DjangoModelFactory):
    class Meta:
        model = TaskResults

    status = factory.Iterator([TaskResultsStatus.PENDING.value, "completed"])
    message = factory.Faker("sentence")
    checks = factory.SubFactory(ChecksFactory)
    transmodel_txcfileattributes = factory.SubFactory(TXCFileAttributesFactory)
    dataquality_report = None


class ObservationResultsFactory(DjangoModelFactory):
    class Meta:
        model = ObservationResults

    details = factory.Faker("sentence")
    is_suppressed = factory.Faker("pybool")
    serviced_organisation_vehicle_journey = factory.SubFactory(
        ServicedOrganisationVehicleJourneyFactory
    )
    taskresults = factory.SubFactory(TaskResultsFactory)
    vehicle_journey = factory.SubFactory(VehicleJourneyFactory)
    service_pattern_stop = factory.SubFactory(ServicePatternStopFactory)
