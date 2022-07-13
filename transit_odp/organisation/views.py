from allauth.account.adapter import get_adapter
from django.contrib.auth import get_user_model
from django.http import Http404, HttpResponseRedirect
from django.utils.translation import gettext as _
from django.views.generic import CreateView
from django.views.generic.base import ContextMixin
from django_hosts import reverse
from invitations.utils import get_invitation_model

import config.hosts
from transit_odp.bods.interfaces.plugins import get_notifications
from transit_odp.common.forms import (
    AcceptRejectForm,
    AgentLeaveForm,
    AgentRemoveForm,
    AgentResendInviteForm,
    ConfirmationForm,
)
from transit_odp.common.view_mixins import BODSBaseView
from transit_odp.common.views import BaseDetailView, BaseTemplateView, BaseUpdateView
from transit_odp.organisation.forms.management import InvitationForm, UserEditForm
from transit_odp.organisation.forms.organisation_profile import OrganisationProfileForm
from transit_odp.organisation.models import Organisation
from transit_odp.users.constants import AccountType
from transit_odp.users.models import AgentUserInvite
from transit_odp.users.views.mixins import (
    AgentOrgAdminViewMixin,
    OrgAdminViewMixin,
    OrgUserViewMixin,
)

notifier = get_notifications()

User = get_user_model()


class ManageView(OrgAdminViewMixin, BaseDetailView, ContextMixin):
    template_name = "users/users_manage.html"
    model = Organisation

    def get_queryset(self):
        return self.request.user.organisations.all()

    def get_context_data(self, *args, **kwargs):
        kwargs = super().get_context_data(*args, **kwargs)
        organisation = self.get_object()
        kwargs.update(
            {
                "pending_standard_invites": organisation.invitation_set.filter(
                    accepted=False, agent_user_invite=None
                ),
                "pending_agent_invites": organisation.agentuserinvite_set.filter(
                    status=AgentUserInvite.PENDING
                ),
                "users": organisation.users.all(),
            }
        )

        return kwargs


class InviteView(OrgAdminViewMixin, BODSBaseView, CreateView):
    template_name = "users/users_invite.html"
    form_class = InvitationForm

    def get_success_url(self):
        return reverse("users:invite-success", host=self.request.host.name)

    def get_cancel_url(self):
        return reverse(
            "users:manage",
            kwargs={"pk": self.request.user.organisation.id},
            host=self.request.host.name,
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {
                "cancel_url": self.get_cancel_url(),
                "request": self.request,
                # Create empty instance to avoid error in form clean() method,
                # caused by GOVUKModelForm calling clean before InvitationForm
                # is fully instantiated
                "instance": self.form_class.Meta.model(),
            }
        )
        return kwargs

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        self.stash_data(form)
        return super().form_valid(form)

    def stash_data(self, form):
        """Stash valid data in session for subsequent view to unstash"""
        get_adapter(self.request).stash_invite_email(
            self.request, form.cleaned_data["email"]
        )


class OrgProfileView(OrgUserViewMixin, BaseDetailView):
    template_name = "organisation/org_profile.html"
    model = Organisation

    def get_queryset(self):
        return self.request.user.organisations.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_url"] = self.request.build_absolute_uri(self.request.path)
        return context


class OrgProfileEditView(AgentOrgAdminViewMixin, BaseUpdateView):
    template_name = "organisation/organisation_profile_form/index.html"
    model = Organisation
    form_class = OrganisationProfileForm

    def get_queryset(self):
        return self.request.user.organisations.all()

    def get_success_url(self):
        org_id = self.kwargs.get("pk", None)
        return reverse(
            "users:edit-org-profile-success",
            kwargs={"pk": org_id},
            host=config.hosts.PUBLISH_HOST,
        )

    def get_cancel_url(self):
        org_id = self.kwargs.get("pk", None)
        return reverse(
            "users:organisation-profile",
            host=self.request.host.name,
            kwargs={"pk": org_id},
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        organisation = kwargs["instance"]
        initial_licence = organisation.licence_not_required
        kwargs.update(
            {
                "cancel_url": self.get_cancel_url(),
                "initial": {"licence_required": initial_licence},
            }
        )
        return kwargs

    def form_valid(self, form):

        noc_has_changed = form.nested_noc.has_changed()
        response = super().form_valid(form)

        if not noc_has_changed:
            return response

        org = self.get_object()
        account_types = [AccountType.org_admin.value, AccountType.agent_user.value]
        recipients = org.users.filter(account_type__in=account_types)
        for recipient in recipients:
            if recipient.is_agent_user:
                notifier.send_agent_noc_changed_notification(org.name, recipient.email)
            else:
                notifier.send_operator_noc_changed_notification(recipient.email)

        return response


class OrgProfileEditSuccessView(AgentOrgAdminViewMixin, BaseTemplateView):
    template_name = "organisation/organisation_form_success.html"


class InviteSuccessView(OrgAdminViewMixin, BaseTemplateView):
    template_name = "users/users_invite_added.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invite_email = get_adapter(self.request).unstash_invite_email(self.request)
        context.update(
            {
                "invite_email": invite_email,
                "button_link": reverse(
                    "users:manage",
                    kwargs={"pk": self.request.user.organisation.id},
                    host=self.request.host.name,
                ),
            }
        )
        return context


class ResendInviteView(OrgAdminViewMixin, BaseUpdateView):
    template_name = "users/user_resend_invite.html"
    form_class = ConfirmationForm

    def get_success_url(self):
        invitation_id = self.object.id
        return reverse(
            "users:re-invite-success",
            kwargs={"pk": invitation_id},
            host=config.hosts.PUBLISH_HOST,
        )

    def get_cancel_url(self):
        return reverse(
            "users:manage",
            kwargs={"pk": self.request.user.organisation_id},
            host=config.hosts.PUBLISH_HOST,
        )

    def get_queryset(self):
        org_admin = self.request.user
        # The user can only resend invitations within their organisation
        return org_admin.organisation.invitation_set.all()

    def get_form_kwargs(self):
        return {"cancel_url": self.get_cancel_url(), "label": "Resend"}

    def post(self, request, *args, **kwargs):
        invitation = self.object = self.get_object()
        invitation.send_invitation(self.request)
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"invite_email": self.object.email})
        return context


