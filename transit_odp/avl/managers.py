from transit_odp.organisation.constants import AVLType
from transit_odp.organisation.managers import DatasetManager


class AVLDatasetManager(DatasetManager):
    def get_queryset(self):
        return super().get_queryset().filter(dataset_type=AVLType)
