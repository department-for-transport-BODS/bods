from typing import List, Tuple, Type

from django.contrib.auth.views import FormView
from django.db import transaction
from django.forms import Form
from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _
from django_hosts import reverse
from django_tables2 import SingleTableView
from formtools.wizard.views import SessionWizardView

import config.hosts
from transit_odp.common.view_mixins import BODSBaseView
from transit_odp.common.views import BaseUpdateView
from transit_odp.organisation.models.data import SeasonalService
from transit_odp.organisation.models.organisations import Organisation
from transit_odp.publish.forms.seasonal_services import (
    DeleteForm,
    EditDateForm,
    EditRegistrationCodeDateForm,
    LicenceNumberForm,
)
from transit_odp.timetables.tables import SeasonalServiceTable, get_table_page
from transit_odp.users.constants import DATASET_MANAGE_TABLE_PAGINATE_BY
from transit_odp.users.views.mixins import OrgUserViewMixin


class ListHomeView(OrgUserViewMixin, SingleTableView):
    template_name = "publish/seasonal_services/index.html"
    model = SeasonalService
    table_class = SeasonalServiceTable
    paginate_by = DATASET_MANAGE_TABLE_PAGINATE_BY

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.org_id = self.kwargs["pk1"]
        seasonal_service_counter = SeasonalService.objects.get_count_in_organisation(
            self.org_id
        )
        context.update(
            {
                "pk1": self.org_id,
                "organisation": Organisation.objects.get(id=self.org_id),
                "seasonal_services_counter": seasonal_service_counter,
            }
        )
        return context

    def get_queryset(self):
        self.org_id = self.kwargs["pk1"]
        qs = super().get_queryset()
        return (
            qs.filter(licence__organisation_id=self.org_id)
            .add_registration_number()
            .order_by("end")
        )


class WizardAddNewView(BODSBaseView, OrgUserViewMixin, SessionWizardView):
    SELECT_PSV_STEP = "select_psv_licence_number"
    PROVIDE_OPERATING_DATE = "provide_operating_dates"

    form_list: List[Tuple[str, Type[Form]]] = [
        (SELECT_PSV_STEP, LicenceNumberForm),
        (PROVIDE_OPERATING_DATE, EditRegistrationCodeDateForm),
    ]

    step_context = {
        SELECT_PSV_STEP: {"step_title": _("Seasonal service operating dates")},
        PROVIDE_OPERATING_DATE: {"step_title": _("Seasonal service operating dates")},
    }

    template_name = "publish/seasonal_services/add_new.html"

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form, **kwargs)
        context.update(
            self.step_context[self.SELECT_PSV_STEP],
        )
        context.update(
            {
                "current_step": self.steps.current,
                "organisation": Organisation.objects.get(id=self.org_id),
                "pk1": self.org_id,
            }
        )
        return context

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs()
        self.org_id = self.kwargs["pk1"]
        self.page = self.request.GET.get("page", None)
        kwargs.update(
            {
                "org_id": self.org_id,
                "page": self.page,
            }
        )
        if step == self.PROVIDE_OPERATING_DATE:
            licence = self.get_cleaned_data_for_step(self.SELECT_PSV_STEP).get(
                "licence"
            )
            kwargs["licence"] = licence
        return kwargs

    @transaction.atomic
    def done(self, form_list, **kwargs):
        all_data = self.get_all_cleaned_data()
        SeasonalService.objects.filter(licence__organisation_id=self.org_id).create(
            licence=all_data["licence"],
            registration_code=all_data["registration_code"],
            start=all_data["start"],
            end=all_data["end"],
        )
        return HttpResponseRedirect(
            reverse(
                "seasonal-service",
                kwargs={"pk1": self.org_id},
                host=config.hosts.PUBLISH_HOST,
            )
            + get_table_page(self.page)
        )


class EditDateView(OrgUserViewMixin, BaseUpdateView):
    template_name = "publish/seasonal_services/form.html"
    form_class = EditDateForm
    model = SeasonalService

    def get_queryset(self):
        self.org_id = self.kwargs.get("pk1")
        qs = super().get_queryset()
        return qs.filter(licence__organisation__id=self.org_id).distinct("id")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.page = self.request.GET.get("page", None)
        kwargs.update(
            {
                "org_id": self.org_id,
                "page": self.page,
            }
        )
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "pk1": self.org_id,
                "organisation": Organisation.objects.get(id=self.org_id),
            }
        )
        return context

    @transaction.atomic
    def form_valid(self, form):
        self.object.start = form.cleaned_data["start"]
        self.object.end = form.cleaned_data["end"]
        self.object.save()
        return HttpResponseRedirect(
            reverse(
                "seasonal-service",
                kwargs={"pk1": self.org_id},
                host=config.hosts.PUBLISH_HOST,
            )
            + get_table_page(self.page)
        )


class DeleteView(OrgUserViewMixin, FormView):
    form_class = DeleteForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["org_id"] = self.kwargs["pk1"]
        return kwargs

    def get_success_url(self):
        page = self.request.GET.get("page", None)
        return reverse(
            "seasonal-service",
            kwargs={"pk1": self.kwargs["pk1"]},
            host=config.hosts.PUBLISH_HOST,
        ) + get_table_page(page)

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
