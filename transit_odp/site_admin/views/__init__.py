from django.views.generic.base import TemplateView

from transit_odp.users.views.mixins import SiteAdminViewMixin

from .agents import (
    AgentDetailView,
    AgentListView,
    RemoveAgentUserSuccessView,
    RemoveAgentUserView,
    ResendAgentUserInviteSuccessView,
    ResendAgentUserInviteView,
)
from .consumers import (
    ConsumerDetailView,
    ConsumerListView,
    RevokeConsumerSuccessView,
    RevokeConsumerView,
    UpdateConsumerNotesView,
)
from .datasets import (
    OrganisationAVLListView,
    OrganisationFaresListView,
    OrganisationTimetableListView,
)
from .invites import (
    BulkResendInviteView,
    InviteSuccessView,
    InviteView,
    ResendInvitationView,
    ResendInviteSuccessView,
    ResendOrgUserInviteSuccessView,
    ResendOrgUserInviteView,
)
from .metrics import (
    MetricsDownloadDetailView,
    MetricsDownloadListView,
    MetricsIndexView,
    MetricsOverviewView,
    OperationalMetricsFileView,
)
from .organisations import (
    ManageOrganisationView,
    OrganisationArchiveSuccessView,
    OrganisationArchiveView,
    OrganisationCreateSuccessView,
    OrganisationCreateView,
    OrganisationDetailView,
    OrganisationEditSuccessView,
    OrganisationEditView,
    OrganisationListView,
    OrganisationUsersManageView,
)
from .users import (
    UserArchiveSuccessView,
    UserDetailView,
    UserEditSuccessView,
    UserEditView,
    UserIsActiveView,
)

__all__ = [
    "APIMetricsFileView",
    "AdminHomeView",
    "AgentDetailView",
    "AgentListView",
    "BulkResendInviteView",
    "ConsumerDetailView",
    "ConsumerListView",
    "InviteSuccessView",
    "InviteView",
    "ManageOrganisationView",
    "MetricsDownloadDetailView",
    "MetricsDownloadListView",
    "MetricsIndexView",
    "MetricsOverviewView",
    "OperationalMetricsFileView",
    "OrganisationAVLListView",
    "OrganisationArchiveSuccessView",
    "OrganisationArchiveView",
    "OrganisationCreateSuccessView",
    "OrganisationCreateView",
    "OrganisationDetailView",
    "OrganisationEditSuccessView",
    "OrganisationEditView",
    "OrganisationFaresListView",
    "OrganisationListView",
    "OrganisationTimetableListView",
    "OrganisationUsersManageView",
    "RemoveAgentUserSuccessView",
    "RemoveAgentUserView",
    "ResendAgentUserInviteSuccessView",
    "ResendAgentUserInviteView",
    "ResendInvitationView",
    "ResendInviteSuccessView",
    "ResendOrgUserInviteSuccessView",
    "ResendOrgUserInviteView",
    "RevokeConsumerSuccessView",
    "RevokeConsumerView",
    "UpdateConsumerNotesView",
    "UserArchiveSuccessView",
    "UserDetailView",
    "UserEditSuccessView",
    "UserEditView",
    "UserIsActiveView",
]


class AdminHomeView(SiteAdminViewMixin, TemplateView):
    template_name = "site_admin/home.html"
