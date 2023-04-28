from transit_odp.browse.views.base_views import BaseListView
from transit_odp.common.views import BaseDetailView
from transit_odp.organisation.models import Organisation


class LocalAuthorityView(BaseListView):
    template_name = "browse/local_authority.html"
    model = Organisation
    # Model needs to be changed


class LocalAuthorityDetailView(BaseDetailView):
    template_name = "browse/local_authority/local_authority_detail.html"
    model = Organisation
    # Model needs to be changed
