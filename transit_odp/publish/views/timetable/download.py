from transit_odp.browse.views.timetable_views import (
    DatasetDownloadView as FeedDownloadViewBase,
)
from transit_odp.users.views.mixins import OrgUserViewMixin


class DatasetDownloadView(OrgUserViewMixin, FeedDownloadViewBase):
    """Adds publisher permissions checks to feed detail download page"""

    # Note don't want to use PublishFeedDetailViewBase since potential MRO clashes
    # with diamond DetailView base
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(organisation_id=self.organisation.id)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pk1"] = self.kwargs["pk1"]
        return context
