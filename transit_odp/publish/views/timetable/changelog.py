from transit_odp.browse.views.base_views import OrgChangeLogView
from transit_odp.organisation.constants import DatasetType
from transit_odp.timetables.tables import TimetableChangelogTable
from transit_odp.users.views.mixins import OrgUserViewMixin


class TimetableChangeLogView(OrgUserViewMixin, OrgChangeLogView):
    template_name = "publish/feed_change_log.html"
    table_class = TimetableChangelogTable
    dataset_type = DatasetType.TIMETABLE.value

    def get_queryset(self):
        return super().get_queryset().prefetch_related("report", "data_quality_tasks")
