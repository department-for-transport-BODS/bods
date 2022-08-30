import datetime

import pytest
from freezegun import freeze_time

from transit_odp.feedback.factories import FeedbackFactory
from transit_odp.feedback.models import Feedback

pytestmark = pytest.mark.django_db


@freeze_time("2022-01-31")
def test_defaults():
    FeedbackFactory()

    assert Feedback.objects.count() == 1
    first_feedback = Feedback.objects.first()
    assert first_feedback.date == datetime.date(2022, 1, 31)
