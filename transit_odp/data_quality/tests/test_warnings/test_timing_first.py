import pytest

from transit_odp.data_quality import factories, models, views
from transit_odp.data_quality.tests.test_warnings.base_warning_test import (
    DetailPageBaseTest,
    ListPageBaseTest,
)

pytestmark = pytest.mark.django_db


@pytest.fixture()
def warning():
    """
    Create warning with 1 service link and 10 timing pattern stops on the
    associated timing pattern
    """
    timing_pattern = factories.TimingPatternFactory.create()
    factories.TimingPatternStopFactory.create_batch(
        10,
        timing_pattern=timing_pattern,
        common_service_pattern=timing_pattern.service_pattern,
    )

    return factories.TimingFirstWarningFactory.create(
        timing_pattern=timing_pattern,
        # 5 of the 10 timing pattern stops should be considered "effected" by
        # the warning and stored as timings
        timings=(5,),
        common_service_pattern=timing_pattern.service_pattern,
        service_links=(1,),
    )


class TestTimingFirstListPage(ListPageBaseTest):
    model = models.TimingFirstWarning
    factory = factories.TimingFirstWarningFactory
    view = views.FirstStopNotTimingListView
    expected_output = {
        "test_get_queryset_adds_correct_message_annotation": (
            "There is at least one journey where the first stop is not a timing point"
        ),
        "test_get_table_creates_correct_column_headers": ["Line", "Timing pattern (1)"],
        "test_preamble_text": (
            "First stop in the following timing pattern(s) "
            "have been observed to not have timing points."
        ),
    }


class TestTimingFirstDetailPage(DetailPageBaseTest):
    model = models.TimingFirstWarning
    factory = factories.TimingFirstWarningFactory
    view = views.FirstStopNotTimingDetailView
    list_url_name = "dq:first-stop-not-timing-point-list"

    expected_output = {
        "test_timing_pattern_table_caption": (
            "{first_effected_stop_name} is the first stop in a timing pattern "
            "but is not designated a timing point"
        ),
        "test_subtitle_text": (
            "Line {service_name} has at least one journey where "
            "the first stop is not a timing point"
        ),
    }
