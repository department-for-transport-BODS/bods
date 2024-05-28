import datetime

from django_hosts import reverse

from config.hosts import PUBLISH_HOST
from transit_odp.browse.common import get_in_scope_in_season_services_line_level_count
from transit_odp.organisation.constants import TimetableType
from transit_odp.organisation.models import ConsumerFeedback, SeasonalService
from transit_odp.publish.requires_attention import (
    get_requires_attention_line_level_data,
)
from transit_odp.publish.tables import DatasetTable
from transit_odp.publish.views.base import BasePublishListView
from transit_odp.timetables.proxies import TimetableDataset


class ListView(BasePublishListView):
    template_name = "publish/feed_list.html"

    dataset_type = TimetableType
    model = TimetableDataset
    table = DatasetTable

    page_title_datatype = "timetables"
    publish_url_name = "new-feed"
    nav_url_name = "feed-list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org_id = context["pk1"]
        context[
            "applicable_services"
        ] = get_in_scope_in_season_services_line_level_count(org_id)
        context["services_requiring_attention"] = len(
            get_requires_attention_line_level_data(org_id)
        )
        today_start = datetime.datetime.today().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        thirty_days_ago = today_start - datetime.timedelta(days=30)
        context["feedback_count"] = (
            ConsumerFeedback.objects.filter(organisation_id=org_id)
            .filter(created__gte=thirty_days_ago)
            .count()
        )
        context[
            "seasonal_services_counter"
        ] = SeasonalService.objects.get_count_in_organisation(org_id)
        context["data_activity_url"] = (
            reverse("data-activity", kwargs={"pk1": org_id}, host=PUBLISH_HOST)
            + "?prev=feed-list"
        )
        return context
