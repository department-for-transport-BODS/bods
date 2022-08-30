import random
from datetime import date

import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText

from transit_odp.data_quality.factories import (
    DataQualityReportFactory,
    ServiceLinkFactory,
    ServicePatternFactory,
    TimingPatternFactory,
    TimingPatternStopFactory,
)
from transit_odp.data_quality.factories.transmodel import (
    ServiceFactory,
    StopPointFactory,
    VehicleJourneyFactory,
)
from transit_odp.data_quality.models.transmodel import ServiceLink, TimingPatternStop
from transit_odp.data_quality.models.warnings import (
    FastLinkWarning,
    FastTimingWarning,
    IncorrectNOCWarning,
    JourneyDateRangeBackwardsWarning,
    JourneyStopInappropriateWarning,
    JourneyWithoutHeadsignWarning,
    LineMissingBlockIDWarning,
    ServiceLinkMissingStopWarning,
    SlowLinkWarning,
    SlowTimingWarning,
    StopMissingNaptanWarning,
    TimingBackwardsWarning,
    TimingDropOffWarning,
    TimingFirstWarning,
    TimingLastWarning,
    TimingMissingPointWarning,
    TimingPatternTimingWarningBase,
    TimingPickUpWarning,
)


class TimingPatternTimingWarningBaseFactory(factory.DjangoModelFactory):
    class Meta:
        model = TimingPatternTimingWarningBase
        exclude = ("common_service_pattern",)

    report = factory.SubFactory(DataQualityReportFactory)
    timing_pattern = factory.SubFactory(
        TimingPatternFactory,
        service_pattern=factory.SelfAttribute("..common_service_pattern"),
    )

    # convenience field to ensure related models share same service pattern
    common_service_pattern = factory.SubFactory(ServicePatternFactory)

    @factory.post_generation
    def service_links(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # allow user to pass ServiceLinks, num ServiceLinks to create or
            # combination of the two
            for item in extracted:
                if isinstance(item, ServiceLink):
                    self.service_links.add(item)
                elif isinstance(item, int):
                    service_links = ServiceLinkFactory.create_batch(item)
                    for link in service_links:
                        self.service_links.add(link)
                else:
                    raise Exception(
                        "arguments must be service link(s) and / or number "
                        "of service links to create"
                    )

    # TODO: tighten up logic, e.g. doesn't currently account for user passing
    # multiple ints
    @factory.post_generation
    def timings(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # allow user to pass TimingPatternStops, num TimingPatternStops to
            # create or combination of the two
            tps = self.timing_pattern.timing_pattern_stops
            max_position = tps.latest(
                "service_pattern_stop__position"
            ).service_pattern_stop.position

            for item in extracted:
                if isinstance(item, TimingPatternStop):
                    if item in tps:
                        self.timings.add(item)
                    else:
                        raise Exception(
                            "timings must be in "
                            "warning.timing_pattern.timing_pattern_stops"
                        )
                elif isinstance(item, int):
                    # service pattern stops on a service pattern should always start
                    # at position 0
                    start_position = random.randint(0, max_position - item)
                    tps_for_timings = tps.filter(
                        service_pattern_stop__position__gte=start_position,
                        service_pattern_stop__position__lt=start_position + item,
                    )
                    for stop in tps_for_timings:
                        self.timings.add(stop)
                else:
                    raise Exception(
                        "arguments must be timing pattern stop(s) and "
                        "/ or number of timing pattern stops to create"
                    )


class FastLinkWarningFactory(TimingPatternTimingWarningBaseFactory):
    class Meta:
        model = FastLinkWarning
        exclude = ("common_service_pattern",)

    report = factory.SubFactory(
        DataQualityReportFactory, summary__data={Meta.model.__name__: 1}
    )


class FastTimingWarningFactory(TimingPatternTimingWarningBaseFactory):
    class Meta:
        model = FastTimingWarning
        exclude = ("common_service_pattern",)

    report = factory.SubFactory(
        DataQualityReportFactory, summary__data={Meta.model.__name__: 1}
    )


class SlowLinkWarningFactory(TimingPatternTimingWarningBaseFactory):
    class Meta:
        model = SlowLinkWarning
        exclude = ("common_service_pattern",)

    report = factory.SubFactory(
        DataQualityReportFactory, summary__data={Meta.model.__name__: 1}
    )


class ServiceLinkMissingStopWarningFactory(factory.DjangoModelFactory):
    class Meta:
        model = ServiceLinkMissingStopWarning

    service_link = factory.SubFactory(ServiceLinkFactory)
    stops = factory.SubFactory(StopPointFactory)
    report = factory.SubFactory(
        DataQualityReportFactory, summary__data={Meta.model.__name__: 1}
    )

    @factory.post_generation
    def stops(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for stop in extracted:
                self.stops.add(stop)


class SlowTimingWarningFactory(TimingPatternTimingWarningBaseFactory):
    class Meta:
        model = SlowTimingWarning
        exclude = ("common_service_pattern",)

    report = factory.SubFactory(
        DataQualityReportFactory, summary__data={Meta.model.__name__: 1}
    )


class TimingFirstWarningFactory(TimingPatternTimingWarningBaseFactory):
    class Meta:
        model = TimingFirstWarning
        exclude = ("common_service_pattern",)

    report = factory.SubFactory(
        DataQualityReportFactory, summary__data={Meta.model.__name__: 1}
    )


class TimingLastWarningFactory(TimingPatternTimingWarningBaseFactory):
    class Meta:
        model = TimingLastWarning
        exclude = ("common_service_pattern",)

    report = factory.SubFactory(
        DataQualityReportFactory, summary__data={Meta.model.__name__: 1}
    )


# TODO: check this factory works as expected
class TimingBackwardsWarningFactory(TimingPatternTimingWarningBaseFactory):
    class Meta:
        model = TimingBackwardsWarning
        exclude = ("common_service_pattern",)

    from_stop = factory.SubFactory(
        TimingPatternStopFactory,
        timing_pattern=factory.SelfAttribute("..timing_pattern"),
        service_pattern_stop__service_pattern=factory.SelfAttribute(
            "..timing_pattern.service_pattern"
        ),
    )
    to_stop = factory.SubFactory(
        TimingPatternStopFactory,
        timing_pattern=factory.SelfAttribute("..timing_pattern"),
        service_pattern_stop__service_pattern=factory.SelfAttribute(
            "..timing_pattern.service_pattern"
        ),
    )

    report = factory.SubFactory(
        DataQualityReportFactory, summary__data={Meta.model.__name__: 1}
    )


class TimingPickUpWarningFactory(TimingPatternTimingWarningBaseFactory):
    class Meta:
        model = TimingPickUpWarning
        exclude = ("common_service_pattern",)

    report = factory.SubFactory(
        DataQualityReportFactory, summary__data={Meta.model.__name__: 1}
    )


class TimingDropOffWarningFactory(TimingPatternTimingWarningBaseFactory):
    class Meta:
        model = TimingDropOffWarning
        exclude = ("common_service_pattern",)

    report = factory.SubFactory(
        DataQualityReportFactory, summary__data={Meta.model.__name__: 1}
    )


class TimingMissingPointWarningFactory(TimingPatternTimingWarningBaseFactory):
    class Meta:
        model = TimingMissingPointWarning
        exclude = ("common_service_pattern",)

    report = factory.SubFactory(
        DataQualityReportFactory, summary__data={Meta.model.__name__: 1}
    )


class JourneyWithoutHeadsignWarningFactory(DjangoModelFactory):
    class Meta:
        model = JourneyWithoutHeadsignWarning
        exclude = ("common_service_pattern",)

    report = factory.SubFactory(
        DataQualityReportFactory, summary__data={Meta.model.__name__: 1}
    )
    vehicle_journey = factory.SubFactory(VehicleJourneyFactory)


class JourneyDateRangeBackwardsWarningFactory(DjangoModelFactory):
    class Meta:
        model = JourneyDateRangeBackwardsWarning
        exclude = ("common_service_pattern",)

    report = factory.SubFactory(
        DataQualityReportFactory, summary__data={Meta.model.__name__: 1}
    )
    vehicle_journey = factory.SubFactory(VehicleJourneyFactory)
    start = date(2020, 1, 1)
    end = date(2019, 12, 1)


class LineMissingBlockIDWarningFactory(DjangoModelFactory):
    class Meta:
        model = LineMissingBlockIDWarning

    report = factory.SubFactory(
        DataQualityReportFactory, summary__data={Meta.model.__name__: 1}
    )
    service = factory.SubFactory(ServiceFactory)


class IncorrectNOCWarningFactory(DjangoModelFactory):
    class Meta:
        model = IncorrectNOCWarning

    noc = factory.fuzzy.FuzzyText(length=4)
    report = factory.SubFactory(
        DataQualityReportFactory, summary__data={Meta.model.__name__: 1}
    )


class StopMissingNaptanWarningFactory(DjangoModelFactory):
    class Meta:
        model = StopMissingNaptanWarning

    stop = factory.SubFactory(StopPointFactory)


class JourneyStopInappropriateWarningFactory(DjangoModelFactory):
    class Meta:
        model = JourneyStopInappropriateWarning

    stop = factory.SubFactory(StopPointFactory)
    stop_type = FuzzyText(length=3)
