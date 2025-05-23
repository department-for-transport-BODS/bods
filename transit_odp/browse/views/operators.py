from logging import getLogger
from math import floor
from typing import Dict

import pandas as pd
from django.db.models import Avg, F
from django_hosts.resolvers import reverse
from waffle import flag_is_active

import config.hosts
from config.hosts import DATA_HOST, PUBLISH_HOST
from transit_odp.avl.constants import MORE_DATA_NEEDED
from transit_odp.avl.post_publishing_checks.constants import NO_PPC_DATA
from transit_odp.avl.proxies import AVLDataset
from transit_odp.avl.require_attention.abods.registery import AbodsRegistery
from transit_odp.avl.require_attention.weekly_ppc_zip_loader import (
    get_vehicle_activity_operatorref_linename,
)
from transit_odp.browse.common import (
    get_franchise_licences,
    get_franchise_organisation,
    get_in_scope_in_season_services_line_level,
    get_operator_with_licence_number,
    otc_map_txc_map_from_licence,
)
from transit_odp.browse.views.base_views import BaseListView
from transit_odp.browse.views.timetable_views import LineMetadataDetailView
from transit_odp.common.constants import FeatureFlags
from transit_odp.common.views import BaseDetailView
from transit_odp.fares_validator.models import FaresValidationResult
from transit_odp.organisation.constants import (
    ENGLISH_TRAVELINE_REGIONS,
    EXPIRED,
    INACTIVE,
    AVLType,
    FaresType,
    TimetableType,
)
from transit_odp.organisation.models import Dataset
from transit_odp.organisation.models import Licence as OrganisationLicence
from transit_odp.organisation.models import Organisation
from transit_odp.organisation.models.data import (
    SeasonalService,
    ServiceCodeExemption,
    TXCFileAttributes,
)
from transit_odp.organisation.models.report import ComplianceReport
from transit_odp.otc.models import Licence as OTCLicence
from transit_odp.otc.models import Service
from transit_odp.publish.requires_attention import (
    FaresRequiresAttention,
    get_avl_requires_attention_line_level_data,
    get_dq_critical_observation_services_map,
    get_fares_compliance_status,
    get_fares_dataset_map,
    get_fares_requires_attention,
    get_fares_timeliness_status,
    get_requires_attention_line_level_data,
    is_stale,
)

logger = getLogger(__name__)


class OperatorsView(BaseListView):
    """
    View to list all active organisations.
    """

    template_name = "browse/operators.html"
    model = Organisation
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        context["ordering"] = self.request.GET.get("ordering", "name")
        active_orgs = self.model.objects.filter(is_active=True)
        operators = {
            "names": [name for name in active_orgs.values_list("name", flat=True)]
        }
        context["operators"] = operators
        return context

    def get_queryset(self):
        qs = self.model.objects.filter(is_active=True)

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


