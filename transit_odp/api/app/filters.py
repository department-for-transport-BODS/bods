from django_filters import rest_framework as filters
from django.db.models.query import QuerySet

import pandas as pd

from transit_odp.publish.requires_attention import get_line_level_txc_map_service_base
from transit_odp.transmodel.models import ServicePattern
from transit_odp.otc.models import Service as OTCService
from django.db.models import Q


class ServicePatternFilterSet(filters.FilterSet):
    service_codes = filters.CharFilter(
        field_name="services__service_code", method="filter_by_service_codes"
    )

    licence_number = filters.CharFilter(method="filter_by_licence_number")

    class Meta:
        model = ServicePattern
        fields = ["revision", "line_name", "service_codes", "licence_number"]

    def filter_by_service_codes(self, queryset, name, value):
        service_codes_list = value.split(",")
        return queryset.filter(services__service_code__in=service_codes_list)

    def filter_by_licence_number(
        self, queryset: QuerySet, _: str, value: str
    ) -> QuerySet:
        """
        Filter service patterns by the services present in the licence number
        If the Txc file present for a service we will search for specific revision id
        and txcattribute file id
        but it not query set was returning all rows so we will search for
        service code and line name to get blank resposne


        Args:
            queryset (QuerySet): Service Pattern Queryset
            _ (str): name of the field
            value (str): Licence number value

        Returns:
            QuerySet: Queryset with services filter applied for licence
        """
        otc_services_df = pd.DataFrame.from_records(
            OTCService.objects.filter(licence__number=value).values(
                "registration_number", "service_number"
            )
        )

        otc_services_df["registration_number"] = otc_services_df[
            "registration_number"
        ].apply(lambda x: x.replace("/", ":"))
        otc_services_df["service_number"] = otc_services_df["service_number"].apply(
            lambda x: str(x).split("|")
        )
        otc_services_df = otc_services_df.explode("service_number")

        txc_map = get_line_level_txc_map_service_base(
            list(otc_services_df["registration_number"])
        )

        query = Q()
        otc_services_df.reset_index(inplace=True)
        for _, row in otc_services_df.iterrows():
            txc_file = txc_map.get(
                (row["registration_number"], row["service_number"]), ""
            )
            if txc_file:
                query |= Q(
                    services__service_code=row["registration_number"],
                    line_name=row["service_number"],
                    services__revision_id=txc_file.revision_id,
                    services__txcfileattributes_id=txc_file.id,
                )
            else:
                query |= Q(
                    services__service_code=row["registration_number"],
                    line_name=row["service_number"],
                )

        return queryset.filter(query)
