from transit_odp.organisation.constants import TimetableType
from transit_odp.organisation.managers import DatasetManager, DatasetRevisionManager


class TimetableDatasetManager(DatasetManager):
    def get_queryset(self):
        return super().get_queryset().filter(dataset_type=TimetableType)


class TimetableDatasetRevisionManager(DatasetRevisionManager):
    def get_queryset(self):
        return super().get_queryset().filter(dataset__dataset_type=TimetableType)
