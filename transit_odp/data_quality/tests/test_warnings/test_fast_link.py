import pytest

from transit_odp.data_quality import views
from transit_odp.data_quality.factories import (
    FastLinkWarningFactory,
    TimingPatternFactory,
    TimingPatternStopFactory,
)
from transit_odp.data_quality.models import FastLinkWarning
from transit_odp.data_quality.tests.test_warnings.base_warning_test import (
    DetailPageBaseTest,
    ListPageBaseTest,
)

pytestmark = pytest.mark.django_db


@pytest.fixture()
def warning():
    """
    Create warning with 1 service link and 10 timing pattern stops on the associated
    timing pattern
    """
    timing_pattern = TimingPatternFactory.create()
    TimingPatternStopFactory.create_batch(
        10,
        timing_pattern=timing_pattern,
        common_service_pattern=timing_pattern.service_pattern,
    )

    return FastLinkWarningFactory.create(
        timing_pattern=timing_pattern,
        # 5 of the 10 timing pattern stops should be considered "effected" by
        # the warning and stored as timings
        timings=(5,),
        common_service_pattern=timing_pattern.service_pattern,
        service_links=(1,),
    )
