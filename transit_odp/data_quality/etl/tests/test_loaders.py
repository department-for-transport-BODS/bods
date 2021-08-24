import itertools
from unittest.mock import Mock

import pytest

from transit_odp.data_quality.dataclasses import Model
from transit_odp.data_quality.dataclasses.factories import (
    LineFactory,
    ServiceLinkFactory,
    ServicePatternFactory,
    StopFactory,
    TimingFactory,
    TimingPatternFactory,
    VehicleJourneyFactory,
)
from transit_odp.data_quality.etl.loaders import (
    ServiceLinkLoader,
    ServicePatternLoader,
    ServicePatternServiceLinkLoader,
    ServicePatternStopLoader,
    TimingPatternLoader,
    TimingPatternStopLoader,
    TransModelMapper,
    VehicleJourneyLoader,
)
from transit_odp.data_quality.etl.model import ServicesLoader, StopPointLoader
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

pytestmark = pytest.mark.django_db


def test_stop_point_loader():
    stops = StopFactory.create_batch(3)
    loader = StopPointLoader()
    loader.load(stops)
    assert StopPoint.objects.all().count() == len(stops)


def test_stop_point_loader_already_exists():
    stops = StopFactory.create_batch(3)
    stop_points = [StopPoint.from_feature(st) for st in stops]
    StopPoint.objects.bulk_create(stop_points)
    loader = StopPointLoader()
    loader.load(stops)
    assert StopPoint.objects.all().count() == len(stops)


def test_service_loader():
    lines = LineFactory.create_batch(3)
    model = Mock(spec=Model, lines=lines)
    loader = ServicesLoader(model)
    loader.load(lines)
    assert Service.objects.all().count() == len(lines)


def test_model_loader_find_stops_by_ito_id():
    model_stops = StopFactory.create_batch(5)
    non_model_stops = StopFactory.create_batch(5)

    stop_points = [StopPoint.from_feature(st) for st in model_stops + non_model_stops]
    StopPoint.objects.bulk_create(stop_points)

    model = Mock(spec=Model, stops=model_stops)
    mapper = TransModelMapper(model)

    test_ito_id = model_stops[0].id
    result = mapper.get_stop_by_ito_id(test_ito_id)
    assert result.ito_id == test_ito_id

    test_ito_id = non_model_stops[0].id
    result = mapper.get_stop_by_ito_id(test_ito_id)
    assert result is None


def test_model_loader_load_existing_stops():
    model_stops = StopFactory.create_batch(5)
    non_model_stops = StopFactory.create_batch(5)

    stop_points = [StopPoint.from_feature(st) for st in model_stops + non_model_stops]
    StopPoint.objects.bulk_create(stop_points)

    model = Mock(spec=Model, stops=model_stops)
    mapper = TransModelMapper(model)

    expected_ito_ids = [st.id for st in model_stops]
    assert len(mapper.stops.keys()) == len(model_stops)
    assert sorted(mapper.stops.keys()) == sorted(expected_ito_ids)


def test_service_link_loader_no_service_links():
    """
    Given that no service links in features list exist in the database.
    Ensure that all the service links are created correctly in database.
    """
    non_model_stops = StopFactory.create_batch(5)
    model_stops = StopFactory.create_batch(3)
    stop_points = [StopPoint.from_feature(st) for st in model_stops + non_model_stops]
    StopPoint.objects.bulk_create(stop_points)

    model = Mock(spec=Model, stops=model_stops)
    stop_ito_ids = [st.id for st in model_stops]
    from_to_ids = list(itertools.combinations(stop_ito_ids, 2))
    features = [
        ServiceLinkFactory(properties__from_stop=from_id, properties__to_stop=to_id)
        for from_id, to_id in from_to_ids
    ]
    loader = ServiceLinkLoader(model)
    assert ServiceLink.objects.count() == 0
    loader.load(features)
    db_service_links = ServiceLink.objects.all()
    assert db_service_links.count() == len(features)

    expected_ito_ids = [sl.id for sl in features]
    actual_ito_ids = db_service_links.values_list("ito_id", flat=True)
    assert sorted(expected_ito_ids) == sorted(actual_ito_ids)


