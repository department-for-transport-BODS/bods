import pytest

from transit_odp.data_quality.views import FastLinkListView, FastLinkDetailView
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


class TestFastLinkListPage(ListPageBaseTest):
    """Test Fast Link Warnings list page"""

    model = FastLinkWarning
    factory = FastLinkWarningFactory
    view = FastLinkListView
    expected_output = {
        "test_get_queryset_adds_correct_message_annotation": (
            "Fast running time between " "{from_stop_name} and {to_stop_name}"
        ),
        "test_get_table_creates_correct_column_headers": ["Line", "Timing pattern (1)"],
        "test_preamble_text": (
            "Following timing pattern(s) have been observed to "
            "have fast timing links."
        ),
    }


class TestFastLinkDetailPage(DetailPageBaseTest):
    """Test Fast Link Warnings detail page"""

    model = FastLinkWarning
    factory = FastLinkWarningFactory
    view = FastLinkDetailView
    list_url_name = "dq:fast-link-list"

    expected_output = {
        "test_timing_pattern_table_caption": (
            "between {first_effected_stop_name} and " "{last_effected_stop_name}"
        ),
        "test_subtitle_text": "Line {service_name} has fast running time between stops",
    }
