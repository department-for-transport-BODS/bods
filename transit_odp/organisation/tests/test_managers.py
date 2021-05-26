from datetime import datetime, timedelta

import pytest
import pytz

from transit_odp.organisation.factories import DatasetFactory, DatasetRevisionFactory
from transit_odp.organisation.models import LiveDatasetRevision

pytestmark = pytest.mark.django_db


class TestLiveDatasetRevisionManager:
    def test_get_queryset(self):
        """Tests queryset returns latest, published revisions"""
        # Setup
        now = datetime.utcnow().replace(tzinfo=pytz.utc)
        datasets = DatasetFactory.create_batch(3, live_revision=None)

        kwargs_list = [
            # dataset 1 has 3 live revisions
            {
                "created": now - timedelta(hours=2),
                "dataset": datasets[0],
                "is_published": True,
            },
            {
                "created": now - timedelta(hours=1),
                "dataset": datasets[0],
                "is_published": True,
            },
            {"created": now, "dataset": datasets[0], "is_published": True},
            # dataset 2 has a live + draft revision
            {
                "created": now - timedelta(hours=6),
                "dataset": datasets[1],
                "is_published": True,
            },
            {
                "created": now - timedelta(hours=1),
                "dataset": datasets[1],
                "is_published": False,
            },
            # dataset 3 has only a draft revision
            {"created": now, "dataset": datasets[2], "is_published": False},
        ]
        for kwargs in kwargs_list:
            DatasetRevisionFactory(**kwargs)

        # Test
        live_revisions = LiveDatasetRevision.objects.all()

        # Assert
        assert len(live_revisions) == 2
        for rev in live_revisions:
            assert (rev.dataset_id, rev.created, rev.is_published) in [
                (datasets[0].id, now, True),
                (datasets[1].id, now - timedelta(hours=6), True),
            ]
