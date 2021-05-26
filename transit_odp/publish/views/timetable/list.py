from django_tables2 import RequestConfig

from transit_odp.organisation.constants import DatasetType, FeedStatus
from transit_odp.organisation.models import Dataset
from transit_odp.publish.tables import DatasetTable
from transit_odp.publish.views.base import BaseTemplateView
from transit_odp.users.views.mixins import OrgUserViewMixin


class PublishView(OrgUserViewMixin, BaseTemplateView):
    template_name = "publish/feed_list.html"
    per_page = 10

    def get_context_data(self, **kwargs):
        # We want to know if tab is None, this means user hasnt clicked on tab
        # so dont run autofocus script
        tab = self.request.GET.get("tab")
        section = tab or "active"
        datasets = (
            Dataset.objects.filter(
                organisation=self.organisation,
                dataset_type=DatasetType.TIMETABLE.value,
            )
            .select_related("organisation")
            .select_related("live_revision")
        )
        exclude_status = [FeedStatus.expired.value, FeedStatus.inactive.value]
        feeds_table = None

        if section == "active":
            # active feeds
            active_feeds = (
                datasets.add_live_data()
                .exclude(status__in=exclude_status)
                .add_draft_revisions()
            )
            feeds_table = DatasetTable(active_feeds)
            RequestConfig(self.request, paginate={"per_page": self.per_page}).configure(
                feeds_table
            )

        elif section == "draft":
            # draft revisions
            draft_revisions = datasets.add_draft_revisions().add_draft_revision_data(
                organisation=self.organisation
            )
            feeds_table = DatasetTable(draft_revisions)
            RequestConfig(self.request, paginate={"per_page": self.per_page}).configure(
                feeds_table
            )

        elif section == "archive":
            # archived feeds
            archive_feeds = (
                datasets.add_live_data()
                .filter(status__in=exclude_status)
                .add_draft_revisions()
            )
            feeds_table = DatasetTable(archive_feeds)
            RequestConfig(self.request, paginate={"per_page": self.per_page}).configure(
                feeds_table
            )
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "organisation": self.organisation,
                "tab": section,
                "focus": tab,
                "sections": (
                    ("active", "Active"),
                    ("draft", "Draft"),
                    ("archive", "Inactive"),
                ),
                "active_feeds": datasets,
                "active_feeds_table": feeds_table,
                "global_feed_stats": datasets.agg_global_feed_stats(
                    dataset_type=DatasetType.TIMETABLE.value,
                    organisation_id=self.organisation.id,
                ),
                "pk1": self.kwargs["pk1"],
                "current_url": self.request.build_absolute_uri(self.request.path),
                "page_title": f"{self.organisation.name} timetables data sets",
            }
        )
        return context
