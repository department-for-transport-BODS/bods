import pytest
from django.db.models import QuerySet
from django.test import TestCase
from transit_odp.organisation.factories import TXCFileAttributesFactory
from transit_odp.dqs.factories import ChecksFactory, TaskResultsFactory
from transit_odp.dqs.models import TaskResults
from transit_odp.dqs.constants import STATUSES


@pytest.mark.django_db
@pytest.fixture
def setup_data(db):
    txcfileattribute1 = TXCFileAttributesFactory()
    txcfileattribute2 = TXCFileAttributesFactory()

    check1 = ChecksFactory(queue_name="Queue1")
    check2 = ChecksFactory(queue_name="Queue2")

    taskresult1 = TaskResultsFactory(
        status=STATUSES["PENDING"],
        transmodel_txcfileattributes=txcfileattribute1,
        checks=check1,
    )
    taskresult2 = TaskResultsFactory(
        status="completed",
        transmodel_txcfileattributes=txcfileattribute1,
        checks=check1,
    )
    taskresult3 = TaskResultsFactory(
        status=STATUSES["PENDING"],
        transmodel_txcfileattributes=txcfileattribute2,
        checks=check2,
    )

    return {
        "txcfileattribute1": txcfileattribute1,
        "txcfileattribute2": txcfileattribute2,
        "taskresult1": taskresult1,
        "taskresult2": taskresult2,
        "taskresult3": taskresult3,
    }


class TestTaskResultsQueryset:
    def test_get_valid_taskresults(self, db, setup_data):
        txcfileattributes = [
            setup_data["txcfileattribute1"],
            setup_data["txcfileattribute2"],
        ]
        queryset = TaskResults.objects.all()

        valid_taskresults = queryset.get_valid_taskresults(txcfileattributes)

        assert isinstance(valid_taskresults, QuerySet)
        assert set(valid_taskresults) == {
            setup_data["taskresult1"],
            setup_data["taskresult2"],
            setup_data["taskresult3"],
        }

    def test_get_pending_objects(self, db, setup_data):
        txcfileattributes = [
            setup_data["txcfileattribute1"],
            setup_data["txcfileattribute2"],
        ]
        queryset = TaskResults.objects.all()

        pending_objects = queryset.get_pending_objects(txcfileattributes)

        assert isinstance(pending_objects, QuerySet)
        assert set(pending_objects) == {
            setup_data["taskresult1"],
            setup_data["taskresult3"],
        }

        for obj in pending_objects:
            assert obj.queue_name in {"Queue1", "Queue2"}