class OperatorDetailView(BaseDetailView):
    """
    View to display Services Requiring Attention metrics relating to
    overall, timetables, location and fares complaince.
    """

    template_name = "browse/operators/operator_detail.html"
    model = Organisation

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True).add_nocs_string()

    def get_overall_ppc_score(self, avl_dt):
        avl_datasets = (
            avl_dt.add_avl_compliance_status_cached()
            .add_post_publishing_check_stats()
            .order_by("avl_feed_status", "-modified")
            .get_active()
            .exclude(avl_compliance_status_cached__in=[MORE_DATA_NEEDED])
        )
        return avl_datasets.exclude(percent_matching=float(NO_PPC_DATA)).aggregate(
            Avg("percent_matching")
        )

    def get_context_data(self, **kwargs):
        is_fares_validator_active = flag_is_active("", "is_fares_validator_active")
        is_avl_require_attention_active = flag_is_active(
            "", FeatureFlags.AVL_REQUIRES_ATTENTION.value
        )
        is_fares_require_attention_active = flag_is_active(
            "", FeatureFlags.FARES_REQUIRE_ATTENTION.value
        )
        is_complete_service_pages_active = flag_is_active(
            "", FeatureFlags.COMPLETE_SERVICE_PAGES.value
        )
        is_operator_prefetch_sra_active = flag_is_active(
            "", FeatureFlags.OPERATOR_PREFETCH_SRA.value
        )
        is_franchise_organisation_active = flag_is_active(
            "", FeatureFlags.FRANCHISE_ORGANISATION.value
        )
        context = super().get_context_data(**kwargs)
        organisation = self.object

        is_franchise = False
        licences_list = []

        if is_franchise_organisation_active:
            is_franchise = organisation.is_franchise

            if is_franchise:
                context["is_franchise"] = is_franchise
                context[
                    "is_franchise_organisation_active"
                ] = is_franchise_organisation_active
                org_atco_codes = organisation.admin_areas.values_list(
                    "atco_code", flat=True
                )
                licences_list = get_franchise_licences(org_atco_codes)

        if not is_franchise:
            licences_list = organisation.licences.values_list("number", flat=True)

        context["is_avl_require_attention_active"] = is_avl_require_attention_active
        context["is_complete_service_pages_active"] = is_complete_service_pages_active
        context["is_fares_require_attention_active"] = is_fares_require_attention_active

        total_fares_sra = total_avl_sra = total_overall_sra = 0
        if is_operator_prefetch_sra_active:
            logger.debug("Operator Prefetch SRA active, Displaying from DB")
            total_timetable_sra = organisation.timetable_sra
            total_avl_sra = organisation.avl_sra
            total_fares_sra = organisation.fares_sra
            total_in_scope = organisation.total_inscope
            total_overall_sra = organisation.overall_sra
        else:
            logger.debug("Operator Prefetch SRA inactive, calculating SRA")
            total_in_scope = len(
                get_in_scope_in_season_services_line_level(organisation.id)
            )
            total_timetable_sra = len(
                get_requires_attention_line_level_data(organisation.id)
            )
            if is_avl_require_attention_active:
                total_avl_sra = len(
                    get_avl_requires_attention_line_level_data(organisation.id)
                )

            if is_fares_require_attention_active:
                fares_reqiures_attention = FaresRequiresAttention(organisation.id)
                total_fares_sra = len(
                    fares_reqiures_attention.get_fares_requires_attention_line_level_data()
                )
            total_overall_sra = max(total_timetable_sra, total_fares_sra, total_avl_sra)

        context["total_in_scope_in_season_services"] = total_in_scope
        context["total_services_requiring_attention"] = total_timetable_sra

        if is_complete_service_pages_active:
            context["total_services_requiring_attention"] = total_overall_sra
            context[
                "timetable_services_requiring_attention_count"
            ] = total_timetable_sra

            if is_avl_require_attention_active:
                context["avl_services_requiring_attention_count"] = total_avl_sra
            if is_fares_require_attention_active:
                context["fares_services_requiring_attention_count"] = total_fares_sra
            context["operator_licences"] = get_operator_with_licence_number(
                licences_list
            )
        else:
            context["operator_licences"] = []
            try:
                context["services_require_attention_percentage"] = round(
                    100
                    * (
                        context["total_services_requiring_attention"]
                        / context["total_in_scope_in_season_services"]
                    )
                )
            except ZeroDivisionError:
                context["services_require_attention_percentage"] = 0

            if is_avl_require_attention_active:
                context["avl_total_services_requiring_attention"] = total_avl_sra

                try:
                    context["avl_services_require_attention_percentage"] = round(
                        100
                        * (
                            context["avl_total_services_requiring_attention"]
                            / context["total_in_scope_in_season_services"]
                        )
                    )
                except ZeroDivisionError:
                    context["avl_services_require_attention_percentage"] = 0

            if is_fares_require_attention_active:
                context["fares_total_services_requiring_attention"] = total_fares_sra
                try:
                    context[
                        "fares_total_services_requiring_attention_percentage"
                    ] = round(
                        100
                        * (
                            context["fares_total_services_requiring_attention"]
                            / context["total_in_scope_in_season_services"]
                        )
                    )
                except ZeroDivisionError:
                    context["fares_total_services_requiring_attention_percentage"] = 0

            fares_datasets = (
                Dataset.objects.filter(
                    organisation=organisation,
                    dataset_type=FaresType,
                )
                .select_related("organisation")
                .select_related("live_revision")
            )
            context["fares_stats"] = fares_datasets.agg_global_feed_stats(
                dataset_type=FaresType, organisation_id=organisation.id
            )
            if is_fares_validator_active:
                try:
                    results = (
                        FaresValidationResult.objects.filter(
                            organisation_id=organisation.id,
                            revision_id=F("revision__dataset__live_revision_id"),
                            revision__dataset__dataset_type=FaresType,
                        )
                        .annotate(status=F("revision__status"))
                        .exclude(status__in=[EXPIRED, INACTIVE])
                        .values("count")
                    )
                except FaresValidationResult.DoesNotExist:
                    results = []
                fares_non_compliant_count = len(
                    [count for count in results if count.get("count") > 0]
                )
                context["fares_non_compliant"] = fares_non_compliant_count
            else:
                # Compliance is n/a for Fares datasets
                context["fares_non_compliant"] = 0

        avl_datasets = (
            AVLDataset.objects.filter(
                organisation=organisation,
                dataset_type=AVLType,
            )
            .select_related("organisation")
            .select_related("live_revision")
            .order_by("id")
        )
        overall_ppc_score = self.get_overall_ppc_score(avl_datasets)[
            "percent_matching__avg"
        ]
        context.update(
            {
                "overall_ppc_score": (
                    floor(overall_ppc_score) if overall_ppc_score else overall_ppc_score
                ),
            }
        )

        if self.request.user.is_authenticated:
            context["timetable_feed_url"] = (
                f"{reverse('api:feed-list', host=DATA_HOST)}"
                f"?noc={organisation.nocs_string}"
                f"&api_key={self.request.user.auth_token.key}"
            )
            context["avl_feed_url"] = (
                f"{reverse('api:avldatafeedapi', host=DATA_HOST)}"
                f"?operatorRef={organisation.nocs_string}"
                f"&api_key={self.request.user.auth_token.key}"
            )
            context["fares_feed_url"] = (
                f"{reverse('api:fares-api-list', host=DATA_HOST)}"
                f"?noc={organisation.nocs_string}"
                f"&api_key={self.request.user.auth_token.key}"
            )

        context["data_activity_url"] = (
            reverse("data-activity", kwargs={"pk1": organisation.id}, host=PUBLISH_HOST)
            + "?prev=operator-detail"
        )
        return context


