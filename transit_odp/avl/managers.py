from transit_odp.organisation.constants import AVLType
from transit_odp.organisation.managers import DatasetManager, DatasetRevisionManager


class AVLDatasetManager(DatasetManager):
    def get_queryset(self):
        return super().get_queryset().filter(dataset_type=AVLType)


class AVLDatasetRevisionManager(DatasetRevisionManager):
    def get_queryset(self):
        return super().get_queryset().filter(dataset__dataset_type=AVLType)
