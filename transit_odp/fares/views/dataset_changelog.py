from transit_odp.browse.views.timetable_views import DatasetChangeLogView
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models import Dataset
from transit_odp.publish.tables import DatasetRevisionTable
from transit_odp.users.views.mixins import OrgUserViewMixin


class FaresChangelogView(OrgUserViewMixin, DatasetChangeLogView):
    template_name = "fares/feed_change_log.html"
    table_class = DatasetRevisionTable

    def get_dataset_queryset(self):
        return (
            Dataset.objects.get_active_org()
            .filter(organisation_id=self.organisation.id)
            .get_dataset_type(dataset_type=DatasetType.FARES.value)
            .add_live_data()
        )

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context["pk1"] = self.kwargs["pk1"]
        return context
