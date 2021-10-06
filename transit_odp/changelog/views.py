from django.views.generic import ListView

from transit_odp.changelog.constants import ConsumerIssue, PublisherIssue
from transit_odp.changelog.models import HighLevelRoadMap, KnownIssues


class ChangelogView(ListView):
    model = KnownIssues
    template_name = "changelog/changelog.html"

    def get_queryset(self):
        return super().get_queryset().order_by("-modified")

    def get_context_data(self, **kwargs):
        roadmap = HighLevelRoadMap.objects.first()

        grouped_issues = {PublisherIssue: [], ConsumerIssue: []}
        for issue in self.object_list:
            # This will avoid doing two separate queries
            if not issue.deleted:
                grouped_issues[issue.category].append(issue)

        last_modified_issue = self.object_list.first()

        if not last_modified_issue:
            last_modified_time = roadmap.modified
        else:
            last_modified_time = max([last_modified_issue.modified, roadmap.modified])

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "known_issues": grouped_issues,
                "last_updated": last_modified_time,
                "roadmap": roadmap,
            }
        )
        return context
