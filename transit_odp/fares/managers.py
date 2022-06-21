from transit_odp.organisation.constants import FaresType
from transit_odp.organisation.managers import DatasetManager, DatasetRevisionManager


class FaresDatasetManager(DatasetManager):
    def get_queryset(self):
        return super().get_queryset().filter(dataset_type=FaresType)


class FaresDatasetRevisionManager(DatasetRevisionManager):
    def get_queryset(self):
        return super().get_queryset().filter(dataset__dataset_type=FaresType)
