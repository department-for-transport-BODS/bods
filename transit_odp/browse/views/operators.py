from typing import Dict
import pandas as pd
import config.hosts
from math import floor

from django.db.models import Avg, F
from django_hosts.resolvers import reverse
from waffle import flag_is_active

from config.hosts import DATA_HOST, PUBLISH_HOST
from transit_odp.avl.constants import MORE_DATA_NEEDED
from transit_odp.avl.post_publishing_checks.constants import NO_PPC_DATA
from transit_odp.avl.proxies import AVLDataset
from transit_odp.avl.require_attention.abods.registery import AbodsRegistery
from transit_odp.avl.require_attention.weekly_ppc_zip_loader import (
    get_vehicle_activity_operatorref_linename,
)
from transit_odp.browse.common import (
    get_in_scope_in_season_services_line_level,
    otc_map_txc_map_from_licence,
)
from transit_odp.browse.views.base_views import BaseListView
from transit_odp.common.views import BaseDetailView
from transit_odp.fares_validator.models import FaresValidationResult
from transit_odp.organisation.constants import (
    ENGLISH_TRAVELINE_REGIONS,
    EXPIRED,
    INACTIVE,
    AVLType,
    FaresType,
)
from transit_odp.organisation.csv.service_codes import STALENESS_STATUS
from transit_odp.organisation.models import (
    Dataset,
    Organisation,
    Licence as OrganisationLicence,
)
from transit_odp.organisation.models.data import SeasonalService, ServiceCodeExemption
from transit_odp.publish.requires_attention import (
    FaresRequiresAttention,
    evaluate_staleness,
    get_avl_requires_attention_line_level_data,
    get_dq_critical_observation_services_map,
    get_fares_compliance_status,
    get_fares_dataset_map,
    get_fares_requires_attention,
    get_fares_timeliness_status,
    get_requires_attention_line_level_data,
)
from transit_odp.common.constants import FeatureFlags


class OperatorsView(BaseListView):
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
            "", "is_avl_require_attention_active"
        )
        is_fares_require_attention_active = flag_is_active(
            "", FeatureFlags.FARES_REQUIRE_ATTENTION.value
        )
        context = super().get_context_data(**kwargs)
        organisation = self.object

        context["total_services_requiring_attention"] = len(
            get_requires_attention_line_level_data(organisation.id)
        )

        context["is_avl_require_attention_active"] = is_avl_require_attention_active
        if is_avl_require_attention_active:
            context["avl_total_services_requiring_attention"] = len(
                get_avl_requires_attention_line_level_data(organisation.id)
            )

        context["is_fares_require_attention_active"] = is_fares_require_attention_active
        if is_fares_require_attention_active:
            fares_reqiures_attention = FaresRequiresAttention(organisation.id)
            context["fares_total_services_requiring_attention"] = len(
                fares_reqiures_attention.get_fares_requires_attention_line_level_data()
            )

        context["total_in_scope_in_season_services"] = len(
            get_in_scope_in_season_services_line_level(organisation.id)
        )
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
            try:
                context["fares_total_services_requiring_attention_percentage"] = round(
                    100
                    * (
                        context["fares_total_services_requiring_attention"]
                        / context["total_in_scope_in_season_services"]
                    )
                )
            except ZeroDivisionError:
                context["fares_total_services_requiring_attention_percentage"] = 0

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
                "overall_ppc_score": floor(overall_ppc_score)
                if overall_ppc_score
                else overall_ppc_score,
            }
        )

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

    def get_queryset(self):
        licence_number = self.kwargs.get("number")
        return super().get_queryset().filter(number=licence_number)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        licence_number = self.kwargs.get("number", "-")
        context["licence_number"] = licence_number
        organisation_licence = self.get_object()
        context["pk"] = organisation_licence.id
        context["api_root"] = reverse("api:app:api-root", host=config.hosts.DATA_HOST)

        self.otc_map, self.txc_map = otc_map_txc_map_from_licence(licence_number)
        self.uncounted_activity_df = get_vehicle_activity_operatorref_linename()
        self.dq_critical_observation_map = get_dq_critical_observation_services_map(
            self.txc_map
        )
        self.fares_require_attention_df = get_fares_dataset_map(self.txc_map)

        self.service_code_exemption_map = self.get_service_code_exemption_map(
            licence_number
        )
        self.seasonal_service_map = self.get_seasonal_service_map(licence_number)

        abods_registry = AbodsRegistery()
        self.synced_in_last_month = abods_registry.records()

        self.fares_map = get_fares_dataset_map(self.txc_map)
        context["organisation"] = organisation_licence.organisation
        context["licence_services"] = self.otc_map

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
                service["dataset_id"] = service_txc_file.revision.dataset_id
            else:
                self.service_txc_file = None
                self.operator_ref = None
                service["dataset_id"] = None
            is_in_scope = self.is_service_in_scope()
            service["is_in_scope"] = is_in_scope

            if not is_in_scope:
                is_compliant = True
            elif (
                not self.is_fares_compliant()
                or not self.is_timetable_compliant()
                or not self.is_avl_compliant()
            ):
                is_compliant = False
            else:
                is_compliant = True
            service["is_compliant"] = is_compliant

        return context

    def is_fares_compliant(self) -> bool:
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

    def is_timetable_compliant(self):
        if not self.service_txc_file:
            return False

        rad = evaluate_staleness(self.service, self.service_txc_file)
        staleness_status = STALENESS_STATUS[rad.index(True)]
        if not self.is_dqs_compliant() or staleness_status != "Up to date":
            return False
        return True

    def is_dqs_compliant(self):
        return (
            True
            if (
                self.service.get("registration_number"),
                self.service.get("service_number"),
            )
            in self.dq_critical_observation_map
            else False
        )

    def is_avl_compliant(self):
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

    def is_service_in_scope(self):
        seasonal_service = self.seasonal_service_map.get(
            self.service.get("registration_number")
        )
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

        if not (
            not (exemption and exemption.registration_code) and is_english_region
        ) or (seasonal_service and not seasonal_service.seasonal_status):
            return False

        return True

    def get_service_compliant_status(
        self, registration_number: str, line_name: str
    ) -> bool:
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
                licence__organisation__licences__number__in=licence_number
            )
            .add_registration_number()
            .add_seasonal_status()
        }

    def get_service_code_exemption_map(
        self, licence_number: str
    ) -> Dict[str, ServiceCodeExemption]:
        return {
            service.registration_number.replace("/", ":"): service
            for service in ServiceCodeExemption.objects.add_registration_number().filter(
                licence__organisation__licences__number__in=licence_number
            )
        }
