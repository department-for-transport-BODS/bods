from math import floor

from django.db.models import Avg

from transit_odp.avl.constants import MORE_DATA_NEEDED
from transit_odp.avl.post_publishing_checks.constants import NO_PPC_DATA
from transit_odp.avl.proxies import AVLDataset
from transit_odp.avl.tables import AVLDataFeedTable
from transit_odp.organisation.constants import AVLType
from transit_odp.publish.views.base import BasePublishListView


class ListView(BasePublishListView):
    template_name = "avl/feed_list.html"

    dataset_type = AVLType
    model = AVLDataset
    table = AVLDataFeedTable

    page_title_datatype = "bus location"
    publish_url_name = "avl:new-feed"
    nav_url_name = "avl:feed-list"

    def get_datasets(self):
        return (
            super()
            .get_datasets()
            .add_avl_compliance_status_cached()
            .add_post_publishing_check_stats()
            .order_by("avl_feed_status", "-modified")
        )

    def get_overall_ppc_score(self):
        avl_datasets = (
            self.get_datasets()
            .get_active()
            .exclude(avl_compliance_status_cached__in=[MORE_DATA_NEEDED])
            .add_post_publishing_check_stats()
        )
        return avl_datasets.exclude(percent_matching=float(NO_PPC_DATA)).aggregate(
            Avg("percent_matching")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        overall_ppc_score = self.get_overall_ppc_score()["percent_matching__avg"]
        context.update(
            {
                "overall_ppc_score": floor(overall_ppc_score)
                if overall_ppc_score
                else overall_ppc_score,
            }
        )
        return context
