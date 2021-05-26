import pytest

from transit_odp.naptan.factories import AdminAreaFactory
from transit_odp.naptan.models import AdminArea
from transit_odp.organisation.factories import DatasetRevisionFactory

pytestmark = pytest.mark.django_db


class TestAdminAreaQuerySet:
    def test_has_published_datasets(self):
        """Tests the queryset is annotated with the number of live dataset revision
        which index the admin area"""
        admin_areas = AdminAreaFactory.create_batch(1)
        DatasetRevisionFactory(is_published=False, admin_areas=admin_areas)
        DatasetRevisionFactory(is_published=True, admin_areas=admin_areas)
        qs = AdminArea.objects.add_dataset_count()
        assert len(qs) == 1

    def test_add_dataset_count(self):
        """Tests the queryset is annotated with the number of dataset revision which
        index the admin area"""
        admin_areas = AdminAreaFactory.create_batch(1)
        DatasetRevisionFactory(is_published=False, admin_areas=admin_areas)
        DatasetRevisionFactory(is_published=True, admin_areas=admin_areas)
        qs = AdminArea.objects.add_dataset_count()
        assert len(qs) == 1
        assert qs[0].dataset_count == 2

    def test_add_published_dataset_count(self):
        """Tests the queryset is annotated with the number of live dataset revision
        which index the admin area"""
        admin_areas = AdminAreaFactory.create_batch(1)
        DatasetRevisionFactory(is_published=False, admin_areas=admin_areas)
        DatasetRevisionFactory(is_published=True, admin_areas=admin_areas)
        qs = AdminArea.objects.add_published_dataset_count()
        assert len(qs) == 1
        assert qs[0].published_dataset_count == 1
