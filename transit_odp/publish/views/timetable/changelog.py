from transit_odp.browse.views.timetable_views import DatasetChangeLogView
from transit_odp.timetables.tables import TimetableChangelogTable
from transit_odp.users.views.mixins import OrgUserViewMixin


class FeedChangeLogView(OrgUserViewMixin, DatasetChangeLogView):
    template_name = "publish/feed_change_log.html"
    table_class = TimetableChangelogTable

    def get_dataset_queryset(self):
        return (
            super().get_dataset_queryset().filter(organisation_id=self.organisation.id)
        )

    def get_queryset(self):
        return super().get_queryset().prefetch_related("report", "data_quality_tasks")

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context["pk1"] = self.kwargs["pk1"]
        return context
