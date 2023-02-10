from django.http import HttpResponse
from django.utils.timezone import now
from django.views import View
from django_tables2 import SingleTableView

from transit_odp.organisation.csv.service_codes import ServiceCodesCSV
from transit_odp.organisation.models import Organisation
from transit_odp.otc.models import Service as OTCService
from transit_odp.publish.requires_attention import get_requires_attention_data
from transit_odp.timetables.tables import RequiresAttentionTable
from transit_odp.users.views.mixins import OrgUserViewMixin


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
        context["services_requiring_attention"] = len(self.object_list)
        context["q"] = self.request.GET.get("q", "").strip()
        return context

    def get_table_data(self):
        keywords = self.request.GET.get("q", "").strip().lower()
        if keywords:
            return [
                service
                for service in self.object_list
                if keywords in service["licence_number"].lower()
                or keywords in service["service_code"].lower()
                or keywords in service["line_number"].lower()
            ]
        return self.object_list

    def get_queryset(self):
        org_id = self.kwargs["pk1"]
        return get_requires_attention_data(org_id)


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