def test_service_link_loader_existing_service_link():
    """
    Given that 1 of the service links in features is already in the database.
    Ensure that only the remaining service links are created.
    """
    non_model_stops = StopFactory.create_batch(5)
    model_stops = StopFactory.create_batch(3)
    stop_points = [StopPoint.from_feature(st) for st in model_stops + non_model_stops]
    StopPoint.objects.bulk_create(stop_points)

    model = Mock(spec=Model, stops=model_stops)
    stop_ito_ids = [st.id for st in model_stops]
    from_to_ids = list(itertools.combinations(stop_ito_ids, 2))
    features = [
        ServiceLinkFactory(properties__from_stop=from_id, properties__to_stop=to_id)
        for from_id, to_id in from_to_ids
    ]

    feature = features[0]
    from_stop = StopPoint.objects.get(ito_id=feature.properties.from_stop)
    to_stop = StopPoint.objects.get(ito_id=feature.properties.to_stop)
    ServiceLink.from_feature(
        feature=feature, from_stop_id=from_stop.id, to_stop_id=to_stop.id
    ).save()

    loader = ServiceLinkLoader(model)
    assert ServiceLink.objects.count() == 1

    loader.load(features)

    db_service_links = ServiceLink.objects.all()
    assert db_service_links.count() == len(features)
    expected_ito_ids = [sl.id for sl in features]
    actual_ito_ids = db_service_links.values_list("ito_id", flat=True)
    assert sorted(expected_ito_ids) == sorted(actual_ito_ids)


def test_service_loader_exisiting_service_patterns():
    """
    Given that 1 of the service patterns in features is already in the database.
    Ensure that only the remaining service patterns are created.
    """
    model_lines = LineFactory.create_batch(5)
    services = [Service.from_feature(li) for li in model_lines]
    Service.objects.bulk_create(services)

    model = Mock(spec=Model, lines=model_lines)
    features = [ServicePatternFactory(properties__line=li.id) for li in model_lines]

    feature = features[0]
    service = Service.objects.get(ito_id=feature.properties.line)
    ServicePattern.from_feature(feature=feature, service_id=service.id).save()

    loader = ServicePatternLoader(model)
    assert ServicePattern.objects.count() == 1
    loader.load(features=features)
    db_service_patterns = ServicePattern.objects.all()

    assert db_service_patterns.count() == len(features)

    expected_ito_ids = [sp.id for sp in features]
    actual_ito_ids = db_service_patterns.values_list("ito_id", flat=True)
    assert sorted(expected_ito_ids) == sorted(actual_ito_ids)


def test_service_loader_no_service_patterns():
    """
    Given that no service patterns in features list exist in the database.
    Ensure that all the service patterns are created correctly in database.
    """
    model_lines = LineFactory.create_batch(5)
    services = [Service.from_feature(li) for li in model_lines]
    Service.objects.bulk_create(services)

    model = Mock(spec=Model, lines=model_lines)
    features = [ServicePatternFactory(properties__line=li.id) for li in model_lines]

    loader = ServicePatternLoader(model)
    assert ServicePattern.objects.count() == 0
    loader.load(features=features)
    db_service_patterns = ServicePattern.objects.all()

    assert db_service_patterns.count() == len(features)

    expected_ito_ids = [sp.id for sp in features]
    actual_ito_ids = db_service_patterns.values_list("ito_id", flat=True)
    assert sorted(expected_ito_ids) == sorted(actual_ito_ids)


