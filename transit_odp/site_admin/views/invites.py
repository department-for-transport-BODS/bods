from typing import Optional

from allauth.account.adapter import get_adapter
from django.contrib.auth import get_user_model
from django.http import Http404, HttpResponseRedirect
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView
from django.views.generic.edit import FormView
from django_hosts import reverse

from config.hosts import ADMIN_HOST
from transit_odp.common.forms import ConfirmationForm
from transit_odp.organisation.forms.management import InvitationForm
from transit_odp.organisation.models import Organisation
from transit_odp.users.models import Invitation
from transit_odp.users.views.mixins import SiteAdminViewMixin

User = get_user_model()


__all__ = [
    "BulkResendInviteView",
    "InviteSuccessView",
    "InviteView",
    "ResendInvitationView",
    "ResendInviteSuccessView",
    "ResendOrgUserInviteSuccessView",
    "ResendOrgUserInviteView",
]


class ResendOrgUserInviteSuccessView(SiteAdminViewMixin, DetailView):
    template_name = "users/user_resend_invite_success.html"
    model = Invitation
    pk_url_kwarg = "pk1"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "invite_email": self.object.email,
                "button_text": "Go back to my account",
                "is_site_admin": True,
            }
        )
        return context


class ResendOrgUserInviteView(SiteAdminViewMixin, UpdateView):
    template_name = "users/user_resend_invite.html"
    form_class = ConfirmationForm

    def get_organisation(self):
        pk = self.kwargs.get(self.pk_url_kwarg)
        try:
            organisation = Organisation.objects.get(id=pk)
        except Organisation.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": Organisation._meta.verbose_name}
            )
        return organisation

    def get_success_url(self):
        invitation_id = self.object.id
        organisation = self.get_organisation()
        return reverse(
            "users:manage-user-re-invite-success",
            kwargs={"pk": organisation.id, "pk1": invitation_id},
            host=ADMIN_HOST,
        )

    def get_cancel_url(self):
        organisation = self.get_organisation()
        return reverse(
            "users:org-user-manage",
            kwargs={"pk": organisation.id},
            host=ADMIN_HOST,
        )

    def get_object(self, queryset=None):

        if queryset is None:
            queryset = self.get_queryset()

        invitation_id = self.kwargs.get("pk1", -1)
        try:
            invitation = queryset.get(pk=invitation_id)
        except Organisation.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": queryset.model._meta.verbose_name}
            )
        return invitation

    def get_queryset(self):
        organisation = self.get_organisation()
        # The user can only resend invitations within their organisation
        return organisation.invitation_set.all()

    def get_form_kwargs(self):
        return {"cancel_url": self.get_cancel_url(), "label": "Resend"}

    def post(self, request, *args, **kwargs):
        invitation = self.object = self.get_object()
        invitation.send_invitation(self.request)
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "invite_email": self.object.email,
                "organisation": self.object.organisation,
                "is_site_admin": True,
            }
        )
        return context


class BulkResendInviteView(SiteAdminViewMixin, FormView):
    form_class = ConfirmationForm
    template_name = "site_admin/bulk_resend_invitation_confirmation.html"

    def get_cancel_url(self):
        return reverse(
            "users:organisation-manage",
            host=self.request.host.name,
        )

    def get_success_url(self):
        return self.get_cancel_url()

    def get_form_kwargs(self):
        adapter = get_adapter(self.request)
        kwargs = super().get_form_kwargs()
        noun = (
            "Invitations"
            if len(adapter.get_bulk_resend_invite_org_ids(self.request)) > 1
            else "Invitation"
        )
        kwargs.update({"cancel_url": self.get_cancel_url(), "label": f"Re-send {noun}"})
        return kwargs

    def get_context_data(self, **kwargs):
        adapter = get_adapter(self.request)
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "back_url": self.get_cancel_url(),
                "resend_ids": adapter.get_bulk_resend_invite_org_ids(self.request),
            }
        )
        return context

    def form_valid(self, form):
        adapter = get_adapter(self.request)
        pending_organisation_ids = adapter.unstash_bulk_resend_invite_org_ids(
            self.request
        )
        invitations = Invitation.objects.filter(accepted=False).filter(
            organisation_id__in=pending_organisation_ids
        )
        for invite in invitations:
            invite.send_invitation(self.request)

        return super().form_valid(form)