class ResendInviteSuccessView(OrgAdminViewMixin, BaseTemplateView):
    template_name = "users/user_resend_invite_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invitation_id = self.kwargs.get("pk")
        invitation = get_invitation_model().objects.get(id=invitation_id)
        context.update({"invite_email": invitation.email})
        return context


class UserIsActiveView(OrgAdminViewMixin, BaseUpdateView):
    template_name = "users/user_archive.html"
    form_class = ConfirmationForm

    def get_success_url(self):
        user_id = self.kwargs.get("pk", None)
        return reverse(
            "users:archive-success", host=self.request.host.name, kwargs={"pk": user_id}
        )

    def get_cancel_url(self):
        user_id = self.kwargs.get("pk", None)
        return reverse(
            "users:manage-user-detail",
            host=self.request.host.name,
            kwargs={"pk": user_id},
        )

    def get_queryset(self):
        org_admin = self.request.user
        # The user can only change users within their organisation
        return org_admin.organisation.users.all().exclude(
            id=org_admin.id
        )  # the user cannot archive themselves

    def get_form_kwargs(self):
        # Note - probably a better way to handle this. As we are using a forms.
        # Form class to display a simple
        # confirmation button, rather than a forms.ModelForm, we need to prevent the
        # form from being initialised with instance
        kwargs = super().get_form_kwargs()
        kwargs.pop("instance", None)
        kwargs.update({"cancel_url": self.get_cancel_url()})
        return kwargs

    def form_valid(self, form):
        user = self.object = self.get_object()
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        return HttpResponseRedirect(self.get_success_url())


class UserArchiveView(OrgAdminViewMixin, BaseTemplateView):
    template_name = "users/user_archive_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs["pk"]
        user = User.objects.get(id=user_id)
        if user:
            context.update({"object": user})
        return context


class UserDetailView(OrgAdminViewMixin, BaseDetailView):
    template_name = "users/users_manage_detail.html"
    model = User
    # Note the User detail object will added to the context as user which will override
    # the built in variable for currently logged in user.
    context_object_name = "bods_user"

    def get_queryset(self):
        organisation = self.request.user.organisation
        allow_accounts = [
            AccountType.org_admin.value,
            AccountType.org_staff.value,
            AccountType.agent_user.value,
        ]
        users = User.objects.filter(
            organisations=organisation, account_type__in=allow_accounts
        )
        return users

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        user = self.get_object()
        if user.is_agent_user:
            invite = user.agent_invitations.filter(
                organisation=self.request.user.organisation
            ).last()
            context["invite"] = invite

        return context


class UserEditView(OrgAdminViewMixin, BaseUpdateView):
    template_name = "users/users_manage_edit.html"
    form_class = UserEditForm
    context_object_name = "user"

    def get_success_url(self):
        user_id = self.kwargs.get("pk", None)
        return reverse(
            "users:manage-user-edit-success",
            host=self.request.host.name,
            kwargs={"pk": user_id},
        )

    def get_cancel_url(self):
        user_id = self.kwargs.get("pk", None)
        return reverse(
            "users:manage-user-detail",
            host=self.request.host.name,
            kwargs={"pk": user_id},
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"cancel_url": self.get_cancel_url()})
        return kwargs

    def get_queryset(self):
        org_admin = self.request.user
        allowed_accounts = [AccountType.org_admin.value, AccountType.org_staff.value]
        # The user can only change users within their organisation
        return org_admin.organisation.users.filter(
            account_type__in=allowed_accounts
        ).exclude(
            id=org_admin.id
        )  # the user cannot archive themselves


class UserEditSuccessView(OrgAdminViewMixin, BaseTemplateView):
    template_name = "users/users_manage_edit_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = self.kwargs.get("pk")
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise Http404(_(f"No {User._meta.verbose_name} found matching the query"))
        else:
            context.update({"user": user})
            return context


