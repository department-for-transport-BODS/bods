import csv
import io
from datetime import datetime

import pytest

from transit_odp.organisation.csv.consumer_feedback import ConsumerFeedbackCSV
from transit_odp.organisation.factories import (
    ConsumerFeedbackFactory,
    DatasetRevisionFactory,
    OrganisationFactory,
)
from transit_odp.organisation.querysets import ANONYMOUS, DATASET_LEVEL, GENERAL_LEVEL
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_consumer_feedback_for_operator_to_string():
    today = datetime.now().date().strftime("%d.%m.%y")
    org = OrganisationFactory(short_name="CSV testers R Us")
    consumer = UserFactory()
    revision = DatasetRevisionFactory(dataset__organisation=org)
    ConsumerFeedbackFactory(
        consumer=consumer, dataset=revision.dataset, organisation=org
    )
    ConsumerFeedbackFactory(consumer=None, dataset=revision.dataset, organisation=org)
    ConsumerFeedbackFactory(consumer=consumer, dataset=None, organisation=org)
    ConsumerFeedbackFactory(consumer=None, dataset=None, organisation=org)

    consumer_feedback_csv = ConsumerFeedbackCSV(org.id, True)
    consumer_feedback_csv.queryset = consumer_feedback_csv.get_queryset().order_by("id")
    actual = consumer_feedback_csv.to_string()
    csvfile = io.StringIO(actual)
    reader = csv.reader(csvfile.getvalue().splitlines())
    headers, *rows = list(reader)
    first, second, third, fourth = rows

    assert headers == [
        "Date",
        "Feedback type",
        "Dataset ID",
        "DataType",
        "Description",
        "Raised by: Name",
        "Raised by: Email",
        "Total number of issues raised on this dataset/feed",
    ]

    assert first[0] == today
    assert first[1] == DATASET_LEVEL
    assert first[3] == "Timetables"
    assert first[5] != first[6] != ANONYMOUS
    assert first[7] == "2"

    assert second[0] == today
    assert second[1] == DATASET_LEVEL
    assert second[3] == "Timetables"
    assert second[5] == second[6] == ANONYMOUS
    assert second[7] == "2"

    assert third[0] == today
    assert third[1] == GENERAL_LEVEL
    assert third[5] != third[6] != ANONYMOUS
    assert third[7] == "-"

    assert fourth[0] == today
    assert fourth[1] == GENERAL_LEVEL
    assert fourth[5] == fourth[6] == ANONYMOUS
    assert fourth[7] == "-"


def test_consumer_feedback_for_consumer_to_string():
    today = datetime.now().date().strftime("%d.%m.%y")
    org = OrganisationFactory(short_name="CSV testers R Us")
    consumer = UserFactory()
    revision = DatasetRevisionFactory(dataset__organisation=org)
    ConsumerFeedbackFactory(
        consumer=consumer, dataset=revision.dataset, organisation=org
    )
    ConsumerFeedbackFactory(consumer=None, dataset=revision.dataset, organisation=org)
    ConsumerFeedbackFactory(consumer=consumer, dataset=None, organisation=org)
    ConsumerFeedbackFactory(consumer=None, dataset=None, organisation=org)

    consumer_feedback_csv = ConsumerFeedbackCSV(org.id)
    consumer_feedback_csv.queryset = consumer_feedback_csv.get_queryset().order_by("id")
    actual = consumer_feedback_csv.to_string()
    csvfile = io.StringIO(actual)
    reader = csv.reader(csvfile.getvalue().splitlines())
    headers, *rows = list(reader)
    first, second, third, fourth = rows

    assert headers == [
        "Date",
        "Feedback type",
        "Dataset ID",
        "DataType",
        "Description",
        "Total number of issues raised on this dataset/feed",
    ]

    assert first[0] == today
    assert first[1] == DATASET_LEVEL
    assert first[3] == "Timetables"
    assert first[5] == "2"

    assert second[0] == today
    assert second[1] == DATASET_LEVEL
    assert second[3] == "Timetables"
    assert second[5] == "2"

    assert third[0] == today
    assert third[1] == GENERAL_LEVEL
    assert third[5] == "-"

    assert fourth[0] == today
    assert fourth[1] == GENERAL_LEVEL
    assert fourth[5] == "-"
