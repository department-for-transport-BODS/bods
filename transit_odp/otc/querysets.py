from typing import TypeVar

from django.db.models import CharField, F, QuerySet, Subquery, Value
from django.db.models.aggregates import Count
from django.db.models.functions import Replace
from django.db.models.query_utils import Q

from transit_odp.organisation.models import Licence as BODSLicence
from transit_odp.organisation.models import TXCFileAttributes
from transit_odp.otc.constants import (
    FLEXIBLE_REG,
    SCHOOL_OR_WORKS,
    SubsidiesDescription,
)

TServiceQuerySet = TypeVar("TServiceQuerySet", bound="ServiceQuerySet")


class ServiceQuerySet(QuerySet):
    def add_service_code(self) -> TServiceQuerySet:
        return self.annotate(
            service_code=Replace(
                "registration_number",
                Value("/", output_field=CharField()),
                Value(":", output_field=CharField()),
            )
        )

    def add_operator_details(self) -> TServiceQuerySet:
        return self.annotate(
            otc_operator_id=F("operator__operator_id"),
            operator_name=F("operator__operator_name"),
            address=F("operator__address"),
        )

    def add_licence_details(self) -> TServiceQuerySet:
        return self.annotate(
            otc_licence_number=F("licence__number"),
            licence_status=F("licence__status"),
            expiry_date=F("licence__expiry_date"),
            granted_date=F("licence__granted_date"),
        )

    def add_timetable_data_annotations(self) -> TServiceQuerySet:
        return self.add_service_code().add_operator_details().add_licence_details()

    def get_all_in_organisation(self, organisation_id: int) -> TServiceQuerySet:
        org_licences = BODSLicence.objects.filter(organisation=organisation_id)
        return (
            self.filter(licence__number__in=Subquery(org_licences.values("number")))
            .add_service_code()
            .order_by("licence__number", "registration_number")
            .distinct("licence__number", "registration_number")
        )

    def get_all_without_exempted_ones(self, organisation_id: int) -> TServiceQuerySet:
        org_licences = BODSLicence.objects.filter(organisation=organisation_id)

        return (
            self.filter(licence__number__in=Subquery(org_licences.values("number")))
            .add_service_code()
            .exclude(
                service_code__in=Subquery(
                    org_licences.add_exempted_service_codes().values(
                        "exempted_service_code"
                    )
                )
            )
            .order_by("licence__number", "registration_number")
            .distinct("licence__number", "registration_number")
        )

    def get_missing_from_organisation(self, organisation_id: int) -> TServiceQuerySet:
        org_licences = BODSLicence.objects.filter(organisation=organisation_id)
        org_timetables = TXCFileAttributes.objects.filter(
            revision__dataset__organisation_id=organisation_id
        ).get_active_live_revisions()
        return (
            self.filter(licence__number__in=Subquery(org_licences.values("number")))
            .add_service_code()
            .exclude(service_code__in=Subquery(org_timetables.values("service_code")))
            .exclude(
                service_code__in=Subquery(
                    org_licences.add_exempted_service_codes().values(
                        "exempted_service_code"
                    )
                )
            )
            .order_by("licence__number", "registration_number", "service_number")
            .distinct("licence__number", "registration_number", "service_number")
        )

    def search(self, keywords: str) -> TServiceQuerySet:
        """Searches License code, service number, and line number in
        OTCService using keywords.
        """
        licence_number_keywords = Q(licence__number__icontains=keywords)
        service_number_keywords = Q(service_number__icontains=keywords)
        registration_number_keywords = Q(registration_number__icontains=keywords)
        return self.filter(
            licence_number_keywords
            | service_number_keywords
            | registration_number_keywords
        ).distinct()


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