def test_service_pattern_stop_loader():
    """
    Given a data quality ServicePattern with a line and 5 stops.
    Ensure all the required ServicePatternStops are created.
    """
    line = LineFactory()
    stops = StopFactory.create_batch(5)
    stop_ids = [st.id for st in stops]
    service_pattern = ServicePatternFactory(
        properties__stops=stop_ids, properties__line=line.id
    )

    service = Service.from_feature(line)
    service.save()
    stop_points = [StopPoint.from_feature(st) for st in stops]
    StopPoint.objects.bulk_create(stop_points)
    ServicePattern.from_feature(feature=service_pattern, service_id=service.id).save()

    service_patterns = [service_pattern]
    model = Mock(spec=Model, service_patterns=service_patterns, stops=stops)
    loader = ServicePatternStopLoader(model)

    assert ServicePatternStop.objects.count() == 0

    loader.load(features=service_patterns)

    sps = ServicePatternStop.objects.all()
    assert sps.count() == len(stops)

    actual_stop_ids = sps.values_list("stop__ito_id", flat=True)
    assert sorted(stop_ids) == sorted(actual_stop_ids)

    # Given that we delete one of the ServicePatternStops
    # Ensure that calling load again creates the ServicePatternStop again
    sps[3].delete()

    sps = ServicePatternStop.objects.all()
    assert sps.count() == len(stops) - 1

    loader.load(features=service_patterns)

    sps = ServicePatternStop.objects.all()
    assert sps.count() == len(stops)

    actual_stop_ids = sps.values_list("stop__ito_id", flat=True)
    assert sorted(stop_ids) == sorted(actual_stop_ids)


def test_service_pattern_service_link_loader():
    lines = LineFactory.create_batch(1)
    stops = StopFactory.create_batch(4)

    stop_ito_ids = [st.id for st in stops]
    from_to_ids = list(itertools.combinations(stop_ito_ids, 2))
    service_links = [
        ServiceLinkFactory(properties__from_stop=from_id, properties__to_stop=to_id)
        for from_id, to_id in from_to_ids
    ]

    service_link_ids = [sl.id for sl in service_links]
    service_patterns = [
        ServicePatternFactory(
            properties__line=lines[0].id,
            properties__stops=stop_ito_ids,
            properties__service_links=service_link_ids,
        )
    ]

    model = Mock(
        spec=Model,
        lines=lines,
        stops=stops,
        service_patterns=service_patterns,
        service_links=service_links,
    )

    ServicesLoader(model).load(lines)
    StopPointLoader().load(stops)
    ServiceLinkLoader(model).load(service_links)
    ServicePatternLoader(model).load(service_patterns)

    loader = ServicePatternServiceLinkLoader(model)

    assert ServicePatternServiceLink.objects.count() == 0
    loader.load(features=service_patterns)

    spsl = ServicePatternServiceLink.objects.all()
    assert spsl.count() == len(service_links)

    actual_service_link_ito_ids = spsl.values_list("service_link__ito_id", flat=True)
    assert sorted(service_link_ids) == sorted(actual_service_link_ito_ids)

    # Given that we delete one of the ServicePatternServiceLinks
    # Ensure that calling load again creates the ServicePatternServiceLink again
    spsl[3].delete()

    spsl = ServicePatternServiceLink.objects.all()
    assert spsl.count() == len(service_links) - 1

    loader.load(features=service_patterns)

    spsl = ServicePatternServiceLink.objects.all()
    assert spsl.count() == len(service_links)

    actual_service_link_ito_ids = spsl.values_list("service_link__ito_id", flat=True)
    assert sorted(service_link_ids) == sorted(actual_service_link_ito_ids)


