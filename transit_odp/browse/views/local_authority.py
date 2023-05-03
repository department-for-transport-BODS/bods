from math import ceil

from transit_odp.browse.views.base_views import BaseListView
from transit_odp.common.views import BaseDetailView
from transit_odp.otc.models import LocalAuthority
from transit_odp.otc.models import Service as OTCService
from transit_odp.publish.requires_attention import get_requires_attention_data_lta


class LocalAuthorityView(BaseListView):
    template_name = "browse/local_authority.html"
    model = LocalAuthority
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        context["ordering"] = self.request.GET.get("ordering", "name")
        all_ltas_current_page = context["object_list"]
        for lta in all_ltas_current_page:
            context[
                "total_in_scope_in_season_services"
            ] = OTCService.objects.get_in_scope_in_season_lta_services(lta).count()

            context["total_services_requiring_attention"] = len(
                get_requires_attention_data_lta(lta)
            )

            try:
                context["services_require_attention_percentage"] = ceil(
                    100
                    * (
                        context["total_services_requiring_attention"]
                        / context["total_in_scope_in_season_services"]
                    )
                )
            except ZeroDivisionError:
                context["services_require_attention_percentage"] = 0

        context["ltas"] = {
            "names": list(all_ltas_current_page.values_list("name", flat=True))
        }
        return context

    def get_queryset(self):
        qs = self.model.objects.filter(name__isnull=False).exclude(name__exact="")

        search_term = self.request.GET.get("q", "").strip()
        if search_term:
            qs = qs.filter(name__icontains=search_term)

        qs = qs.order_by(*self.get_ordering())
        return qs

    def get_ordering(self):
        ordering = self.request.GET.get("ordering", "name")
        if isinstance(ordering, str):
            ordering = (ordering,)
        return ordering


class LocalAuthorityDetailView(BaseDetailView):
    template_name = "browse/local_authority/local_authority_detail.html"
    model = LocalAuthority

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        local_authority = self.object

        context[
            "total_in_scope_in_season_services"
        ] = OTCService.objects.get_in_scope_in_season_lta_services(
            local_authority
        ).count()

        context["total_services_requiring_attention"] = len(
            get_requires_attention_data_lta(local_authority)
        )

        try:
            context["services_require_attention_percentage"] = ceil(
                100
                * (
                    context["total_services_requiring_attention"]
                    / context["total_in_scope_in_season_services"]
                )
            )
        except ZeroDivisionError:
            context["services_require_attention_percentage"] = 0

        return context
