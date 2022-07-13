from transit_odp.fares.managers import FaresDatasetManager, FaresDatasetRevisionManager
from transit_odp.fares.querysets import FaresDatasetQuerySet
from transit_odp.organisation.models import Dataset, DatasetRevision
from transit_odp.organisation.querysets import DatasetRevisionQuerySet


class FaresDataset(Dataset):
    objects = FaresDatasetManager.from_queryset(FaresDatasetQuerySet)()

    class Meta:
        proxy = True


class FaresDatasetRevision(DatasetRevision):
    objects = FaresDatasetRevisionManager.from_queryset(DatasetRevisionQuerySet)()

    class Meta:
        proxy = True
