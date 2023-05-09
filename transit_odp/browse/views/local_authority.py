from math import ceil
from django.db.models import Value, CharField, Case, When
from transit_odp.browse.lta_constants import LTAS_DICT
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
        context["object_list"] = self.object_list_lta_mapping(context["object_list"])
        context["q"] = self.request.GET.get("q", "")
        context["ordering"] = self.request.GET.get("ordering", "mapped_name")
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

        ordering = self.request.GET.get("ordering", "mapped_name")
        if ordering == "name":
            context["ltas"] = {
                "names": self.lta_name_mapping(
                    list(self.get_queryset().values_list("name", flat=True))
                )
            }
        elif ordering == "mapped_name":
            ltas_list = self.lta_name_mapping(
                list(self.get_queryset().values_list("name", flat=True))
            )
            ltas_list.sort(key=lambda lta: lta["mapped_name"])
            context["ltas"] = {"names": [lta["mapped_name"] for lta in ltas_list]}
        return context

    def object_list_lta_mapping(self, object_list):
        new_object_list = []
        for otc_name, value_name in LTAS_DICT.items():
            for lta_object in object_list:
                if lta_object.name == otc_name:
                    lta_object.name = value_name
                    new_object_list.append(lta_object)
        return new_object_list

    def lta_name_mapping(self, all_otc_ltas: list):
        ltas_list = []
        for otc_name, value_name in LTAS_DICT.items():
            for otc_lta in all_otc_ltas:
                if otc_lta == otc_name:
                    ltas_list.append({"name": otc_lta, "mapped_name": value_name})
        return ltas_list

    def get_queryset(self):
        lta_name_list = list(LTAS_DICT.keys())
        qs = self.model.objects.filter(name__in=lta_name_list)
        # Add annotated field "mapped_name"
        qs = qs.annotate(
            mapped_name=Case(
                *[
                    When(name=name, then=Value(mapped_name, output_field=CharField()))
                    for name, mapped_name in LTAS_DICT.items()
                ],
                default=Value("", output_field=CharField())
            )
        )
        search_term = self.request.GET.get("q", "").strip()
        if search_term:
            qs = qs.filter(mapped_name__icontains=search_term)

        qs = qs.order_by(*self.get_ordering())
        return qs

    def get_ordering(self):
        ordering = self.request.GET.get("ordering", "mapped_name")
        if ordering == "mapped_name":
            ordering = ("mapped_name",)
        elif isinstance(ordering, str):
            ordering = (ordering,)
        return ordering


class LocalAuthorityDetailView(BaseDetailView):
    template_name = "browse/local_authority/local_authority_detail.html"
    model = LocalAuthority

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        local_authority = self.lta_name_mapping(self.object)

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

    def lta_name_mapping(self, lta_object):
        for otc_name, value_name in LTAS_DICT.items():
            if lta_object.name == otc_name:
                lta_object.name = value_name
        return lta_object
