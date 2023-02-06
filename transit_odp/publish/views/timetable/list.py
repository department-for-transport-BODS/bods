from transit_odp.organisation.constants import TimetableType
from transit_odp.organisation.models.data import SeasonalService
from transit_odp.otc.models import Service as OTCService
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
        context["all_service_codes"] = OTCService.objects.get_all_without_exempted_ones(
            org_id
        ).count()
        context[
            "missing_service_codes"
        ] = OTCService.objects.get_missing_from_organisation(org_id).count()
        context[
            "seasonal_services_counter"
        ] = SeasonalService.objects.get_count_in_organisation(org_id)
        return context
