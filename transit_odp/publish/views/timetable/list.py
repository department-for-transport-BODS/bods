from typing import List, Tuple, Type

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.forms import Form
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.timezone import now
from django.utils.translation import gettext as _
from django.views import View
from django.views.generic.edit import BaseDeleteView
from django_hosts import reverse
from django_tables2 import SingleTableView
from formtools.wizard.views import SessionWizardView

import config.hosts
from transit_odp.common.view_mixins import BODSBaseView
from transit_odp.common.views import BaseUpdateView
from transit_odp.organisation.constants import TimetableType
from transit_odp.organisation.csv.service_codes import ServiceCodesCSV
from transit_odp.organisation.models import Organisation
from transit_odp.organisation.models.data import SeasonalService
from transit_odp.organisation.models.organisations import Licence
from transit_odp.otc.models import Service as OTCService
from transit_odp.publish.forms import (
    SeasonalServiceEditDateForm,
    SeasonalServiceLicenceNumberForm,
)
from transit_odp.publish.tables import DatasetTable
from transit_odp.publish.views.base import BasePublishListView
from transit_odp.timetables.proxies import TimetableDataset
from transit_odp.timetables.tables import RequiresAttentionTable, SeasonalServiceTable
from transit_odp.users.views.mixins import OrgUserViewMixin


class ListView(BasePublishListView):
    template_name = "publish/feed_list.html"

    dataset_type = TimetableType
    model = TimetableDataset
    table = DatasetTable

    page_title_datatype = "timetables"
    publish_url_name = "new-feed"
    nav_url_name = "feed-list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org_id = context["pk1"]
        context["all_service_codes"] = OTCService.objects.get_all_without_exempted_ones(
            org_id
        ).count()
        context[
            "missing_service_codes"
        ] = OTCService.objects.get_missing_from_organisation(org_id).count()
        context[
            "seasonal_services_counter"
        ] = SeasonalService.objects.get_count_in_organisation(org_id)
        return context


class RequiresAttentionView(OrgUserViewMixin, SingleTableView):
    template_name = "publish/requires_attention.html"
    model = OTCService
    table_class = RequiresAttentionTable
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org_id = self.kwargs["pk1"]
        context["org_id"] = org_id
        data_owner = self.organisation.name if self.request.user.is_agent_user else "My"

        context["ancestor"] = f"Review {data_owner} Timetables Data"
        context[
            "num_missing_services"
        ] = OTCService.objects.get_missing_from_organisation(org_id).count()

        context["not_empty"] = self.object_list.count()
        context["q"] = self.request.GET.get("q", "").strip()
        return context

    def get_queryset(self):
        org_id = self.kwargs["pk1"]
        qs = OTCService.objects.get_missing_from_organisation(org_id)

        keywords = self.request.GET.get("q", "").strip()
        if keywords:
            qs = qs.search(keywords)

        return qs