class UserAgentResponseView(BaseUpdateView):
    template_name = "users/user_agent_invite_response.html"
    form_class = AcceptRejectForm
    model = AgentUserInvite

    def get_accepted_url(self):
        return reverse(
            "users:agent-user-response-accepted",
            host=self.request.host.name,
            kwargs={"pk": self.object.id},
        )

    def get_rejected_url(self):
        return reverse(
            "users:agent-user-response-rejected",
            host=self.request.host.name,
            kwargs={"pk": self.object.id},
        )

    def get_queryset(self):
        agent = self.request.user
        return agent.agent_invitations.filter(status=AgentUserInvite.PENDING)

    def get_form_kwargs(self):
        # pop the instance since we only want accept/reject not the whole invite
        kwargs = super().get_form_kwargs()
        kwargs.pop("instance", None)
        return kwargs

    def form_valid(self, form):
        status = form.data.get("status", "pending")
        invite = self.get_object()

        if status == invite.ACCEPTED:
            url = self.get_accepted_url()
            invite.accept_invite()
        elif status == invite.REJECTED:
            url = self.get_rejected_url()
            invite.reject_invite()
        else:
            url = reverse("users:home", host=self.request.host.name)
        return HttpResponseRedirect(url)


class UserAgentAcceptResponseView(BaseDetailView):
    template_name = "users/user_agent_invite_response_accepted.html"
    model = AgentUserInvite

    def get_queryset(self):
        agent = self.request.user
        return agent.agent_invitations.filter(status=AgentUserInvite.ACCEPTED)


class UserAgentRejectResponseView(BaseDetailView):
    template_name = "users/user_agent_invite_response_rejected.html"
    model = AgentUserInvite

    def get_queryset(self):
        agent = self.request.user
        return agent.agent_invitations.filter(status=AgentUserInvite.REJECTED)


class UserAgentLeaveOrgView(BaseUpdateView):
    template_name = "users/user_agent_leave_organisation.html"
    model = AgentUserInvite
    form_class = AgentLeaveForm

    def get_queryset(self):
        agent = self.request.user
        return agent.agent_invitations.filter(status=AgentUserInvite.ACCEPTED)

    def get_cancel_url(self):
        return reverse("users:home", host=self.request.host.name)

    def get_success_url(self):
        return reverse(
            "users:agent-user-leave-success",
            kwargs={"pk": self.get_object().id},
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
            invite.leave_organisation()
        else:
            url = self.get_cancel_url()
        return HttpResponseRedirect(url)


class UserAgentLeaveOrgSuccessView(BaseDetailView):
    template_name = "users/user_agent_leave_organisation_success.html"
    model = AgentUserInvite

    def get_queryset(self):
        agent = self.request.user
        return agent.agent_invitations.filter(status=AgentUserInvite.INACTIVE)


class UserAgentRemoveView(BaseUpdateView):
    """View to remove an agent from an organisation."""

    template_name = "users/remove_agent_user_from_org.html"
    model = AgentUserInvite
    form_class = AgentRemoveForm

    def get_queryset(self):
        admin_org = self.request.user.organisation
        return admin_org.agentuserinvite_set.filter(status=AgentUserInvite.ACCEPTED)

    def get_cancel_url(self):
        return reverse(
            "users:manage-user-detail",
            kwargs={"pk": self.get_object().agent.id},
            host=self.request.host.name,
        )

    def get_success_url(self):
        return reverse(
            "users:agent-remove-success",
            kwargs={"pk": self.get_object().id},
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


class UserAgentRemoveSuccessView(BaseDetailView):
    """A view when an agent is successfully removed from an organisation."""

    template_name = "users/remove_agent_user_from_org_success.html"
    model = AgentUserInvite

    def get_queryset(self):
        admin_org = self.request.user.organisation
        return admin_org.agentuserinvite_set.filter(status=AgentUserInvite.INACTIVE)


class ResendAgentUserInviteView(BaseUpdateView):
    """View to remove an agent from an organisation."""

    template_name = "users/resend_agent_invite.html"
    model = AgentUserInvite
    form_class = AgentResendInviteForm

    def get_queryset(self):
        admin_org = self.request.user.organisation
        return admin_org.agentuserinvite_set.filter(status=AgentUserInvite.PENDING)

    def get_cancel_url(self):
        return reverse(
            "users:manage",
            kwargs={"pk": self.get_object().organisation.id},
            host=self.request.host.name,
        )

    def get_success_url(self):
        return reverse(
            "users:agent-resend-invite-success",
            kwargs={"pk": self.get_object().id},
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


class ResendAgentUserInviteSuccessView(BaseDetailView):
    """A view when an agent is successfully removed from an organisation."""

    template_name = "users/resend_agent_invite_success.html"
    model = AgentUserInvite

    def get_queryset(self):
        admin_org = self.request.user.organisation
        return admin_org.agentuserinvite_set.filter(status=AgentUserInvite.PENDING)