class LicenceDetailView(BaseDetailView):
    template_name = "browse/operators/licence_details.html"
    model = OrganisationLicence
    slug_url_kwarg = "number"
    slug_field = "number"

    def get_object(self):
        licence_number = self.kwargs.get("number")
        org_id = self.kwargs.get("pk", "-")
        is_franchise_organisation_active = flag_is_active(
            "", FeatureFlags.FRANCHISE_ORGANISATION.value
        )
        franchise_organisation = get_franchise_organisation(licence_number, org_id)

        if (
            is_franchise_organisation_active
            and franchise_organisation
            and franchise_organisation.is_franchise
        ):
            return OTCLicence.objects.get(number=licence_number)
        return self.model.objects.get(number=licence_number)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        licence_number = self.kwargs.get("number", "-")
        org_id = self.kwargs.get("pk", "-")
        context["licence_number"] = licence_number
        licence_obj = self.get_object()
        is_franchise_organisation_active = flag_is_active(
            "", FeatureFlags.FRANCHISE_ORGANISATION.value
        )
        franchise_organisation = get_franchise_organisation(licence_number, org_id)
        context["pk"] = org_id
        context["api_root"] = reverse("api:app:api-root", host=config.hosts.DATA_HOST)

        is_prefetch_compliance_report_active = flag_is_active(
            "", FeatureFlags.PREFETCH_DATABASE_COMPLIANCE_REPORT.value
        )

        if is_prefetch_compliance_report_active:
            licence_services_df = pd.DataFrame.from_records(
                ComplianceReport.objects.values(
                    "registration_number",
                    "service_number",
                    "overall_requires_attention",
                    "scope_status",
                    "seasonal_status",
                )
                .filter(
                    otc_licence_number=licence_number,
                    licence_organisation_id=org_id,
                )
                .order_by("service_number", "registration_number")
            )
            self.otc_map = licence_services_df.to_dict("records")
            self.prefetch_service_sra()

        else:
            self.otc_map, self.txc_map = otc_map_txc_map_from_licence(licence_number)
            self.service_code_exemption_map = self.get_service_code_exemption_map(
                licence_number
            )
            self.seasonal_service_map = self.get_seasonal_service_map(licence_number)

            self.calculate_service_sra()

        if (
            is_franchise_organisation_active
            and franchise_organisation
            and franchise_organisation.is_franchise
        ):
            context["organisation"] = franchise_organisation
        else:
            context["organisation"] = licence_obj.organisation
        context["licence_services"] = self.otc_map
        return context

    def prefetch_service_sra(self):
        for service in self.otc_map:
            service["registration_number"] = service["registration_number"].replace(
                "/", ":"
            )

            is_in_scope = True if service["scope_status"] == "In Scope" else False
            is_in_season = (
                True if service["seasonal_status"] != "Out of Season" else False
            )
            service["is_in_scope"] = is_in_scope
            service["is_in_season"] = is_in_season

            is_label_green = False
            label_str = ""

            if not is_in_scope or not is_in_season:
                is_compliant = True
                label_str = "Out of Season"
                if not is_in_scope:
                    label_str = "Out of Scope"
            elif service["overall_requires_attention"] == "No":
                is_compliant = True
                is_label_green = True
                label_str = "Compliant"
            else:
                is_compliant = False
                label_str = "Not Compliant"

            service["is_compliant"] = is_compliant
            service["is_label_green"] = is_label_green
            service["label_str"] = label_str

    def calculate_service_sra(self):
        self.is_fra_active = flag_is_active(
            "", FeatureFlags.FARES_REQUIRE_ATTENTION.value
        )
        self.is_dqs_ra_active = flag_is_active(
            "", FeatureFlags.DQS_REQUIRE_ATTENTION.value
        )
        self.is_avl_ra_active = flag_is_active(
            "", FeatureFlags.AVL_REQUIRES_ATTENTION.value
        )
        self.dq_critical_observation_map = []
        if self.is_dqs_ra_active:
            self.dq_critical_observation_map = get_dq_critical_observation_services_map(
                self.txc_map
            )

        self.fares_require_attention_df = pd.DataFrame(
            columns=["national_operator_code", "line_name"]
        )
        if self.is_fra_active:
            self.fares_require_attention_df = get_fares_dataset_map(self.txc_map)

        self.synced_in_last_month = []
        self.uncounted_activity_df = pd.DataFrame(columns=["OperatorRef", "LineRef"])
        if self.is_avl_ra_active:
            abods_registry = AbodsRegistery()
            self.synced_in_last_month = abods_registry.records()
            self.uncounted_activity_df = get_vehicle_activity_operatorref_linename()

        for service in self.otc_map:
            service["registration_number"] = service["registration_number"].replace(
                "/", ":"
            )
            self.service = service
            service_txc_file = self.txc_map.get(
                (service.get("registration_number"), service.get("service_number")),
                None,
            )
            if service_txc_file:
                self.service_txc_file = service_txc_file
                self.operator_ref = self.service_txc_file.national_operator_code
                self.service_number = service.get("service_number")
                service["dataset_id"] = service_txc_file.revision.dataset_id
            else:
                self.service_txc_file = None
                self.operator_ref = None
                service["dataset_id"] = None
                self.service_number = None
            is_in_scope = self.is_service_in_scope()
            is_in_season = self.is_service_in_season()
            service["is_in_scope"] = is_in_scope
            service["is_in_season"] = is_in_season

            is_label_green = False
            label_str = ""

            if not is_in_scope or not is_in_season:
                is_compliant = True
                label_str = "Out of Season"
                if not is_in_scope:
                    label_str = "Out of Scope"
            elif (
                not self.is_fares_compliant()
                or not self.is_timetable_compliant()
                or not self.is_avl_compliant()
            ):
                is_compliant = False
                label_str = "Not Compliant"
            else:
                is_compliant = True
                is_label_green = True
                label_str = "Compliant"
            service["is_compliant"] = is_compliant
            service["is_label_green"] = is_label_green
            service["label_str"] = label_str

    def is_fares_compliant(self) -> bool:
        """Check if a given service is fairs compliant or not

        Returns:
            bool: True if compliant else False
        """
        if not self.is_fra_active:
            return True

        if not self.service_txc_file:
            return False

        fares_file_details = self.fares_require_attention_df[
            (
                self.fares_require_attention_df["national_operator_code"]
                == self.operator_ref
            )
            & (self.fares_require_attention_df["line_name"] == self.service_number)
        ]

        if fares_file_details.empty:
            return False

        row = fares_file_details.iloc[0]
        row["valid_to"] = row["valid_to"].date() if pd.notna(row["valid_to"]) else None
        row["valid_from"] = (
            row["valid_from"].date() if pd.notna(row["valid_from"]) else None
        )
        fares_timeliness_status = get_fares_timeliness_status(
            row["valid_to"], row["last_updated_date"].date()
        )
        fares_compliance_status = get_fares_compliance_status(row["is_fares_compliant"])

        if (
            get_fares_requires_attention(
                "Published", fares_timeliness_status, fares_compliance_status
            )
            == "Yes"
        ):
            return False
        return True

    def is_timetable_compliant(self) -> bool:
        """Check if a service is timetable require attention
        or not

        Returns:
            bool: True is compliant False if not
        """
        if not self.service_txc_file:
            return False

        service_obj = Service(self.service)
        service_obj.association_date_otc_effective_date = self.service.get(
            "association_date_otc_effective_date"
        )
        service_obj.effective_stale_date_otc_effective_date = self.service.get(
            "effective_stale_date_otc_effective_date"
        )

        if not self.is_dqs_compliant() or is_stale(service_obj, self.service_txc_file):
            return False
        return True

    def is_dqs_compliant(self) -> bool:
        """Check if service has any dqs require attention

        Returns:
            bool: True if compliant False if not
        """
        if not self.is_dqs_ra_active:
            return True

        return (
            False
            if (
                self.service.get("registration_number"),
                self.service.get("service_number"),
            )
            in self.dq_critical_observation_map
            else True
        )

    def is_avl_compliant(self) -> bool:
        """Check if avl is compliant for a service

        Returns:
            bool: True if compliant else False
        """
        if not self.is_avl_ra_active:
            return True

        if not self.service_txc_file:
            return False

        line_name = self.service.get("service_number")
        if (
            not self.uncounted_activity_df.loc[
                (self.uncounted_activity_df["OperatorRef"] == self.operator_ref)
                & (
                    self.uncounted_activity_df["LineRef"].isin(
                        [line_name, line_name.replace(" ", "_")]
                    )
                )
            ].empty
            or f"{line_name}__{self.operator_ref}" not in self.synced_in_last_month
        ):
            return False
        return True

    def is_service_in_scope(self) -> bool:
        """check is service is in scope or not system will
        check 2 points to decide in scope Service Exception,
        and Traveling region

        Returns:
            bool: True if in scope else False
        """
        exemption = self.service_code_exemption_map.get(
            self.service.get("registration_number")
        )
        traveline_regions = self.service.get("traveline_region")
        if traveline_regions:
            traveline_regions = traveline_regions.split("|")
        else:
            traveline_regions = []
        is_english_region = list(
            set(ENGLISH_TRAVELINE_REGIONS) & set(traveline_regions)
        )

        if not (not (exemption and exemption.registration_code) and is_english_region):
            return False

        return True

    def is_service_in_season(self) -> bool:
        """check is service is in season or not system will
        check 1 points to decide service in season,
        Seasonal service status

        Returns:
            bool: True if in scope else False
        """
        seasonal_service = self.seasonal_service_map.get(
            self.service.get("registration_number").replace("/", ":")
        )
        if seasonal_service and not seasonal_service.seasonal_status:
            return False
        return True

    def get_service_compliant_status(
        self, registration_number: str, line_name: str
    ) -> bool:
        """Check if service is compliant or not, it will check 3 params
        Fares Compliant, Timetable Compliant, AVL compliant

        Args:
            registration_number (str): Registration number
            line_name (str): Line name

        Returns:
            bool: True if compliant False if not
        """
        if (
            self.is_fares_compliant(registration_number, line_name)
            and self.is_timetable_compliant(registration_number, line_name)
            and self.is_avl_compliant(registration_number, line_name)
        ):
            return True
        return False

    def get_seasonal_service_map(
        self, licence_number: str
    ) -> Dict[str, SeasonalService]:
        """
        Get a dictionary which includes all the Seasonal Services
        for an organisation.
        """
        return {
            service.registration_number.replace("/", ":"): service
            for service in SeasonalService.objects.filter(
                licence__organisation__licences__number__in=[licence_number]
            )
            .add_registration_number()
            .add_seasonal_status()
        }

    def get_service_code_exemption_map(
        self, licence_number: str
    ) -> Dict[str, ServiceCodeExemption]:
        """Get the status of service excemption

        Args:
            licence_number (str): licence number to check for excemption

        Returns:
            Dict[str, ServiceCodeExemption]: dict for excemption object
        """
        return {
            service.registration_number.replace("/", ":"): service
            for service in ServiceCodeExemption.objects.add_registration_number().filter(
                licence__organisation__licences__number__in=licence_number
            )
        }


