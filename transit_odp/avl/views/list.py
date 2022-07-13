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
            .add_avl_compliance_status()
            .order_by("avl_feed_status", "-modified")
        )
