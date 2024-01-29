import pytest

from transit_odp.naptan.factories import (
    AdminAreaFactory,
    FlexibleZoneFactory,
    StopPointFactory,
    LocalityFactory,
    DistrictFactory,
)
from transit_odp.naptan.models import AdminArea, FlexibleZone
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


class TestFlexibleZoneQuerySet:
    def test_flexible_zone_query_set(self):
        """Tests the flexible_zone defaults query set"""
        admin_area = AdminAreaFactory()
        district = DistrictFactory()
        locality = LocalityFactory(admin_area=admin_area, district=district)
        naptan_stoppoint = StopPointFactory(locality=locality, admin_area=admin_area)
        FlexibleZoneFactory(naptan_stoppoint=naptan_stoppoint, sequence_number=1)
        FlexibleZoneFactory(naptan_stoppoint=naptan_stoppoint, sequence_number=2)

        qs = FlexibleZone.objects.all()
        assert qs[0].sequence_number == 1
        assert qs[1].sequence_number == 2
