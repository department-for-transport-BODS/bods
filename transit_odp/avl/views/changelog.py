from transit_odp.browse.views.base_views import OrgChangeLogView
from transit_odp.organisation.constants import DatasetType
from transit_odp.publish.tables import DatasetRevisionTable
from transit_odp.users.views.mixins import OrgUserViewMixin


class AVLChangeLogView(OrgUserViewMixin, OrgChangeLogView):
    template_name = "avl/changelog.html"
    table_class = DatasetRevisionTable
    dataset_type = DatasetType.AVL.value
