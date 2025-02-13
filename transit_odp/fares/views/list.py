from django_hosts import reverse

from config.hosts import PUBLISH_HOST
from transit_odp.fares.tables import FaresDataFeedTable
from transit_odp.organisation.constants import FaresType
from transit_odp.organisation.models import Dataset
from transit_odp.publish.views.base import BasePublishListView
from transit_odp.publish.requires_attention import (
    FaresRequiresAttention,
)
from transit_odp.browse.common import get_in_scope_in_season_services_line_level

class ListView(BasePublishListView):
    template_name = "fares/feed_list.html"

    dataset_type = FaresType
    # TODO: try to use proxy model in the future instead
    model = Dataset
    table = FaresDataFeedTable

    page_title_datatype = "fares"
    publish_url_name = "fares:new-feed"
    nav_url_name = "fares:feed-list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org_id = context["pk1"]
        context["data_activity_url"] = (
            reverse(
                "data-activity", kwargs={"pk1": self.organisation.id}, host=PUBLISH_HOST
            )
            + "?prev=fares-feed-list"
        )
        context["applicable_services"] = len(
            get_in_scope_in_season_services_line_level(org_id)
        )
        # SRA
        fares_sra = FaresRequiresAttention(org_id)
        context["services_requiring_attention"] = len(
            fares_sra.get_fares_requires_attention_line_level_data()
        )

        return context
