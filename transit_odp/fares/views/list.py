from transit_odp.fares.tables import FaresDataFeedTable
from transit_odp.organisation.constants import FaresType
from transit_odp.organisation.models import Dataset
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
