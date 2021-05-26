from django_tables2 import RequestConfig

from transit_odp.avl.tables import AVLDataFeedTable
from transit_odp.organisation.constants import DatasetType, FeedStatus
from transit_odp.organisation.models import Dataset
from transit_odp.publish.views.timetable.list import PublishView


class ListView(PublishView):
    template_name = "avl/feed_list.html"

    def get_context_data(self, **kwargs):
        tab = self.request.GET.get("tab")
        section = tab or "active"
        datasets = (
            Dataset.objects.filter(
                organisation=self.organisation,
                dataset_type=DatasetType.AVL.value,
            )
            .select_related("organisation")
            .select_related("live_revision")
        ).order_by("status")

        exclude_status = [FeedStatus.expired.value, FeedStatus.inactive.value]
        feeds_table = None

        if section == "active":
            active_feeds = (
                datasets.add_live_data()
                .exclude(status__in=exclude_status)
                .add_draft_revisions()
            )
            feeds_table = AVLDataFeedTable(active_feeds)
            RequestConfig(self.request, paginate={"per_page": self.per_page}).configure(
                feeds_table
            )

        elif section == "draft":
            draft_revisions = datasets.add_draft_revisions().add_draft_revision_data(
                organisation=self.organisation, dataset_types=[DatasetType.AVL]
            )
            feeds_table = AVLDataFeedTable(draft_revisions)
            RequestConfig(self.request, paginate={"per_page": self.per_page}).configure(
                feeds_table
            )

        elif section == "archive":
            archive_feeds = (
                datasets.add_live_data()
                .filter(status__in=exclude_status)
                .add_draft_revisions()
            )
            feeds_table = AVLDataFeedTable(archive_feeds)
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
                    dataset_type=DatasetType.AVL.value,
                    organisation_id=self.organisation.id,
                ),
                "pk1": self.kwargs["pk1"],
                "current_url": self.request.build_absolute_uri(self.request.path),
                "page_title": f"{self.organisation.name} bus location data feeds",
            }
        )
        return context
