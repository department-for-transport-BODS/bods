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

    return factories.SlowLinkWarningFactory.create(
        timing_pattern=timing_pattern,
        # 5 of the 10 timing pattern stops should be considered "effected" by
        # the warning and stored as timings
        timings=(5,),
        common_service_pattern=timing_pattern.service_pattern,
        service_links=(1,),
    )


class TestSlowLinkListPage(ListPageBaseTest):
    """Test Slow Link Warnings list page"""

    model = models.SlowLinkWarning
    factory = factories.SlowLinkWarningFactory
    view = views.SlowLinkListView
    expected_output = {
        "test_get_queryset_adds_correct_message_annotation": (
            "Slow running time between {from_stop_name} and {to_stop_name}"
        ),
        "test_get_table_creates_correct_column_headers": ["Line", "Timing pattern (1)"],
        "test_preamble_text": (
            "Following timing pattern(s) have been observed to have slow links."
        ),
    }


class TestSlowLinkDetailPage(DetailPageBaseTest):
    """Test Slow Link Warnings detail page"""

    model = models.SlowLinkWarning
    factory = factories.SlowLinkWarningFactory
    view = views.SlowLinkDetailView
    list_url_name = "dq:slow-link-list"

    expected_output = {
        "test_timing_pattern_table_caption": (
            "between {first_effected_stop_name} and {last_effected_stop_name}"
        ),
        "test_subtitle_text": "Line {service_name} has slow running time between stops",
    }
