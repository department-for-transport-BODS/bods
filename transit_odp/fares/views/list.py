from django_hosts import reverse
from waffle import flag_is_active

from config.hosts import PUBLISH_HOST
from transit_odp.browse.common import get_in_scope_in_season_services_line_level
from transit_odp.common.constants import FeatureFlags
from transit_odp.fares.tables import FaresDataFeedTable
from transit_odp.organisation.constants import FaresType
from transit_odp.organisation.models import Dataset
from transit_odp.organisation.models.organisations import Organisation
from transit_odp.publish.requires_attention import FaresRequiresAttention
from transit_odp.publish.views.base import BasePublishListView


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

        is_operator_prefetch_sra_active = flag_is_active(
            "", FeatureFlags.OPERATOR_PREFETCH_SRA.value
        )
        is_fares_require_attention_active = flag_is_active(
            "", FeatureFlags.FARES_REQUIRE_ATTENTION.value
        )
        context["is_fares_require_attention_active"] = is_fares_require_attention_active

        if is_operator_prefetch_sra_active:
            applicable_services = context["organisation"].total_inscope
            fares_sra_count = context["organisation"].fares_sra
        else:
            applicable_services = len(
                get_in_scope_in_season_services_line_level(org_id)
            )

            fares_sra_count = 0
            if is_fares_require_attention_active:
                fares_sra = FaresRequiresAttention(org_id)
                fares_sra_count = len(
                    fares_sra.get_fares_requires_attention_line_level_data()
                )

        context["applicable_services"] = applicable_services
        context["services_requiring_attention"] = fares_sra_count

        return context