class InviteSuccessView(SiteAdminViewMixin, TemplateView):
    template_name = "site_admin/users_invite_success.html"


class InviteView(SiteAdminViewMixin, CreateView):
    template_name = "site_admin/users_invite.html"
    form_class = InvitationForm

    def get_organisation(self):
        try:
            org_id = self.kwargs.get("pk")
            self.object = Organisation.objects.get(id=org_id)

        except Organisation.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": Organisation._meta.verbose_name}
            )

        return self.object

    def get_success_url(self):
        org_id = self.kwargs.get("pk")
        return reverse(
            "users:org-user-invite-success",
            kwargs={"pk": org_id},
            host=self.request.host.name,
        )

    def get_cancel_url(self):
        org_id = self.kwargs.get("pk")
        return reverse(
            "users:org-user-manage",
            kwargs={"pk": org_id},
            host=self.request.host.name,
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {
                "cancel_url": self.get_cancel_url(),
                "request": self.request,
                # Create empty instance to avoid error in form clean() method,
                # caused by GOVUKModelForm calling clean
                # before InvitationForm is fully instantiated
                "instance": self.form_class.Meta.model(),
                "organisation": self.get_organisation(),
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


class ResendInvitationView(SiteAdminViewMixin, UpdateView):
    model = Invitation
    form_class = ConfirmationForm
    template_name: str = "site_admin/organisation_resend_invite.html"

    organisation: Optional[Organisation] = None

    def get_success_url(self):
        organisation_id = self.kwargs.get(self.pk_url_kwarg)
        return reverse(
            "users:re-invite-success",
            kwargs={"pk": organisation_id},  # Note this is the organisation_id
            host=ADMIN_HOST,
        )

    def get_cancel_url(self):
        return reverse("users:organisation-manage", host=ADMIN_HOST)

    def get_organisation(self):
        if self.organisation is None:
            pk = self.kwargs.get(self.pk_url_kwarg)
            try:
                self.organisation = Organisation.objects.get(id=pk)
            except Organisation.DoesNotExist:
                raise Http404(
                    _("No %(verbose_name)s found matching the query")
                    % {"verbose_name": Organisation._meta.verbose_name}
                )
        return self.organisation

    def get_object(self, queryset=None):
        # Get pending invitation for organisation based on URL state
        queryset = self.get_queryset()

        try:
            # This assumes there is at most one pending invitation.
            # If there are more, only the first is resent.
            return queryset.first()
        except Invitation.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": Invitation._meta.verbose_name}
            )

    def get_queryset(self):
        # Get organisation based on URL state
        organisation = self.get_organisation()

        # Get pending invitations for organisation
        return Invitation.objects.filter(organisation=organisation, accepted=False)

    def get_form_kwargs(self):
        return {"cancel_url": self.get_cancel_url(), "label": "Resend"}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"invite_email": self.object.email})
        return context

    def post(self, request, *args, **kwargs):
        invitation = self.object = self.get_object()
        invitation.send_invitation(self.request)

        # Stash invitation_id to display email on success page
        self.request.session["invitation_sent"] = invitation.id

        return HttpResponseRedirect(self.get_success_url())


class ResendInviteSuccessView(SiteAdminViewMixin, DetailView):
    template_name = "site_admin/organisation_resend_invite_success.html"
    model = Invitation

    def get_object(self, queryset=None):
        try:
            # Get invitation from stash
            invitation_id = self.request.session.pop("invitation_sent")
            return Invitation.objects.get(id=invitation_id)
        except (Invitation.DoesNotExist, KeyError):
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": Invitation._meta.verbose_name}
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {"invite_email": self.object.email, "button_text": "Go back to my account"}
        )
        return context