class ServiceCodeView(OrgUserViewMixin, View):
    def get(self, *args, **kwargs):
        self.org = Organisation.objects.get(id=kwargs["pk1"])
        return self.render_to_response()

    def render_to_response(self):
        csv_filename = (
            f"{now():%d%m%y}_timetables_datastatus_by_service_code_"
            f"{self.org.name}.csv"
        )
        csv_export = ServiceCodesCSV(self.org.id)
        file_ = csv_export.to_csv()
        response = HttpResponse(file_, content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={csv_filename}"
        return response


class SeasonalServiceView(OrgUserViewMixin, SingleTableView):
    template_name = "publish/seasonal_services.html"
    model = SeasonalService
    table_class = SeasonalServiceTable
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org_id = self.kwargs["pk1"]
        context["pk1"] = org_id
        context[
            "seasonal_services_counter"
        ] = SeasonalService.objects.get_count_in_organisation(org_id)
        return context

    def get_table_data(self, **kwargs):
        # org_id = self.request.GET.get("pk1")
        org_id = self.kwargs["pk1"]
        return SeasonalService.objects.filter(licence__organisation_id=org_id)


class SeasonalServiceWizardAddNewView(
    BODSBaseView, OrgUserViewMixin, SessionWizardView
):
    SELECT_PSV_STEP = "select_psv_licence_number"
    PROVIDE_OPERATING_DATE = "provide_operating_dates"

    form_list: List[Tuple[str, Type[Form]]] = [
        (SELECT_PSV_STEP, SeasonalServiceLicenceNumberForm),
        (PROVIDE_OPERATING_DATE, SeasonalServiceEditDateForm),
    ]

    step_context = {
        SELECT_PSV_STEP: {"step_title": _("Seasonal service operating dates")},
        PROVIDE_OPERATING_DATE: {"step_title": _("Seasonal service operating dates")},
    }

    def get_queryset(self):
        org_id = self.request.GET.get("pk1")
        return Licence.objects.filter(organisation_id=org_id)

    def get_template_names(self):
        return "publish/seasonal_services_add_date_form.html"

    def get_context_data(self, form, **kwargs):
        kwargs = super().get_context_data(form, **kwargs)
        kwargs.update(self.step_context[self.SELECT_PSV_STEP])
        kwargs.update({"form_list": list(self.form_list.items())[0:1]})
        kwargs.update({"current_step": self.steps.current, "pk1": self.kwargs["pk1"]})
        return kwargs

    @transaction.atomic
    def done(self, form_list, **kwargs):
        org_id = self.kwargs["pk1"]
        all_data = self.get_all_cleaned_data()
        SeasonalService.objects.filter(licence__organisation_id=org_id).create(
            licence=all_data["licence"],
            registration_code=all_data["registration_code"],
            start=all_data["start"],
            end=all_data["end"],
        )
        return HttpResponseRedirect(
            reverse(
                "seasonal-service",
                kwargs={"pk1": org_id},
                host=config.hosts.PUBLISH_HOST,
            )
        )


class SeasonalServiceEditDateView(OrgUserViewMixin, SingleTableView):
    template_name = "publish/seasonal_services.html"
    model = SeasonalService
    table_class = SeasonalServiceTable
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org_id = self.kwargs["pk1"]
        context["pk1"] = org_id
        # uncomment when BODP-5626 merged
        context[
            "seasonal_services_counter"
        ] = 12  # SeasonalService.objects.get_seasonal_service_counter(org_id)
        return context


class SeasonalServiceDelete(OrgUserViewMixin, BaseDeleteView):
    template_name = None
    model = SeasonalService

    def get(self, request, *args, **kwargs):
        seasonal_service_id = kwargs["pk"]
        SeasonalService.objects.get(id=seasonal_service_id).delete()
        return HttpResponseRedirect(
            reverse(
                "seasonal-service",
                kwargs={"pk1": kwargs["pk1"]},
                host=config.hosts.PUBLISH_HOST,
            )
        )
        # return super().get(request, *args, **kwargs)

    # def get_success_url(self):
    #     return reverse(
    #         "seasonal-service",
    #         kwargs={"pk1": self.kwargs["pk1"]},
    #         host=config.hosts.PUBLISH_HOST,
    #     )

    # def form_valid(self, form):
    #     try:
    #         SeasonalService.objects.get(id=102).delete()
    #     except:
    #         pass
    #     return HttpResponseRedirect(self.get_success_url())


# class SeasonalServiceDelete(OrgUserViewMixin, BaseUpdateView):
#     template_name = "publish/seasonal_service_delete.html"
#     model = SeasonalService
#     fields = "__all__"

#     def as_view(self, *args, **kwargs) -> Any:
#         super().as_view()
#         breakpoint()
#         return self.form_valid()

#     def get_success_url(self):

#         return reverse(
#             "seasonal-service",
#             kwargs={"pk1": self.kwargs["pk1"]},
#             host=config.hosts.PUBLISH_HOST,
#         )

#     def form_valid(self):
#         try:
#             SeasonalService.objects.get(id=113).delete()
#         except:
#             pass
#         return HttpResponseRedirect(self.get_success_url())


def seasonal_service_delete(request, *args, **kwargs):
    SeasonalService.objects.get(id=115).delete()
    return HttpResponseRedirect(
        reverse(
            "seasonal-service",
            kwargs={"pk1": kwargs["pk1"]},
            host=config.hosts.PUBLISH_HOST,
        )
    )
