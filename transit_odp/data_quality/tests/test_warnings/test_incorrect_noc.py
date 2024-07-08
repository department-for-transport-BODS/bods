import pytest

from transit_odp.data_quality import factories, models, views
from transit_odp.data_quality.tests.test_warnings.base_warning_test import (
    ListPageBaseTest,
    get_initialised_view,
)

pytestmark = pytest.mark.django_db


@pytest.fixture()
def warning():
    """
    Create simple warning
    """
    return factories.IncorrectNOCWarningFactory.create(noc="NOC1")


class TestIncorrectNocListPage(ListPageBaseTest):
    model = models.IncorrectNOCWarning
    factory = factories.IncorrectNOCWarningFactory
    view = views.IncorrectNOCListView
    expected_output = {
        "test_get_table_creates_correct_column_headers": [
            "Service",
            "Details",
            "Service Code",
            "Line Name",
        ],
        "test_preamble_text": (
            "The following service(s) have been observed to have incorrect "
            "national operator code(s)."
        ),
    }

    def test_get_queryset_adds_correct_message_annotation(
        self,
        warning,
    ):
        view = get_initialised_view(self.view, warning)
        warnings_qs = view.get_queryset()
        expected_message = (
            "NOC1 is specified in the dataset but not assigned to your organisation"
        )
        assert warnings_qs.first().service == expected_message
