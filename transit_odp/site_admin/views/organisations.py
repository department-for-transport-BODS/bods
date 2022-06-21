from datetime import datetime
from typing import List, TypedDict

from allauth.account.adapter import get_adapter
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpResponseRedirect
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView
from django.views.generic.base import ContextMixin
from django.views.generic.edit import FormMixin
from django_filters.views import FilterView
from django_hosts import reverse
from django_tables2 import SingleTableView

from config.hosts import ADMIN_HOST
from transit_odp.common.forms import ConfirmationForm
from transit_odp.common.view_mixins import RangeFilterContentMixin
from transit_odp.organisation.forms.organisation_profile import NOCFormset
from transit_odp.organisation.models import Organisation
from transit_odp.site_admin.filters import OrganisationFilter
from transit_odp.site_admin.forms import (
    BulkResendInvitesForm,
    OrganisationForm,
    OrganisationNameForm,
)
from transit_odp.site_admin.tables import OrganisationTable
from transit_odp.users.constants import AccountType, AgentUserType
from transit_odp.users.models import AgentUserInvite, Invitation
from transit_odp.users.views.mixins import SiteAdminViewMixin

User = get_user_model()

__all__ = [
    "ManageOrganisationView",
    "OrganisationArchiveSuccessView",
    "OrganisationArchiveView",
    "OrganisationCreateSuccessView",
    "OrganisationCreateView",
    "OrganisationDetailView",
    "OrganisationEditSuccessView",
    "OrganisationEditView",
    "OrganisationListView",
    "OrganisationUsersManageView",
]


class ManageOrganisationView(
    SiteAdminViewMixin, RangeFilterContentMixin, SingleTableView
):
    template_name = "site_admin/organisations_manage.html"
    table_class = OrganisationTable
    model = Organisation

    # state to generate range_filters
    ranges = ["a-f", "g-l", "m-r", "s-z", "0-9"]
    lookup = "name__iregex"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.add_registration_complete().add_last_active().add_invite_sent()

    def get_table_data(self):
        data = super().get_table_data()

        # Apply range filter
        range_filter_value = self.get_filter_param()
        data = self.apply_range_filter(data, range_filter_value)

        return data

    def get_context_data(self, *args, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs.pop(
            "organisation_list"
        )  # remove as it will not be in sync with object_list after filtering

        # Generate range filters
        qs = self.get_queryset()
        filter_context = self.get_filter_context(qs)
        kwargs.update(**filter_context)
        kwargs["filter"] = OrganisationFilter()

        return kwargs


class OrganisationArchiveSuccessView(SiteAdminViewMixin, DetailView):
    template_name = "site_admin/organisation_archive_success.html"
    model = Organisation


class OrganisationArchiveView(SiteAdminViewMixin, UpdateView):
    template_name = "site_admin/organisation_archive.html"
    model = Organisation
    form_class = ConfirmationForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {
                "cancel_url": reverse(
                    "users:organisation-detail",
                    host=ADMIN_HOST,
                    kwargs={"pk": self.object.id},
                )
            }
        )
        kwargs.pop("instance", None)
        return kwargs

    def get_success_url(self):
        return reverse(
            "users:organisation-archive-success",
            kwargs={"pk": self.object.id},
            host=ADMIN_HOST,
        )

    def form_valid(self, form):
        organisation = self.get_object()

        # set organisation to active/inactive
        organisation.is_active = not organisation.is_active
        organisation.save(update_fields=["is_active"])

        # set organisation users to 'inactive'
        users = User.objects.filter(organisations=organisation).exclude(
            account_type=AgentUserType
        )
        if users:
            users.update(is_active=organisation.is_active)

        agents = User.objects.filter(
            organisations=organisation, account_type=AgentUserType
        )
        for agent in agents:
            agent.organisations.remove(organisation)

        return HttpResponseRedirect(self.get_success_url())


class OrganisationCreateSuccessView(SiteAdminViewMixin, TemplateView):
    template_name = "site_admin/organisation_create_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invite_email = get_adapter(self.request).unstash_invite_email(self.request)
        context.update({"invite_email": invite_email})
        return context


