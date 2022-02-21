from django.db.models import F, QuerySet, Value
from django.db.models.aggregates import Count
from django.db.models.functions import Replace
from django.db.models.query_utils import Q

from transit_odp.otc.constants import (
    FLEXIBLE_REG,
    SCHOOL_OR_WORKS,
    SubsidiesDescription,
)


class ServiceQuerySet(QuerySet):
    def add_service_code(self):
        return self.annotate(
            service_code=Replace("registration_number", Value("/"), Value(":"))
        )

    def add_operator_details(self):
        return self.annotate(
            otc_operator_id=F("operator__operator_id"),
            operator_name=F("operator__operator_name"),
            address=F("operator__address"),
        )

    def add_licence_details(self):
        return self.annotate(
            otc_licence_number=F("licence__number"),
            licence_status=F("licence__status"),
            expiry_date=F("licence__expiry_date"),
            granted_date=F("licence__granted_date"),
        )

    def add_timetable_data_annotations(self):
        return self.add_service_code().add_operator_details().add_licence_details()


class LicenceQuerySet(QuerySet):
    def add_distinct_service_count(self):
        return self.annotate(
            distinct_service_count=Count("services__registration_number", distinct=True)
        )

    def add_school_or_work_count(self):
        return self.annotate(
            school_or_work_count=Count(
                "services",
                filter=Q(services__service_type_description=SCHOOL_OR_WORKS),
            )
        )

    def add_flexible_registration_count(self):
        return self.annotate(
            flexible_registration_count=Count(
                "services",
                filter=Q(services__service_type_description=FLEXIBLE_REG),
            )
        )

    def add_school_or_work_and_subsidies_count(self):
        return self.annotate(
            school_or_work_and_subsidies_count=Count(
                "services",
                filter=Q(
                    services__service_type_description=SCHOOL_OR_WORKS,
                    services__subsidies_description=SubsidiesDescription.YES,
                ),
            )
        )

    def add_school_or_work_and_in_part_count(self):
        return self.annotate(
            school_or_work_and_in_part_count=Count(
                "services",
                filter=Q(
                    services__service_type_description=SCHOOL_OR_WORKS,
                    services__subsidies_description=SubsidiesDescription.IN_PART,
                ),
            )
        )

    def add_data_annotations(self):
        return (
            self.add_distinct_service_count()
            .add_school_or_work_count()
            .add_school_or_work_and_subsidies_count()
            .add_school_or_work_and_in_part_count()
            .add_flexible_registration_count()
        )
