from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import TemplateView

from transit_odp.api.views.base import DatasetViewSet
from transit_odp.organisation.constants import TimetableType
from transit_odp.organisation.models import Dataset


class TimetablesApiView(LoginRequiredMixin, TemplateView):
    template_name = "swagger_ui/timetables.html"


class TimetablesViewSet(DatasetViewSet):
    def get_queryset(self):
        qs = (
            Dataset.objects.get_published()
            .get_live_dq_score()
            .get_active_org()
            .get_viewable_statuses()
            .add_is_live_pti_compliant()
            .add_organisation_name()
            .select_related("live_revision")
            .prefetch_related("organisation__nocs")
            .prefetch_related("live_revision__admin_areas")
            .prefetch_related("live_revision__localities")
            .prefetch_related("live_revision__services")
        )
        qs = qs.filter(dataset_type=TimetableType)

        status_list = self.request.GET.getlist("status", [])
        if not self.request.resolver_match.kwargs:
            if not status_list or "" in status_list:
                status_list = ["live"]
            elif status_list and "" not in status_list:
                status_list = [
                    status.replace("published", "live") for status in status_list
                ]
            qs = qs.filter(live_revision__status__in=status_list)
        keywords = self.request.GET.get("search", "").strip()
        if keywords:
            # TODO - enable full-text search
            qs = qs.filter(
                Q(live_revision__name__icontains=keywords)
                | Q(live_revision__description__icontains=keywords)
                | Q(organisation_name__icontains=keywords)
                | Q(live_revision__admin_areas__name__icontains=keywords)
            )

        # Make the search results distinct since there will be duplicates from the
        # join with admin_areas
        qs = qs.order_by("id").distinct()

        return qs
