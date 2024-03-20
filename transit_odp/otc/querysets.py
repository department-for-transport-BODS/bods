from datetime import timedelta
from typing import TypeVar

from django.db.models import (
    Case,
    CharField,
    Count,
    DateField,
    ExpressionWrapper,
    F,
    OuterRef,
    QuerySet,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Replace, TruncDate
from django.db.models.query_utils import Q
from django.utils import timezone

from transit_odp.common.querysets import GroupConcat
from transit_odp.naptan.models import AdminArea
from transit_odp.organisation.constants import ENGLISH_TRAVELINE_REGIONS
from transit_odp.organisation.models import Licence as BODSLicence
from transit_odp.organisation.models import (
    SeasonalService,
    ServiceCodeExemption,
    TXCFileAttributes,
)
from transit_odp.otc.constants import (
    API_TYPE_WECA,
    FLEXIBLE_REG,
    SCHOOL_OR_WORKS,
    SubsidiesDescription,
)
from transit_odp.organisation.models import Licence as OrganisationLicence

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

    def add_traveline_region_weca(self) -> TServiceQuerySet:
        """
        Traveline Region that the UI LTA maps to via the admin area table
        by joining atco code. If Traveline Region value is multiple in the row
        for this service code it should sperated with |.

        Returns:
            TServiceQuerySet: QuerySet with anotated column
        """
        return self.annotate(
            traveline_region_weca=GroupConcat(
                AdminArea.objects.filter(atco_code=OuterRef("atco_code")).values(
                    "traveline_region_id"
                ),
                delimiter="|",
                distinct=True,
            )
        )

    def add_traveline_region_otc(self) -> TServiceQuerySet:
        """
        Traveline Region that the UI LTA maps to via LocalAuthority table
        by joining ui lta table and then admin area table via ui lta and
        get the traveline_region_id.If Traveline Region value is multiple
        in the row for this service code it should sperated with |.

        Returns:
            TServiceQuerySet: QuerySet with anotated column
        """
        return self.annotate(
            traveline_region_otc=GroupConcat(
                "registration__ui_lta__naptan_ui_lta_records__traveline_region_id",
                delimiter="|",
                distinct=True,
            )
        )

    def add_traveline_region_details(self):
        """Fetch traveline reason id for WECA and OTC

        Returns:
            TServiceQuerySet: QuerySet with anotated column
        """
        return self.annotate(
            traveline_region=Case(
                When(
                    Q(api_type=API_TYPE_WECA),
                    then=F("traveline_region_weca"),
                ),
                default=F("traveline_region_otc"),
                output_field=CharField(),
            )
        )

    def add_ui_lta_otc(self) -> TServiceQuerySet:
        """
        Local authority name should be displayed with | seperation if multiple.

        Returns:
            TServiceQuerySet: QuerySet with anotated column
        """
        return self.annotate(
            ui_lta_otc=GroupConcat(
                F("registration__ui_lta__name"), delimiter="|", distinct=True
            )
        )

    def add_ui_lta_weca(self) -> TServiceQuerySet:
        """
        This column is populated with the UI LTA(s) the service code belongs to
        via the relationship between the service and the Admin Area with the ATCO
        which is mapped to the UI LTA entity. And if the service belongs to more
        than one UI LTA, then separate these with a |.

        Returns:
            TServiceQuerySet: QuerySet with anotated column
        """
        return self.annotate(
            ui_lta_weca=GroupConcat(
                AdminArea.objects.filter(atco_code=OuterRef("atco_code")).values(
                    "ui_lta__name"
                ),
                delimiter="|",
                distinct=True,
            )
        )

    def add_ui_lta(self):
        """
        This column is populated with the UI LTA(s) the service code belongs to
        via the relationship between the service and the Admin Area with the ATCO
        which is mapped to the UI LTA entity. And if the service belongs to more
        than one UI LTA, then separate these with a |.

        Returns:
            TServiceQuerySet: QuerySet with anotated column
        """
        return self.annotate(
            local_authority_ui_lta=Case(
                When(
                    Q(api_type=API_TYPE_WECA),
                    then=F("ui_lta_weca"),
                ),
                default=F("ui_lta_otc"),
                output_field=CharField(),
            )
        )

    def add_service_number(self) -> TServiceQuerySet:
        """
        There may be multiple rows for the service, and each row has it's
        own service number, then This will appear in the report as with | seperator.

        Returns:
            TServiceQuerySet: QuerySet with anotated column
        """
        return self.annotate(
            service_numbers=GroupConcat(
                F("service_number"), delimiter="|", distinct=True
            )
        )

    def add_timetable_data_annotations(self) -> TServiceQuerySet:
        """
        This will fetch oprator details travline region ui lta and service number from
        OTC service table.

        Returns:
            TServiceQuerySet: QuerySet with anotated column
        """

        return (
            self.add_service_code()
            .add_operator_details()
            .add_licence_details()
            .add_traveline_region_weca()
            .add_traveline_region_otc()
            .add_traveline_region_details()
            .add_ui_lta_otc()
            .add_ui_lta_weca()
            .add_ui_lta()
            .add_service_number()
        )

    def get_all_in_organisation(self, organisation_id: int) -> TServiceQuerySet:
        org_licences = BODSLicence.objects.filter(organisation__id=organisation_id)
        return (
            self.filter(licence__number__in=Subquery(org_licences.values("number")))
            .add_service_code()
            .order_by("licence__number", "registration_number")
            .distinct("licence__number", "registration_number")
        )

    def get_all_without_exempted_ones(self, organisation_id: int) -> TServiceQuerySet:
        org_licences = BODSLicence.objects.filter(organisation__id=organisation_id)

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
        org_licences = BODSLicence.objects.filter(organisation__id=organisation_id)
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

    def get_in_scope_in_season_services(self, organisation_id: int) -> TServiceQuerySet:
        now = timezone.now()
        licences_subquery = BODSLicence.objects.filter(organisation__id=organisation_id)
        seasonal_services_subquery = Subquery(
            SeasonalService.objects.filter(licence__organisation__id=organisation_id)
            .filter(start__gt=now.date())
            .add_registration_number()
            .values("registration_number")
        )
        exemptions_subquery = Subquery(
            ServiceCodeExemption.objects.add_registration_number()
            .filter(licence__organisation__id=organisation_id)
            .values("registration_number")
        )

        traveline_region_subquery = Subquery(
            self.get_org_weca_otc_traveline_region_exemption(organisation_id)
        )

        return (
            self.filter(
                licence__number__in=Subquery(licences_subquery.values("number"))
            )
            .add_service_code()
            .exclude(registration_number__in=exemptions_subquery)
            .exclude(registration_number__in=seasonal_services_subquery)
            .exclude(registration_number__in=traveline_region_subquery)
            .order_by("licence__number", "registration_number", "service_number")
            .distinct("licence__number", "registration_number")
        )

    def get_org_weca_otc_traveline_region_exemption(self, organisation_id: int):
        """Return registration numbers to be exempted based on traveline_region_id
        Which are not in england

        Args:
            organisation_id (int): Organisation to filter services for
        """
        organisation_licences = OrganisationLicence.objects.filter(
            organisation_id=organisation_id
        ).values("number")
        weca_registrations = [
            (
                self.filter(
                    licence__number__in=organisation_licences,
                    api_type=API_TYPE_WECA,
                )
                .exclude(
                    atco_code__in=AdminArea.objects.filter(
                        traveline_region_id__in=ENGLISH_TRAVELINE_REGIONS
                    ).values("atco_code")
                )
                .values("registration_number")
            )
        ]

        # OTC registrations which doesn't have any UI LTA in english region
        weca_registrations.append(
            (
                self.filter(licence__number__in=organisation_licences)
                .filter(api_type__isnull=True)
                .exclude(
                    registration_number__in=Subquery(
                        self.filter(licence__number__in=organisation_licences)
                        .filter(
                            registration__ui_lta__naptan_ui_lta_records__traveline_region_id__in=ENGLISH_TRAVELINE_REGIONS
                        )
                        .values("registration_number")
                    )
                )
                .values("registration_number")
            )
        )

        return self.merge_weca_otc_queries(weca_registrations)

    def merge_weca_otc_queries(self, registrations):
        final_subquery = None
        for service_queryset in registrations:
            if final_subquery is None:
                final_subquery = service_queryset
            else:
                final_subquery = final_subquery | service_queryset

        final_subquery = final_subquery.distinct()
        return final_subquery

    def get_weca_services_register_numbers(self, ui_lta):
        """
        Get the WECA services for a given ui lta
        """
        return self.filter(
            atco_code__in=AdminArea.objects.filter(ui_lta=ui_lta).values("atco_code"),
            licence_id__isnull=False,
        ).values("id")

    def get_weca_otc_traveline_region_exemption(self, ui_lta):
        """
        Get OTC and WECA registration_number subquery, which are exempted
        because those are not present in english traveline region
        """
        weca_registrations = [
            self.filter(
                atco_code__in=AdminArea.objects.filter(ui_lta=ui_lta)
                .exclude(traveline_region_id__in=ENGLISH_TRAVELINE_REGIONS)
                .values("atco_code"),
                api_type=API_TYPE_WECA,
            ).values("registration_number")
        ]

        # OTC registrations which doesn't have any UI LTA in english region
        weca_registrations.append(
            (
                self.filter(registration__ui_lta__in=[ui_lta])
                .filter(api_type__isnull=True)
                .exclude(
                    registration_number__in=Subquery(
                        self.filter(registration__ui_lta__in=[ui_lta])
                        .filter(
                            registration__ui_lta__naptan_ui_lta_records__traveline_region_id__in=ENGLISH_TRAVELINE_REGIONS
                        )
                        .values("registration_number")
                    )
                )
                .values("registration_number")
            )
        )

        return self.merge_weca_otc_queries(weca_registrations)

    def get_in_scope_in_season_lta_services(self, lta_list):
        now = timezone.now()
        services_subquery_list = [
            x.registration_numbers.values("id")
            for x in lta_list
            if x.registration_numbers.values("id")
        ]

        if len(lta_list) > 0:
            weca_services_list = self.get_weca_services_register_numbers(
                lta_list[0].ui_lta
            )

            if weca_services_list:
                services_subquery_list.append(weca_services_list)

        if services_subquery_list:
            final_subquery = self.merge_weca_otc_queries(services_subquery_list)
            if len(final_subquery) > 0:
                seasonal_services_subquery = Subquery(
                    SeasonalService.objects.filter(
                        licence__organisation__licences__number__in=Subquery(
                            final_subquery.values("licence__number")
                        )
                    )
                    .filter(start__gt=now.date())
                    .add_registration_number()
                    .values("registration_number")
                )

                exemptions_subquery = Subquery(
                    ServiceCodeExemption.objects.add_registration_number()
                    .filter(
                        licence__organisation__licences__number__in=Subquery(
                            final_subquery.values("licence__number")
                        )
                    )
                    .values("registration_number")
                )

                exemption_traveline_region_subquery = Subquery(
                    self.get_weca_otc_traveline_region_exemption(lta_list[0].ui_lta)
                )

                all_in_scope_in_season_services_count = (
                    self.filter(id__in=Subquery(final_subquery.values("id")))
                    .annotate(otc_licence_number=F("licence__number"))
                    .exclude(registration_number__in=exemptions_subquery)
                    .exclude(registration_number__in=seasonal_services_subquery)
                    .exclude(
                        registration_number__in=exemption_traveline_region_subquery
                    )
                    .order_by(
                        "licence__number", "registration_number", "service_number"
                    )
                    .distinct("licence__number", "registration_number")
                ).count()
            return all_in_scope_in_season_services_count
        else:
            return None

    def get_operator_id(self, service_id: int):
        from transit_odp.otc.models import Operator as OTCOperator

        operator_id = self.filter(id=service_id).values_list("operator_id", flat=True)

        otc_operator_id = OTCOperator.objects.filter(id__in=operator_id).values_list(
            "operator_id", flat=True
        )

        return otc_operator_id

    def add_otc_stale_date(self):
        return self.annotate(
            effective_stale_date_otc_effective_date=TruncDate(
                ExpressionWrapper(
                    F("effective_date") - timedelta(days=42),
                    output_field=DateField(),
                )
            )
        )

    def add_otc_association_date(self):
        return self.annotate(
            association_date_otc_effective_date=TruncDate(
                ExpressionWrapper(
                    F("effective_date") - timedelta(days=70),
                    output_field=DateField(),
                )
            )
        )

    def get_all_otc_data_for_lta(self, final_subquery) -> TServiceQuerySet:
        return (
            self.add_otc_stale_date()
            .add_otc_association_date()
            .annotate(otc_licence_number=F("licence__number"))
            .filter(id__in=final_subquery)
            .order_by("licence__number", "registration_number", "service_number")
            .distinct("licence__number", "registration_number")
        )

    def get_all_otc_data_for_organisation(
        self, organisation_id: int
    ) -> TServiceQuerySet:
        licences_subquery = Subquery(
            BODSLicence.objects.filter(organisation__id=organisation_id).values(
                "number"
            )
        )
        return (
            self.add_otc_stale_date()
            .add_otc_association_date()
            .annotate(otc_licence_number=F("licence__number"))
            .filter(licence__number__in=licences_subquery)
            .order_by("licence__number", "registration_number", "service_number")
            .distinct("licence__number", "registration_number")
        )

    def get_otc_data_for_organisation(self, organisation_id: int) -> TServiceQuerySet:
        now = timezone.now()
        # seasonal services that are out of season
        seasonal_services_subquery = Subquery(
            SeasonalService.objects.filter(licence__organisation__id=organisation_id)
            .filter(start__gt=now.date())
            .add_registration_number()
            .values("registration_number")
        )
        exemptions_subquery = Subquery(
            ServiceCodeExemption.objects.add_registration_number()
            .filter(licence__organisation__id=organisation_id)
            .values("registration_number")
        )

        traveline_region_subquery = Subquery(
            self.get_org_weca_otc_traveline_region_exemption(organisation_id)
        )

        return (
            self.get_all_otc_data_for_organisation(organisation_id)
            .exclude(registration_number__in=exemptions_subquery)
            .exclude(registration_number__in=seasonal_services_subquery)
            .exclude(registration_number__in=traveline_region_subquery)
            .order_by("licence__number", "registration_number", "service_number")
            .distinct("licence__number", "registration_number")
        )

    def get_otc_data_for_lta(self, lta_list) -> TServiceQuerySet:
        now = timezone.now()

        services_subquery_list = [
            x.registration_numbers.values("id")
            for x in lta_list
            if x.registration_numbers.values("id")
        ]

        if len(lta_list) > 0:
            weca_services_list = self.get_weca_services_register_numbers(
                lta_list[0].ui_lta
            )
            if weca_services_list:
                services_subquery_list.append(weca_services_list)

        if services_subquery_list:
            final_subquery = self.merge_weca_otc_queries(services_subquery_list)

            # seasonal services that are out of season
            seasonal_services_subquery = Subquery(
                SeasonalService.objects.filter(
                    licence__organisation__licences__number__in=Subquery(
                        final_subquery.values("licence__number")
                    )
                )
                .filter(start__gt=now.date())
                .add_registration_number()
                .values("registration_number")
            )
            exemptions_subquery = Subquery(
                ServiceCodeExemption.objects.add_registration_number()
                .filter(
                    licence__organisation__licences__number__in=Subquery(
                        final_subquery.values("licence__number")
                    )
                )
                .values("registration_number")
            )

            exemption_traveline_region_subquery = Subquery(
                self.get_weca_otc_traveline_region_exemption(lta_list[0].ui_lta)
            )

            return (
                self.get_all_otc_data_for_lta(final_subquery)
                .exclude(registration_number__in=exemptions_subquery)
                .exclude(registration_number__in=seasonal_services_subquery)
                .exclude(registration_number__in=exemption_traveline_region_subquery)
                .order_by("licence__number", "registration_number", "service_number")
                .distinct("licence__number", "registration_number")
            )
        else:
            return None

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
    def add_service_count(self):
        return self.annotate(service_count=Count("services"))

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


class OperatorQuerySet(QuerySet):
    def add_service_count(self):
        return self.annotate(service_count=Count("services"))


class LocalAuthorityQuerySet(QuerySet):
    pass
