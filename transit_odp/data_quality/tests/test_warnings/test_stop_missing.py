import pytest

from transit_odp.data_quality import factories, models, views
from transit_odp.data_quality.tests.test_warnings.base_warning_test import (
    DetailPageBaseTest,
    ListPageBaseTest,
    get_initialised_view,
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

    return factories.TimingMissingPointWarningFactory.create(
        timing_pattern=timing_pattern,
        # in theory there will only ever be one "timings", which is the
        # TimingPatternStop after
        # which we believe there's a missing timing point
        timings=(1,),
        common_service_pattern=timing_pattern.service_pattern,
        service_links=(1,),
    )


@pytest.mark.django_db
class TestStopMissingListPage(ListPageBaseTest):
    model = models.TimingMissingPointWarning
    factory = factories.TimingMissingPointWarningFactory
    view = views.MissingStopListView
    expected_output = {
        "test_get_queryset_adds_correct_message_annotation": (
            "Timing point after " "{effected_stop_name} is missing"
        ),
        "test_get_table_creates_correct_column_headers": ["Line", "Timing pattern (1)"],
        "test_preamble_text": (
            "Following timing pattern(s) have been observed to "
            "have timing point(s) missing."
        ),
    }

    def test_get_queryset_adds_correct_message_annotation(
        self,
        warning,
    ):
        view = get_initialised_view(self.view, warning)
        warnings_qs = view.get_queryset()

        effected_stop_name = warning.timings.first().service_pattern_stop.stop.name

        expected_message = self.expected_output[
            "test_get_queryset_adds_correct_message_annotation"
        ]
        expected_message = expected_message.format(
            effected_stop_name=effected_stop_name
        )

        # earliest("timing_pattern_id") ensures order_by is same as distinct,
        # avoiding programming error
        # (using first() orders by id, making order_by inconsistent with distinct).
        assert warnings_qs.earliest("timing_pattern_id").message == expected_message


@pytest.mark.django_db
class TestStopMissingDetailPage(DetailPageBaseTest):
    model = models.TimingMissingPointWarning
    factory = factories.TimingMissingPointWarningFactory
    view = views.MissingStopDetailView
    list_url_name = "dq:missing-stops-list"

    expected_output = {
        "test_timing_pattern_table_caption": (
            "Next timing point after "
            "{first_effected_stop_name} is missing or is greater than 15 minutes away"
        ),
        "test_subtitle_text": (
            "Line {service_name} has no timing point for " "more than 15 minutes"
        ),
    }
