import datetime

from django_hosts import reverse
from waffle import flag_is_active

from config.hosts import PUBLISH_HOST
from transit_odp.browse.common import get_in_scope_in_season_services_line_level
from transit_odp.common.constants import FeatureFlags
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
        is_operator_prefetch_active = flag_is_active(
            "", FeatureFlags.OPERATOR_PREFETCH_SRA.value
        )

        if is_operator_prefetch_active:
            organisation = context["organisation"]
            applicable_services = organisation.total_inscope
            service_require_attention = organisation.timetable_sra
        else:
            applicable_services = len(
                get_in_scope_in_season_services_line_level(org_id)
            )
            service_require_attention = len(
                get_requires_attention_line_level_data(org_id)
            )

        context["applicable_services"] = applicable_services
        context["services_requiring_attention"] = service_require_attention
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
