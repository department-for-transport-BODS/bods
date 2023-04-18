from transit_odp.browse.views.base_views import BaseListView
from transit_odp.common.views import BaseDetailView
from transit_odp.otc.models import LocalAuthority


class LocalAuthorityView(BaseListView):
    template_name = "browse/local_authority.html"
    model = LocalAuthority
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        context["ordering"] = self.request.GET.get("ordering", "name")
        all_ltas = self.model.objects.filter(name__isnull=False)
        ltas = {"names": [name for name in all_ltas.values_list("name", flat=True)]}

        context["ltas"] = ltas
        return context

    def get_queryset(self):
        qs = self.model.objects.filter(name__isnull=False)

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
