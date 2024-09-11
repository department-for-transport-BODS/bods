from transit_odp.organisation.constants import DatasetType
from transit_odp.publish.views.timetable.download import DatasetDownloadView


class DownloadFaresFileView(DatasetDownloadView):
    dataset_type = DatasetType.FARES.value
