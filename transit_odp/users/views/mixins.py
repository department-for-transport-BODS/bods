from typing import Any

from allauth.account.adapter import get_adapter
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import Http404
from django.utils.translation import gettext as _
from django_hosts import reverse

from config.hosts import ADMIN_HOST, PUBLISH_HOST
from transit_odp.common.adapters import AccountAdapter
from transit_odp.organisation.models import Organisation
from transit_odp.users.constants import AccountType


class AdapterMixin(object):
    request: Any

    @property
    def adapter(self) -> AccountAdapter:
        return get_adapter(self.request)


class HostAuthMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """Permission mixin to restrict PUBLISH views to org users and ADMIN views to
    site_admin users"""

    raise_exception = False

    def has_permission(self):
        host = self.request.host.name
        user = self.request.user
        return (host == PUBLISH_HOST and user.is_org_user) or (
            host == ADMIN_HOST and user.is_site_admin
        )

    def get_login_url(self):
        return reverse("account_login", host=self.request.host.name)


class BaseOrgUserMixin(HostAuthMixin):
    """
    Base mixin for org users to filter organisation
    """

    def __init__(self, *args, **kwargs):
        self._organisation = None
        super().__init__(*args, **kwargs)

    @property
    def organisation(self) -> Organisation:
        if self._organisation is not None:
            return self._organisation

        org_id = self.kwargs.get("pk1")
        if org_id is None:
            return None

        try:
            self._organisation = self.request.user.organisations.get(id=org_id)
        except Organisation.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": Organisation._meta.verbose_name}
            )
        return self.organisation


class OrgUserViewMixin(BaseOrgUserMixin):
    """
    Permission mixin to restrict view to only org users (on publish host)
    Redirect to login if not logged in and forbidden if logged in but no permission to
    access page
    """

    def has_permission(self):
        """Checks if a user has permission to acess a view."""

        org_id = self.kwargs.get("pk1", False)
        # i'm checking the org_id is truthy here since some org user views don't
        # have `/org/pk1/` for example the initial publish landing page.
        if org_id and not self.request.user.organisations.filter(id=org_id).exists():
            return False

        return super().has_permission() and self.request.user.is_org_user


class OrgAdminViewMixin(BaseOrgUserMixin):
    """Permission mixin to restrict view to only org admins (on publish host)"""

    def has_permission(self):
        return super().has_permission() and self.request.user.is_org_admin


class AgentOrgAdminViewMixin(BaseOrgUserMixin):
    """Permission mixin to restrict a view to agents or org admins."""

    def has_permission(self):
        is_correct_user = (
            self.request.user.is_org_admin or self.request.user.is_agent_user
        )
        return super().has_permission() and is_correct_user


class SiteAdminViewMixin(HostAuthMixin):
    """Permission mixin to restrict view to only site admins (on admin host)"""

    def has_permission(self):
        return (
            super().has_permission()
            and self.request.user.account_type == AccountType.site_admin
        )


class SiteAdminOrOrgAdminViewMixin(HostAuthMixin):
    """Permission mixin to restrict view to admins users (on publish/admin host)"""

    def has_permission(self):
        account_type = self.request.user.account_type
        return super().has_permission() and (
            account_type == AccountType.org_admin
            or account_type == AccountType.site_admin
        )