class OrganisationCreateView(SiteAdminViewMixin, CreateView):
    model = Organisation
    template_name = "site_admin/organisation_form.html"
    form_class = OrganisationNameForm

    def get_success_url(self):
        return reverse(
            "users:create-organisation-success",
            host=ADMIN_HOST,
            args=[self.object.id],
        )

    def get_cancel_url(self):
        return reverse(
            "users:organisation-manage",
            host=ADMIN_HOST,
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["cancel_url"] = self.get_cancel_url()
        return kwargs

    def form_valid(self, form):
        noc_codes = NOCFormset(self.request.POST)
        with transaction.atomic():
            self.object = form.save()
            email = form.cleaned_data.get("email")
            if noc_codes.is_valid():
                noc_codes.instance = self.object
                noc_codes.save()

            self.stash_data(form)
            invitation = Invitation.create(
                inviter=self.request.user,
                email=email,
                account_type=AccountType.org_admin.value,
                organisation=self.object,
                is_key_contact=True,
            )
            invitation.send_invitation(self.request)
        return HttpResponseRedirect(self.get_success_url())

    def stash_data(self, form):
        """Stash valid data in session for subsequent view to unstash"""
        get_adapter(self.request).stash_invite_email(
            self.request, form.cleaned_data["email"]
        )


class OrganisationDetailView(SiteAdminViewMixin, DetailView):
    model = Organisation
    template_name = "site_admin/organisation_detail.html"

    class Properties(TypedDict):
        agents: List[User]
        avls_created: int
        created: datetime
        date_added: datetime
        fares_created: int
        is_active: bool
        key_contact: str
        last_active: datetime
        nocs: List[str]
        operator_id: int
        registration_complete: bool
        short_name: str
        status: str
        timetables_created: int

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .prefetch_related("nocs")
            .add_key_contact_email()
            .add_registration_complete()
            .add_last_active()
            .add_status()
            .add_published_dataset_count_types()
        )
        return qs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        organisation = self.object
        agent_users = list(
            organisation.users.filter(account_type=AgentUserType, is_active=True)
        )
        nocs = [code.noc for code in organisation.nocs.all()]
        properties = {
            "agents": agent_users,
            "avls_created": organisation.published_avl_count,
            "date_added": organisation.created,
            "fares_created": organisation.published_fares_count,
            "is_active": organisation.is_active,
            "key_contact": organisation.key_contact_email,
            "last_active": organisation.last_active,
            "name": organisation.name,
            "nocs": nocs,
            "operator_id": organisation.id,
            "registration_complete": organisation.registration_complete,
            "short_name": organisation.short_name,
            "status": organisation.status,
            "timetables_created": organisation.published_timetable_count,
        }
        data.update({"properties": self.Properties(**properties)})
        return data


class OrganisationEditSuccessView(SiteAdminViewMixin, TemplateView):
    template_name = "site_admin/organisation_edit_success.html"


class OrganisationEditView(SiteAdminViewMixin, UpdateView):
    template_name = "site_admin/organisation_edit.html"
    model = Organisation
    form_class = OrganisationForm

    def get_success_url(self):
        org_id = self.kwargs.get("pk", None)
        return reverse(
            "users:edit-organisation-success",
            kwargs={"pk": org_id},
            host=ADMIN_HOST,
        )

    def get_cancel_url(self):
        org_id = self.kwargs.get("pk", None)
        return reverse(
            "users:organisation-detail",
            kwargs={"pk": org_id},
            host=ADMIN_HOST,
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

    def get_queryset(self):
        qs = super().get_queryset()
        qs.add_key_contact_email().add_registration_complete()
        return qs


class OrganisationListView(SiteAdminViewMixin, FilterView, SingleTableView, FormMixin):
    """A FilterView for displaying all the Organisations in BODS."""

    template_name = "site_admin/organisation_list.html"
    model = Organisation
    filterset_class = OrganisationFilter
    table_class = OrganisationTable
    form_class = BulkResendInvitesForm
    _form_instance = None

    def get_form(self, form_class=None):
        """
        Will always return the same instance of the form
        """
        if self._form_instance:
            return self._form_instance
        self._form_instance = super().get_form(form_class)
        return self.get_form(form_class)

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .add_registration_complete()
            .add_last_active()
            .add_invite_sent()
            .add_status()
            .add_first_letter()
            .order_by("name")
        )
        search_term = self.request.GET.get("q")
        if search_term:
            qs = qs.filter(name__istartswith=search_term)

        return qs

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"data": self.request.GET, "orgs": self.get_queryset()})
        return kwargs

    def get_table_kwargs(self):
        form = self.get_form()
        # cleaned_data is only defined when form.is_valid() is called.
        # So if its not defined then we are using the filter if it is
        # then we are using the bulk resend feature.
        return {
            "in_error": bool(form.errors),
            "checked_ids": getattr(form, "cleaned_data", {"invites": []})["invites"],
        }

    def get_success_url(self):
        return reverse("users:bulk-resend-invite", host=self.request.host.name)

    def get(self, request, *args, **kwargs):
        adapter = get_adapter(request)
        adapter.unstash_bulk_resend_invite_org_ids(request)
        form = self.get_form()
        # need to run is_valid so we can get the cleaned data.
        form_is_valid = form.is_valid()
        if not form.cleaned_data["bulk_invite"] or not form_is_valid:
            return super().get(request, *args, **kwargs)

        if form_is_valid:
            adapter.stash_bulk_resend_invite_org_ids(
                request, form.cleaned_data["invites"]
            )
            return self.form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active_orgs = self.model.objects.all()
        operators = {
            "names": [name for name in active_orgs.values_list("name", flat=True)]
        }
        context["operators"] = operators
        context["q"] = self.request.GET.get("q", "").strip()
        context["letters"] = self.request.GET.getlist("letters")
        return context


class OrganisationUsersManageView(DetailView, SiteAdminViewMixin, ContextMixin):
    template_name = "site_admin/organisation_user_manage.html"
    model = Organisation

    def get_queryset(self):
        return Organisation.objects.all()

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
