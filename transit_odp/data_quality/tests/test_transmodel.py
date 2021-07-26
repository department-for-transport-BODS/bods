import pytest

from transit_odp.data_quality.dataclasses.factories import (
    LineFactory,
    ServiceLinkFactory,
    ServicePatternFactory,
    StopFactory,
    VehicleJourneyFactory,
)
from transit_odp.data_quality.factories import StopPointFactory
from transit_odp.data_quality.factories.transmodel import (
    ServiceFactory,
    TimingPatternFactory,
)
from transit_odp.data_quality.models.transmodel import (
    Service,
    ServiceLink,
    ServicePattern,
    StopPoint,
    VehicleJourney,
)

pytestmark = pytest.mark.django_db


def test_service_from_feature():
    line = LineFactory()
    service = Service.from_feature(line)
    service.save()
    assert Service.objects.filter(ito_id=line.id).count() == 1


def test_stop_point_from_feature():
    stop = StopFactory()
    stop_point = StopPoint.from_feature(stop)
    stop_point.save()
    assert StopPoint.objects.filter(ito_id=stop.id).count() == 1


def test_service_link_from_feature():
    from_stop = StopPointFactory()
    to_stop = StopPointFactory()

    service_link = ServiceLinkFactory(
        properties__from_stop=from_stop.id, properties__to_stop=to_stop.id
    )
    service_link_db = ServiceLink.from_feature(
        feature=service_link, from_stop_id=from_stop.id, to_stop_id=to_stop.id
    )
    service_link_db.save()

    service_links = ServiceLink.objects.all()
    assert service_links.count() == 1
    service_link_db = service_links.first()
    assert service_link_db.from_stop.ito_id == from_stop.ito_id
    assert service_link_db.to_stop.ito_id == to_stop.ito_id


def test_service_pattern_from_feature():
    service = ServiceFactory()
    feature = ServicePatternFactory(properties__line=service.ito_id)
    service_pattern = ServicePattern.from_feature(feature, service.id)
    service_pattern.save()

    assert service_pattern.name == feature.properties.feature_name
    assert service_pattern.service_id == service.id


def test_vehicle_journey_from_feature():
    timing_pattern = TimingPatternFactory()
    feature = VehicleJourneyFactory(timing_pattern=timing_pattern.ito_id)

    vehicle_journey = VehicleJourney.from_feature(
        feature=feature, timing_pattern_id=timing_pattern.id
    )
    vehicle_journey.save()

    assert vehicle_journey.timing_pattern_id == timing_pattern.id
    assert vehicle_journey.ito_id == feature.id
    assert vehicle_journey.dates == feature.datetime_dates
