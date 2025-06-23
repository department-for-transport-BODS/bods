from logging import getLogger
from math import floor, ceil
import re
from typing import Dict, List
from datetime import datetime, timedelta

import pandas as pd
from django.db.models import Avg, F
from django_hosts.resolvers import reverse
from waffle import flag_is_active
from django.db.models import Max
from transit_odp.transmodel.models import BookingArrangements, Service

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
from transit_odp.organisation.models.organisations import Licence
from transit_odp.organisation.models.report import ComplianceReport
from transit_odp.otc.models import Licence as OTCLicence
from transit_odp.publish.requires_attention import (
    FaresRequiresAttention,
    get_avl_requires_attention_line_level_data,
    get_dq_critical_observation_services_map,
    get_fares_compliance_status,
    get_fares_dataset_map,
    get_fares_requires_attention,
    get_fares_timeliness_status,
    get_line_level_txc_map_service_base,
    is_avl_requires_attention,
    get_requires_attention_line_level_data,
    is_stale,
)
from transit_odp.otc.models import Service as OTCService
from transit_odp.browse.timetable_visualiser import TimetableVisualiser
from django.views.generic import DetailView


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
    model = OTCLicence
    slug_url_kwarg = "number"
    slug_field = "number"

    def get_object(self):
        licence_number = self.kwargs.get("number")
        return self.model.objects.get(number=licence_number)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        licence_number = self.kwargs.get("number", "-")
        org_id = self.kwargs.get("org_id", None)
        context["licence_number"] = licence_number
        licence_obj = self.get_object()
        is_franchise_organisation_active = flag_is_active(
            "", FeatureFlags.FRANCHISE_ORGANISATION.value
        )
        franchise_organisation = None
        if org_id:
            franchise_organisation = get_franchise_organisation(licence_number, org_id)
        context["org_id"] = org_id
        context["api_root"] = reverse("api:app:api-root", host=config.hosts.DATA_HOST)

        is_prefetch_compliance_report_active = flag_is_active(
            "", FeatureFlags.PREFETCH_DATABASE_COMPLIANCE_REPORT.value
        )

        if is_prefetch_compliance_report_active:
            licence_services_qs = ComplianceReport.objects.filter(
                otc_licence_number=licence_number
            )

            if org_id:
                licence_services_qs = licence_services_qs.filter(
                    licence_organisation_id=org_id
                )

            licence_services_df = pd.DataFrame.from_records(
                licence_services_qs.values(
                    "registration_number",
                    "service_number",
                    "overall_requires_attention",
                    "scope_status",
                    "seasonal_status",
                ).order_by("service_number", "registration_number")
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
            organisation_id = franchise_organisation.id
            organisation_name = franchise_organisation.name
        else:
            licence_obj = Licence.objects.filter(number=licence_number).first()
            if licence_obj:
                organisation_id = licence_obj.organisation.id
                organisation_name = licence_obj.organisation.name
            else:
                organisation_id = None
                organisation_name = "Organisation not yet created"

        context["licence_services"] = self.otc_map
        context["organisation_id"] = organisation_id
        context["organisation_name"] = organisation_name
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


class LicenceLineMetadataDetailView(DetailView):
    slug_url_kwarg = "number"
    slug_field = "number"
    template_name = "browse/timetables/dataset_detail/licence_review_line_metadata.html"
    model = Dataset

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
        org_id = self.kwargs.get("org_id", None)
        kwargs["licence_number"] = licence_number
        line = self.request.GET.get("line")
        service_code = self.request.GET.get("service")
        pessenger_page = bool(self.request.GET.get("pf", 0))

        kwargs["line_name"] = line
        kwargs["service_code"] = service_code
        kwargs["pessenger_facing"] = pessenger_page
        kwargs["licence_page"] = True
        if pessenger_page:
            kwargs["licence_page"] = False
        kwargs = super().get_context_data(**kwargs)

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
            if licence_obj:
                kwargs["organisation"] = licence_obj.organisation
            else:
                kwargs["organisation"] = None

        dataset = self.object
        if dataset:
            live_revision = dataset.live_revision
        else:
            live_revision = None
        kwargs["pk"] = dataset.id if dataset else None

        kwargs["is_specific_feedback"] = flag_is_active("", "is_specific_feedback")
        kwargs["api_root"] = reverse("api:app:api-root", host=config.hosts.DATA_HOST)
        # Get the flag is_timetable_visualiser_active state
        is_timetable_visualiser_active = flag_is_active(
            "", "is_timetable_visualiser_active"
        )
        kwargs["is_timetable_visualiser_active"] = is_timetable_visualiser_active
        is_complete_service_pages_active = flag_is_active(
            "", FeatureFlags.COMPLETE_SERVICE_PAGES.value
        )
        kwargs["is_complete_service_pages_real_time_data_active"] = flag_is_active(
            "", FeatureFlags.COMPLETE_SERVICE_PAGES_REAL_TIME_DATA.value
        )
        kwargs["is_complete_service_pages_active"] = is_complete_service_pages_active
        kwargs["is_fares_require_attention_active"] = flag_is_active(
            "", FeatureFlags.FARES_REQUIRE_ATTENTION.value
        )
        kwargs["is_avl_require_attention_active"] = flag_is_active(
            "", FeatureFlags.AVL_REQUIRES_ATTENTION.value
        )

        kwargs["current_valid_files"] = []
        kwargs["service_type"] = "N/A"
        if live_revision:
            kwargs["current_valid_files"] = self.get_current_files(
                live_revision.id, kwargs["service_code"], kwargs["line_name"]
            )

            kwargs.update(
                self.get_service_type_data(
                    live_revision.id, line, service_code, kwargs["current_valid_files"]
                )
            )

            # If flag is enabled, show the timetable visualiser
            if is_timetable_visualiser_active:
                kwargs.update(
                    self.get_timetable_visualiser_data(
                        live_revision.id, line, service_code
                    )
                )

            if is_complete_service_pages_active and self.page == "licence":
                self.line = line
                self.service_code = service_code
                self.service = self.get_otc_service()
                licence_number = None
                self.service_code_exemption_map = {}
                self.seasonal_service_map = {}
                self.service_inscope = True
                self.service_inseason = True
                if self.service:
                    licence_number = self.service.licence.number
                    self.service_code_exemption_map = (
                        self.get_service_code_exemption_map(licence_number)
                    )
                    self.seasonal_service_map = self.get_seasonal_service_map(
                        licence_number
                    )
                    self.service_inscope = self.is_service_in_scope_service()
                    self.service_inseason = self.is_service_in_season_service()

                kwargs["service_inscope"] = self.service_inscope
                kwargs["service_inseason"] = self.service_inseason

                txc_file_attributes = (
                    self.get_timetable_files_for_line(
                        live_revision.id, service_code, line
                    )
                    .add_service_code(service_code)
                    .add_split_linenames()
                )

                kwargs.update(
                    self.get_avl_data(
                        txc_file_attributes,
                        line,
                    )
                )
                kwargs.update(self.get_fares_data(txc_file_attributes))
                kwargs.update(
                    self.get_timetables_data(
                        txc_file_attributes, service_code, dataset.id
                    )
                )

        return kwargs

    def get_service_type(self, revision_id, service_code, line_name) -> str:
        """
        Determine the service type based on the provided parameters.

        This method queries the database to retrieve service types for a given revision,
        service code, and line name. It then analyzes the retrieved service types to determine
        the overall service type.

        Parameters:
            revision_id (int): The ID of the revision.
            service_code (str): The service code.
            line_name (str): The name of the line.

        Returns:
            str: The determined service type, which can be one of the following:
                - "Standard" if all retrieved service types are "standard".
                - "Flexible" if all retrieved service types are "flexible".
                - "Flexible/Standard" if both "standard" and "flexible" service types are present.
        """
        all_service_types_list = []
        service_types_qs = (
            Service.objects.filter(
                revision=revision_id,
                service_code=service_code,
                name=line_name,
            )
            .values_list("service_type", flat=True)
            .distinct()
        )
        for service_type in service_types_qs:
            all_service_types_list.append(service_type)

        if all(service_type == "standard" for service_type in all_service_types_list):
            return "Standard"
        elif all(service_type == "flexible" for service_type in all_service_types_list):
            return "Flexible"
        return "Flexible/Standard"

    def get_timetable_files_for_line(
        self, revision_id, service_code, line_name
    ) -> List[TXCFileAttributes]:
        highest_revision_number = TXCFileAttributes.objects.filter(
            revision=revision_id,
            service_code=service_code,
            line_names__contains=[line_name],
        ).aggregate(highest_revision_number=Max("revision_number"))[
            "highest_revision_number"
        ]

        file_name_qs = TXCFileAttributes.objects.filter(
            revision=revision_id,
            service_code=service_code,
            line_names__contains=[line_name],
            revision_number=highest_revision_number,
        )
        return file_name_qs

    def get_current_files(self, revision_id, service_code, line_name) -> list:
        """
        Get the list of current valid files for a given revision, service code, and line name.

        This method retrieves the filenames of the current valid files for a specific revision,
        service code, and line name, considering the operating period start and end dates.

        Parameters:
            revision_id (int): The ID of the revision.
            service_code (str): The service code.
            line_name (str): The name of the line.

        Returns:
            list: A list of dictionaries, each containing information about a valid file, including:
                - "filename": The name of the file.
                - "start_date": The start date of the file's operating period.
                - "end_date": The end date of the file's operating period, if available.
        """
        valid_file_names = []
        today = datetime.now().date()

        file_name_qs = self.get_timetable_files_for_line(
            revision_id, service_code, line_name
        ).values_list(
            "filename",
            "operating_period_start_date",
            "operating_period_end_date",
        )

        for file_name in file_name_qs:
            operating_period_start_date = file_name[1]
            operating_period_end_date = file_name[2]

            if operating_period_start_date and operating_period_end_date:
                if (
                    operating_period_start_date <= today
                    and today <= operating_period_end_date
                ):
                    valid_file_names.append(
                        {
                            "filename": file_name[0],
                            "start_date": operating_period_start_date,
                            "end_date": operating_period_end_date,
                        }
                    )
            elif operating_period_start_date:
                if operating_period_start_date <= today:
                    valid_file_names.append(
                        {
                            "filename": file_name[0],
                            "start_date": operating_period_start_date,
                            "end_date": None,
                        }
                    )
            elif operating_period_end_date:
                if today <= operating_period_end_date:
                    valid_file_names.append(
                        {
                            "filename": file_name[0],
                            "start_date": None,
                            "end_date": operating_period_end_date,
                        }
                    )

        return valid_file_names

    def get_most_recent_modification_datetime(
        self, revision_id, service_code, line_name
    ):
        """
        Get the most recent modification datetime for a given revision, service code, and line name.

        This function retrieves the maximum modification datetime among all TXC file attributes
        matching the provided revision ID, service code, and line name.

        Parameters:
            revision_id (int): The ID of the revision.
            service_code (str): The service code.
            line_name (str): The name of the line.

        Returns:
            datetime: The most recent modification datetime, or None if no matching records are found.
        """
        return TXCFileAttributes.objects.filter(
            revision_id=revision_id,
            service_code=service_code,
            line_names__contains=[line_name],
        ).aggregate(max_modification_datetime=Max("modification_datetime"))[
            "max_modification_datetime"
        ]

    def get_lastest_operating_period_start_date(
        self, revision_id, service_code, line_name, recent_modification_datetime
    ):
        """
        Get the latest operating period start date for a given revision, service code,
        line name, and recent modification datetime.

        This method retrieves the maximum start date of the operating period among all TXC
        file attributes matching the provided parameters and having the specified recent
        modification datetime.

        Parameters:
            revision_id (int): The ID of the revision.
            service_code (str): The service code.
            line_name (str): The name of the line.
            recent_modification_datetime (datetime): The most recent modification datetime.

        Returns:
            datetime: The latest operating period start date, or None if no matching records are found.
        """
        return TXCFileAttributes.objects.filter(
            revision_id=revision_id,
            service_code=service_code,
            line_names__contains=[line_name],
            modification_datetime=recent_modification_datetime,
        ).aggregate(max_start_date=Max("operating_period_start_date"))["max_start_date"]

    def get_single_booking_arrangements_file(self, revision_id, service_code):
        """
        Retrieve the booking arrangements details from a single booking arrangements file
        for a given revision ID and service code.

        This function attempts to retrieve service IDs corresponding to the provided revision ID
        and service code. If no matching service IDs are found, it returns None. Otherwise, it
        queries the booking arrangements associated with the retrieved service IDs and returns
        a distinct set of booking arrangements details.

        Parameters:
            revision_id (int): The ID of the revision.
            service_code (str): The service code.

        Returns:
            QuerySet or None"""
        try:
            service_ids = (
                Service.objects.filter(revision=revision_id)
                .filter(service_code=service_code)
                .values_list("id", flat=True)
            )
        except Service.DoesNotExist:
            return None
        return (
            BookingArrangements.objects.filter(service_id__in=service_ids)
            .values_list("description", "email", "phone_number", "web_address")
            .distinct()
        )

    def get_valid_files(self, revision_id, valid_files, service_code, line_name):
        """
        Get the valid booking arrangements files based on the provided parameters.

        This method determines the valid booking arrangements file(s) for a given revision,
        service code, line name, and list of valid files. It considers various factors such
        as the number of valid files, the most recent modification datetime, and the operating
        period start date to determine the appropriate booking arrangements file(s) to return.

        Parameters:
            revision_id (int): The ID of the revision.
            valid_files (list): A list of valid files containing information about each file,
                including the filename, start date, and end date.
            service_code (str): The service code.
            line_name (str): The name of the line.

        Returns:
            QuerySet or None:
        """
        if len(valid_files) == 1:
            return self.get_single_booking_arrangements_file(revision_id, service_code)
        elif len(valid_files) > 1:
            booking_arrangements_qs = None
            most_recent_modification_datetime = (
                self.get_most_recent_modification_datetime(
                    revision_id, service_code, line_name
                )
            )
            booking_arrangements_qs = TXCFileAttributes.objects.filter(
                revision_id=revision_id,
                service_code=service_code,
                line_names__contains=[line_name],
                modification_datetime=most_recent_modification_datetime,
            )

            if len(booking_arrangements_qs) == 1:
                return self.get_single_booking_arrangements_file(
                    booking_arrangements_qs.first().revision_id, [service_code]
                )

            lastest_operating_period_start = (
                self.get_lastest_operating_period_start_date(
                    revision_id,
                    service_code,
                    line_name,
                    most_recent_modification_datetime,
                )
            )
            booking_arrangements_qs = booking_arrangements_qs.filter(
                operating_period_start_date=lastest_operating_period_start
            )

            if len(booking_arrangements_qs) == 1:
                return self.get_single_booking_arrangements_file(
                    booking_arrangements_qs.first().revision_id, [service_code]
                )

            booking_arrangements_qs = booking_arrangements_qs.order_by(
                "-filename"
            ).first()

            return self.get_single_booking_arrangements_file(
                booking_arrangements_qs.revision_id, [service_code]
            )

    def get_direction_timetable(
        self, df_timetable: pd.DataFrame, direction: str = "outbound"
    ) -> Dict:
        """
        Get the timetable details like the total, current page and the dataframe
        based on the timetable dataframe and the direction.

        :param df_timetable pd.DataFrame
        Timetable visualiser dataframe
        :param direction string
        Possible values can be 'outbound' or 'inbound'

        :return Dict
        {
            'total_page': "Total pages of the dataframe",
            'curr_page': "Current page",
            'show_all': "Flag to show all rows in dataframe",
            'df_timetable': "Dataframe sliced with rows and columns"
        }
        """

        if df_timetable.empty:
            return {
                "total_page": 0,
                "curr_page": 1,
                "show_all": False,
                "df_timetable": pd.DataFrame(),
                "total_row_count": 0,
            }

        if direction == "outbound":
            show_all_param = self.request.GET.get("showAllOutbound", "false")
            curr_page_param = int(self.request.GET.get("outboundPage", "1"))
        else:
            show_all_param = self.request.GET.get("showAllInbound", "false")
            curr_page_param = int(self.request.GET.get("inboundPage", "1"))
            pass

        show_all = show_all_param.lower() == "true"
        total_row_count, total_columns_count = df_timetable.shape
        total_page = ceil((total_columns_count - 1) / 10)
        curr_page_param = 1 if curr_page_param > total_page else curr_page_param
        page_size = 10
        # Adding 1 to always show the first column of stops
        col_start = ((curr_page_param - 1) * page_size) + 1
        col_end = min(total_columns_count, (curr_page_param * page_size) + 1)
        col_indexes_display = []
        for i in range(col_start, col_end):
            col_indexes_display.append(i)
        if len(col_indexes_display) > 0:
            col_indexes_display.insert(0, 0)
        row_count = min(total_row_count, 10)
        # Slice the dataframe by the 10 rows if show all is false
        df_timetable = (
            df_timetable.iloc[:, col_indexes_display]
            if show_all
            else df_timetable.iloc[:row_count, col_indexes_display]
        )

        return {
            "total_page": total_page,
            "curr_page": curr_page_param,
            "show_all": show_all,
            "df_timetable": df_timetable,
            "total_row_count": total_row_count,
        }

    def get_avl_data(
        self, txc_file_attributes: List[TXCFileAttributes], line_name: str
    ):
        """
        Get the AVL data for the Dataset
        """

        uncounted_activity_df = get_vehicle_activity_operatorref_linename()
        abods_registry = AbodsRegistery()
        synced_in_last_month = abods_registry.records()

        is_avl_compliant = True
        for file in txc_file_attributes:
            noc = file.national_operator_code
            if is_avl_compliant:
                is_avl_compliant = not is_avl_requires_attention(
                    noc, line_name, synced_in_last_month, uncounted_activity_df
                )
            else:
                break

        return {"is_avl_compliant": is_avl_compliant}

    def get_fares_data(
        self,
        txc_file_attributes: List[TXCFileAttributes],
    ):
        """
        Get the fares data for the dataset
        """
        is_fares_require_attention_active = flag_is_active(
            "", FeatureFlags.FARES_REQUIRE_ATTENTION.value
        )

        txc_map = dict(enumerate(txc_file_attributes))
        is_fares_compliant = True
        if is_fares_require_attention_active:
            fares_df = get_fares_dataset_map(txc_map)
            fra = FaresRequiresAttention(None)
            for txc_file in txc_file_attributes:
                if is_fares_compliant:
                    is_fares_compliant = not fra.is_fares_requires_attention(
                        txc_file, fares_df
                    )
                else:
                    break
        else:
            fares_df = pd.DataFrame()

        tariff_basis, product_name = [], []
        today = datetime.today().date()
        current_valid_files, future_files, expired_files = [], [], []
        dataset_id, org_id = None, None

        for row in fares_df.to_dict(orient="records"):
            tariff_basis.extend(row["tariff_basis"])
            product_name.extend(row["product_name"])
            dataset_id = row["dataset_id"]
            org_id = row["operator_id"]

            start_date = (
                row["valid_from"].date() if not pd.isnull(row["valid_from"]) else today
            )
            end_date = (
                row["valid_to"].date() if not pd.isnull(row["valid_to"]) else today
            )
            file_name = row["xml_file_name"]

            if end_date >= today >= start_date:
                current_valid_files.append(
                    self.get_file_object(row["valid_from"], row["valid_to"], file_name)
                )

            if start_date > today:
                future_files.append(
                    self.get_file_object(row["valid_from"], row["valid_to"], file_name)
                )

            if today > end_date:
                expired_files.append(
                    self.get_file_object(row["valid_from"], row["valid_to"], file_name)
                )

        return {
            "is_fares_compliant": is_fares_compliant,
            "fares_dataset_id": dataset_id,
            "fares_tariff_basis": tariff_basis,
            "fares_products": product_name,
            "fares_valid_files": current_valid_files,
            "fares_future_dated_files": future_files,
            "fares_expired_files": expired_files,
            "fares_org_id": org_id,
        }

    def get_file_object(self, start_date, end_date, file_name):
        """
        Return the object for the file details
        """
        return {
            "start_date": None if pd.isnull(start_date) else start_date,
            "end_date": None if pd.isnull(end_date) else end_date,
            "filename": file_name,
        }

    def get_timetables_data(
        self,
        file_attributes: list[TXCFileAttributes],
        service_code: str,
        dataset_id: int,
    ):
        """
        Get the timetables data for the dataset
        """
        today = datetime.today().date()
        current_valid_files = []
        future_files = []
        expired_files = []
        national_operator_code = set()

        for file in file_attributes:
            start_date = (
                file.operating_period_start_date
                if file.operating_period_start_date
                else today
            )
            end_date = (
                file.operating_period_end_date
                if file.operating_period_end_date
                else today
            )
            file_name = file.filename

            if end_date >= today >= start_date:
                current_valid_files.append(
                    self.get_file_object(
                        file.operating_period_start_date,
                        file.operating_period_end_date,
                        file_name,
                    )
                )

            national_operator_code.add(file.national_operator_code)
            if start_date > today:
                future_files.append(
                    self.get_file_object(
                        file.operating_period_start_date,
                        file.operating_period_end_date,
                        file_name,
                    )
                )

            if today > end_date:
                expired_files.append(
                    self.get_file_object(
                        file.operating_period_start_date,
                        file.operating_period_end_date,
                        file_name,
                    )
                )

        is_dqs_require_attention = flag_is_active(
            "", FeatureFlags.DQS_REQUIRE_ATTENTION.value
        )

        txcfa_map = get_line_level_txc_map_service_base([service_code])
        dqs_critical_issues_service_line_map = (
            get_dq_critical_observation_services_map(txcfa_map)
            if is_dqs_require_attention
            else []
        )

        txc_file = txcfa_map.get((service_code, self.line))
        is_timetable_compliant = False
        if self.service and txc_file:
            if len(dqs_critical_issues_service_line_map) == 0 and not is_stale(
                self.service, txc_file
            ):
                is_timetable_compliant = True

        national_operator_code = list(national_operator_code)
        return {
            "is_timetable_compliant": is_timetable_compliant,
            "timetables_dataset_id": dataset_id,
            "timetables_valid_files": current_valid_files,
            "timetables_future_dated_files": future_files,
            "timetables_expired_files": expired_files,
            "national_operator_code": ",".join(national_operator_code),
        }

    def get_otc_service(self):
        if not self.service_code:
            return None

        otc_map = {
            (
                f"{service.registration_number.replace('/', ':')}",
                f"{split_service_number}",
            ): service
            for service in OTCService.objects.add_otc_stale_date()
            .add_otc_association_date()
            .add_traveline_region_weca()
            .add_traveline_region_otc()
            .add_traveline_region_details()
            .filter(registration_number=self.service_code.replace(":", "/"))
            for split_service_number in service.service_number.split("|")
        }

        return otc_map.get((self.service_code, self.line))

    def get_timetable_visualiser_data(
        self, revision_id: int, line_name: str, service_code: str
    ):
        """
        Get the data for the timetable visualiser
        """

        date = self.request.GET.get("date", datetime.now().strftime("%Y-%m-%d"))
        # Regular expression pattern to match dates in yyyy-mm-dd format
        date_pattern = r"^\d{4}-\d{2}-\d{2}$"
        is_valid_date = re.match(date_pattern, date) is not None
        if not is_valid_date:
            date = datetime.now().strftime("%Y-%m-%d")

        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        timetable_inbound_outbound = TimetableVisualiser(
            revision_id,
            service_code,
            line_name,
            target_date,
            True,
        ).get_timetable_visualiser()

        vehicle_journey_codes = set()
        if not timetable_inbound_outbound["outbound"]["df_timetable"].empty:

            vehicle_journey_codes.update(
                timetable_inbound_outbound["outbound"]["df_timetable"].columns.tolist()
            )
        if not timetable_inbound_outbound["inbound"]["df_timetable"].empty:

            vehicle_journey_codes.update(
                timetable_inbound_outbound["inbound"]["df_timetable"].columns.tolist()
            )

        is_timetable_info_available = False
        timetable = {}
        for direction in ["outbound", "inbound"]:
            direction_details = timetable_inbound_outbound[direction]
            journey = direction_details["description"]
            journey = direction.capitalize() + " - " + journey if journey else ""
            bound_details = self.get_direction_timetable(
                direction_details["df_timetable"], direction
            )
            if (
                not is_timetable_info_available
                and not bound_details["df_timetable"].empty
            ):
                is_timetable_info_available = True
            timetable[direction] = {
                "df": bound_details["df_timetable"],
                "total_page": bound_details["total_page"],
                "total_row_count": bound_details["total_row_count"],
                "curr_page": bound_details["curr_page"],
                "show_all": bound_details["show_all"],
                "journey_name": journey,
                "stops": direction_details["stops"],
                "observations": direction_details.get("observations", {}),
                "page_param": direction + "Page",
                "show_all_param": "showAll" + direction.capitalize(),
                "start_and_end": direction_details["description"]
            }
        return {
            "curr_date": date,
            "timetable": timetable,
            "is_timetable_info_available": is_timetable_info_available,
            "vehicle_journey_codes": ",".join(vehicle_journey_codes),
        }

    def get_service_type_data(
        self, revision_id: int, line: str, service_code: str, current_valid_files: list
    ):
        """
        Get the data associated with service type
        """

        service_type = self.get_service_type(revision_id, service_code, line)
        data = {}
        data["service_type"] = service_type

        if service_type == "Flexible" or service_type == "Flexible/Standard":
            booking_arrangements_info = self.get_valid_files(
                revision_id,
                current_valid_files,
                service_code,
                line,
            )
            if booking_arrangements_info:
                data["booking_arrangements"] = booking_arrangements_info[0][0]
                data["booking_methods"] = booking_arrangements_info[0][1:]

        return data

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

    def is_service_in_scope_service(self) -> bool:
        """check is service is in scope or not system will
        check 3 points to decide in scope Service Exception,
        Seasonal Service Status and Traveling region

        Returns:
            bool: True if in scope else False
        """
        exemption = self.service_code_exemption_map.get(
            self.service.registration_number
        )
        traveline_regions = self.service.traveline_region
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

    def is_service_in_season_service(self) -> bool:
        """check is service is in season or not system will
        check 1 points to decide in season, Seasonal Service Status

        Returns:
            bool: True if in season else False
        """
        seasonal_service = self.seasonal_service_map.get(
            self.service.registration_number.replace("/", ":")
        )

        if seasonal_service and not seasonal_service.seasonal_status:
            return False
        return True

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
