from transit_odp.browse.views.base_views import OrgChangeLogView
from transit_odp.organisation.constants import DatasetType
from transit_odp.publish.tables import DatasetRevisionTable
from transit_odp.users.views.mixins import OrgUserViewMixin


class FaresChangelogView(OrgUserViewMixin, OrgChangeLogView):
    template_name = "fares/feed_change_log.html"
    table_class = DatasetRevisionTable
    dataset_type = DatasetType.FARES.value