def test_timing_pattern_loader():
    lines = LineFactory.create_batch(5)
    service_patterns = [ServicePatternFactory(properties__line=li.id) for li in lines]
    timing_patterns = [
        TimingPatternFactory(service_pattern=sp.id) for sp in service_patterns
    ]
    model = Mock(
        spec=Model,
        lines=lines,
        service_patterns=service_patterns,
        timing_patterns=timing_patterns,
    )
    ServicesLoader(model).load(lines)
    ServicePatternLoader(model).load(service_patterns)

    loader = TimingPatternLoader(model)
    assert TimingPattern.objects.count() == 0
    loader.load(timing_patterns)

    db_timing_patterns = TimingPattern.objects.all()
    assert db_timing_patterns.count() == len(timing_patterns)
    actual_timing_pattern_ids = db_timing_patterns.values_list("ito_id", flat=True)
    assert sorted(tp.id for tp in timing_patterns) == sorted(actual_timing_pattern_ids)

    # Given that we delete one of the TimingPatterns
    # Ensure that calling load again creates the TimingPatterns
    db_timing_patterns[2].delete()
    db_timing_patterns = TimingPattern.objects.all()
    assert db_timing_patterns.count() == len(timing_patterns) - 1

    loader.load(timing_patterns)

    db_timing_patterns = TimingPattern.objects.all()
    assert db_timing_patterns.count() == len(timing_patterns)
    actual_timing_pattern_ids = db_timing_patterns.values_list("ito_id", flat=True)
    assert sorted(tp.id for tp in timing_patterns) == sorted(actual_timing_pattern_ids)


def test_load_timing_pattern_stop_loader():
    lines = LineFactory.create_batch(1)
    stops = StopFactory.create_batch(5)
    stop_ids = [st.id for st in stops]
    service_patterns = [
        ServicePatternFactory(properties__line=li.id, properties__stops=stop_ids)
        for li in lines
    ]
    timings = TimingFactory.create_batch(5)
    timing_patterns = [
        TimingPatternFactory(service_pattern=sp.id, timings=timings)
        for sp in service_patterns
    ]

    model = Mock(
        spec=Model,
        stops=stops,
        lines=lines,
        service_patterns=service_patterns,
        timing_patterns=timing_patterns,
    )
    ServicesLoader(model).load(lines)
    StopPointLoader().load(stops)
    ServicePatternLoader(model).load(service_patterns)
    ServicePatternStopLoader(model).load(service_patterns)
    TimingPatternLoader(model).load(timing_patterns)

    loader = TimingPatternStopLoader(model)
    assert TimingPatternStop.objects.count() == 0
    loader.load(timing_patterns)
    assert TimingPatternStop.objects.count() == len(timings)

    loader = TimingPatternStopLoader(model)
    loader.load(timing_patterns)
    assert TimingPatternStop.objects.count() == len(timings)


def test_vehicle_journey_loader():
    lines = LineFactory.create_batch(5)
    service_patterns = [ServicePatternFactory(properties__line=li.id) for li in lines]
    timing_patterns = [
        TimingPatternFactory(service_pattern=sp.id) for sp in service_patterns
    ]
    vehicle_journeys = [
        VehicleJourneyFactory(timing_pattern=tp.id) for tp in timing_patterns
    ]
    model = Mock(
        spec=Model,
        lines=lines,
        service_patterns=service_patterns,
        timing_patterns=timing_patterns,
        vehicle_journeys=vehicle_journeys,
    )
    ServicesLoader(model).load(lines)
    ServicePatternLoader(model).load(service_patterns)
    TimingPatternLoader(model).load(timing_patterns)

    loader = VehicleJourneyLoader(model)
    assert VehicleJourney.objects.count() == 0
    loader.load(vehicle_journeys)

    db_vehicle_journeys = VehicleJourney.objects.all()
    assert db_vehicle_journeys.count() == len(vehicle_journeys)
    actual_vehicle_journey_ids = db_vehicle_journeys.values_list("ito_id", flat=True)
    assert sorted(vj.id for vj in vehicle_journeys) == sorted(
        actual_vehicle_journey_ids
    )

    # Given that we delete one of the TimingPatterns
    # Ensure that calling load again creates the TimingPatterns
    db_vehicle_journeys[2].delete()
    db_timing_patterns = VehicleJourney.objects.all()
    assert db_timing_patterns.count() == len(vehicle_journeys) - 1

    loader.load(vehicle_journeys)

    db_vehicle_journeys = VehicleJourney.objects.all()
    assert db_vehicle_journeys.count() == len(vehicle_journeys)
    actual_vehicle_journey_ids = db_vehicle_journeys.values_list("ito_id", flat=True)
    assert sorted(vj.id for vj in vehicle_journeys) == sorted(
        actual_vehicle_journey_ids
    )
