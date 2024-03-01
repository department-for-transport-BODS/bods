from django.contrib.auth import get_user_model
from django.http import Http404, HttpResponseRedirect
from django.utils.translation import gettext as _
from django.views.generic import DetailView, UpdateView
from django_hosts import reverse

from transit_odp.common.forms import ConfirmationForm
from transit_odp.organisation.forms.management import UserEditForm
from transit_odp.organisation.models import Organisation
from transit_odp.users.views.mixins import SiteAdminViewMixin

__all__ = [
    "UserArchiveSuccessView",
    "UserDetailView",
    "UserEditSuccessView",
    "UserEditView",
    "UserIsActiveView",
]

User = get_user_model()


class UserArchiveSuccessView(SiteAdminViewMixin, DetailView):
    model = User
    template_name = "site_admin/user_archive_success.html"
    pk_url_kwarg = "pk1"


class UserDetailView(SiteAdminViewMixin, DetailView):
    model = User
    template_name = "site_admin/users_manage_detail.html"
    pk_url_kwarg = "pk1"

    def get_queryset(self):
        org_id = self.kwargs.get("pk", -1)
        return User.objects.filter(organisations__id=org_id)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        user = self.get_object()
        if user.is_agent_user:
            invite = user.agent_invitations.filter(
                organisation_id=self.kwargs.get("pk")
            ).first()
            context["invite"] = invite
        context["organisation"] = Organisation.objects.get(id=self.kwargs["pk"])
        context["user"] = user

        return context


class UserEditSuccessView(SiteAdminViewMixin, DetailView):
    model = User
    template_name = "site_admin/users_manage_edit_success.html"
    pk_url_kwarg = "pk1"


class UserEditView(SiteAdminViewMixin, UpdateView):
    template_name = "site_admin/users_manage_edit.html"
    form_class = UserEditForm
    context_object_name = "user"
    organisation = None

    def get_success_url(self):
        return reverse(
            "users:manage-user-edit-success",
            host=self.request.host.name,
            kwargs={"pk1": self.object.id, "pk": self.organisation.id},
        )

    def get_cancel_url(self):
        return reverse(
            "users:manage-user-detail",
            host=self.request.host.name,
            kwargs={"pk1": self.object.id, "pk": self.organisation.id},
        )

    def get_object(self, queryset=None):
        try:
            user_id = self.kwargs.get("pk1", None)
            org_id = self.kwargs.get("pk", None)

            obj = User.objects.get(id=user_id)
            self.organisation = Organisation.objects.get(id=org_id)

        except queryset.model.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s or %(organisation) found matching the query ")
                % {
                    "verbose_name": User._meta.verbose_name,
                    "organisation": Organisation._meta.verbose_name,
                }
            )
        return obj

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"cancel_url": self.get_cancel_url()})
        return kwargs

    def get_queryset(self):
        try:
            organisation = Organisation.objects.get(id=self.organisation.id)
            # The user can only change users within their organisation
            return organisation.users.all().exclude(
                id=self.object.id
            )  # the user cannot archive themselves
        except Organisation.DoesNotExist:
            raise Http404(
                _(f"No {Organisation._meta.verbose_name} found matching the query")
            )


class UserIsActiveView(SiteAdminViewMixin, UpdateView):
    template_name = "site_admin/user_archive.html"
    form_class = ConfirmationForm
    organisation = None

    def get_success_url(self):
        return reverse(
            "users:org-user-archive-success",
            host=self.request.host.name,
            kwargs={"pk1": self.object.id, "pk": self.organisation.id},
        )

    def get_cancel_url(self):
        return reverse(
            "users:manage-user-detail",
            host=self.request.host.name,
            kwargs={"pk1": self.object.id, "pk": self.organisation.id},
        )

    def get_queryset(self):
        try:
            organisation = Organisation.objects.get(id=self.organisation.id)
            # The user can only change users within their organisation
            return organisation.user_set.all().exclude(
                id=self.object.id
            )  # the user cannot archive themselves
        except Organisation.DoesNotExist:
            raise Http404(
                _(f"No {Organisation._meta.verbose_name} found matching the query")
            )

    def get_form_kwargs(self):
        # Note - probably a better way to handle this. As we are using a forms.Form
        # class to display a simple
        # confirmation button, rather than a forms.ModelForm, we need to prevent the
        # form from being initialised with instance
        kwargs = super().get_form_kwargs()
        kwargs.pop("instance", None)
        kwargs.update({"cancel_url": self.get_cancel_url()})
        return kwargs

    def get_object(self, queryset=None):
        try:
            user_id = self.kwargs.get("pk1", None)
            org_id = self.kwargs.get("pk", None)

            obj = User.objects.get(id=user_id)
            self.organisation = Organisation.objects.get(id=org_id)

        except queryset.model.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s or %(organisation) found matching the query ")
                % {
                    "verbose_name": User._meta.verbose_name,
                    "organisation": Organisation._meta.verbose_name,
                }
            )
        return obj

    def form_valid(self, form):
        user = self.object = self.get_object()
        user.is_active = not user.is_active
        user.save(update_fields=["is_active"])
        return HttpResponseRedirect(self.get_success_url())
