from django.contrib.auth import get_user_model
from django.db.models import Q
from django.db.models.expressions import Value
from django.db.models.fields import CharField
from django.http import Http404, HttpResponseRedirect
from django.views.generic import DetailView, UpdateView
from django.views.generic.list import MultipleObjectMixin
from django_filters.views import FilterView
from django_hosts import reverse
from django_tables2 import SingleTableView
from django_tables2.views import SingleTableMixin

from transit_odp.common.forms import AgentRemoveForm, AgentResendInviteForm
from transit_odp.organisation.models import Organisation
from transit_odp.site_admin.filters import AgentFilter
from transit_odp.site_admin.tables import AgentOrganisationsTable, AgentsTable
from transit_odp.users.constants import AgentUserType
from transit_odp.users.models import AgentUserInvite
from transit_odp.users.views.mixins import SiteAdminViewMixin

User = get_user_model()

__all__ = [
    "AgentDetailView",
    "AgentListView",
    "RemoveAgentUserSuccessView",
    "RemoveAgentUserView",
    "ResendAgentUserInviteSuccessView",
    "ResendAgentUserInviteView",
]


class AgentDetailView(
    SiteAdminViewMixin, SingleTableMixin, DetailView, MultipleObjectMixin
):
    model = User
    template_name = "site_admin/agent_detail.html"
    table_class = AgentOrganisationsTable
    paginate_by = 10

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related("organisations")
            .filter(account_type=AgentUserType, is_active=True)
        )

    def get_table_data(self):
        return Organisation.objects.select_related("key_contact").filter(
            users=self.object
        )

    def get_context_data(self, **kwargs):
        orgs = self.get_table_data()
        context = super().get_context_data(object_list=orgs)
        return context


class AgentListView(SiteAdminViewMixin, FilterView, SingleTableView):
    model = User
    template_name = "site_admin/agent_list.html"
    table_class = AgentsTable
    paginate_by = 10
    filterset_class = AgentFilter

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .annotate(details=Value("See details", output_field=CharField()))
            .filter(account_type=AgentUserType, is_active=True)
            .order_by("agent_organisation", "email")
        )
        search_term = self.request.GET.get("q", "").strip()
        if search_term:
            org_search = Q(agent_organisation__istartswith=search_term)
            email_search = Q(email__istartswith=search_term)
            qs = qs.filter(org_search | email_search)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        context["letters"] = self.request.GET.getlist("letters")
        return context


class RemoveAgentUserSuccessView(DetailView, SiteAdminViewMixin):
    """Success view for when a site admin removes an agent from an organisation."""

    template_name = "site_admin/remove_agent_user_from_org_success.html"
    model = AgentUserInvite

    def get_object(self):
        invite_id = self.kwargs.get("invite_id", -1)
        try:
            invite = AgentUserInvite.objects.get(id=invite_id)
        except AgentUserInvite.DoesNotExist:
            raise Http404
        return invite


class RemoveAgentUserView(UpdateView, SiteAdminViewMixin):
    """UpdateView for removing an agent from an organisation."""

    template_name = "site_admin/remove_agent_user_from_org.html"
    model = AgentUserInvite
    form_class = AgentRemoveForm

    def get_object(self):
        invite_id = self.kwargs.get("invite_id", -1)
        try:
            invite = AgentUserInvite.objects.get(id=invite_id)
        except AgentUserInvite.DoesNotExist:
            raise Http404

        return invite

    def get_cancel_url(self):
        return reverse(
            "users:manage-user-detail",
            kwargs={
                "pk": self.get_object().organisation.id,
                "pk1": self.get_object().agent.id,
            },
            host=self.request.host.name,
        )

    def get_success_url(self):
        return reverse(
            "users:org-remove-agent-success",
            kwargs={
                "invite_id": self.get_object().id,
                "pk": self.get_object().organisation.id,
                "pk1": self.get_object().agent.id,
            },
            host=self.request.host.name,
        )

    def get_form_kwargs(self):
        # pop the instance since we only want accept/reject not the whole invite
        kwargs = super().get_form_kwargs()
        kwargs.pop("instance", None)
        return kwargs

    def form_valid(self, form):
        status = form.data.get("status", "")
        invite = self.get_object()

        if status == AgentUserInvite.INACTIVE:
            url = self.get_success_url()
            invite.remove_agent()
        else:
            url = self.get_cancel_url()
        return HttpResponseRedirect(url)


class ResendAgentUserInviteSuccessView(DetailView, SiteAdminViewMixin):
    """A view when an agent is successfully removed from an organisation."""

    template_name = "site_admin/resend_agent_invite_success.html"
    model = AgentUserInvite

    def get_object(self):
        invite_id = self.kwargs.get("invite_id", -1)
        try:
            invite = AgentUserInvite.objects.get(
                id=invite_id, status=AgentUserInvite.PENDING
            )
        except AgentUserInvite.DoesNotExist:
            raise Http404

        return invite


class ResendAgentUserInviteView(UpdateView, SiteAdminViewMixin):
    """View to remove an agent from an organisation."""

    template_name = "site_admin/resend_agent_invite.html"
    model = AgentUserInvite
    form_class = AgentResendInviteForm

    def get_object(self):
        invite_id = self.kwargs.get("invite_id", -1)
        try:
            invite = AgentUserInvite.objects.get(
                id=invite_id, status=AgentUserInvite.PENDING
            )
        except AgentUserInvite.DoesNotExist:
            raise Http404

        return invite

    def get_cancel_url(self):
        return reverse(
            "users:org-user-manage",
            kwargs={"pk": self.get_object().organisation.id},
            host=self.request.host.name,
        )

    def get_success_url(self):
        return reverse(
            "users:org-resend-agent-invite-success",
            kwargs={
                "pk": self.get_object().organisation.id,
                "invite_id": self.get_object().id,
            },
            host=self.request.host.name,
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop("instance", None)
        return kwargs

    def form_valid(self, form):
        submit = form.data.get("submit", "cancel")

        if submit == "cancel":
            return HttpResponseRedirect(self.get_cancel_url())

        url = self.get_success_url()
        agent_invite = self.get_object()
        if agent_invite.agent is None:
            agent_invite.invitation.send_invitation(self.request)
        else:
            agent_invite.send_confirmation()

        return HttpResponseRedirect(url)