class LicenceLineMetadataDetailView(LineMetadataDetailView):
    slug_url_kwarg = "number"
    slug_field = "number"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.page = "licence"

    def get_object(self):
        try:
            txcfileattribute = self.get_txcfileattribute()
            if txcfileattribute:
                object = (
                    super()
                    .get_queryset()
                    .filter(id=txcfileattribute.revision.dataset_id)
                    .get_active_org()
                    .get_dataset_type(dataset_type=TimetableType)
                    .get_published()
                    .get_viewable_statuses()
                    .add_admin_area_names()
                    .add_live_data()
                    .add_nocs()
                    .select_related("live_revision")
                ).first()
                return object
        except Dataset.DoesNotExist:
            line = self.request.GET.get("line")
            service_code = self.request.GET.get("service")
            logger.debug(
                f"Licence line details object not found for line {line} and service code {service_code}."
            )
            pass
        return Dataset()

    def get_txcfileattribute(self):
        line = self.request.GET.get("line")
        service_code = self.request.GET.get("service")
        return (
            TXCFileAttributes.objects.filter(
                service_code=service_code, line_names__contains=[line]
            )
            .get_active_live_revisions()
            .order_by(
                "service_code",
                "-revision__published_at",
                "-revision_number",
                "-modification_datetime",
                "-operating_period_start_date",
                "-filename",
            )
            .distinct("service_code")
            .first()
        )

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        licence_number = self.kwargs.get("number", "-")
        org_id = self.kwargs.get("pk", "-")
        kwargs["licence_number"] = licence_number
        kwargs["licence_page"] = True
        is_franchise_organisation_active = flag_is_active(
            "", FeatureFlags.FRANCHISE_ORGANISATION.value
        )
        franchise_organisation = get_franchise_organisation(licence_number, org_id)
        licence_obj = OrganisationLicence.objects.filter(number=licence_number).first()

        if (
            is_franchise_organisation_active
            and franchise_organisation
            and franchise_organisation.is_franchise
        ):
            kwargs["organisation"] = franchise_organisation
        else:
            kwargs["organisation"] = licence_obj.organisation

        return kwargs
