from datetime import timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
from django.db.models import Subquery
from django.db.models.functions import Trim
from django.http import HttpResponse
from django.views import View
from waffle import flag_is_active

from transit_odp.avl.require_attention.abods.registery import AbodsRegistery
from transit_odp.avl.require_attention.weekly_ppc_zip_loader import (
    get_vehicle_activity_operatorref_linename,
)
from transit_odp.browse.common import (
    LTACSVHelper,
    get_all_naptan_atco_df,
    get_in_scope_in_season_lta_service_numbers,
    get_service_traveline_regions,
    get_weca_services_register_numbers,
    get_weca_traveline_region_map,
    ui_ltas_string,
)
from transit_odp.browse.lta_column_headers import (
    header_accessor_data,
    header_accessor_data_compliance_report,
    header_accessor_data_line_level,
)
from transit_odp.browse.views.base_views import BaseListView
from transit_odp.common.csv import CSVBuilder, CSVColumn
from transit_odp.common.views import BaseDetailView
from transit_odp.organisation.models import TXCFileAttributes
from transit_odp.organisation.models.data import SeasonalService, ServiceCodeExemption
from transit_odp.otc.constants import API_TYPE_EP, API_TYPE_WECA
from transit_odp.otc.models import LocalAuthority
from transit_odp.otc.models import Service as OTCService
from transit_odp.otc.models import UILta
from transit_odp.publish.requires_attention import (
    evaluate_staleness,
    get_dq_critical_observation_services_map,
    get_line_level_txc_map_lta,
    get_requires_attention_data_lta_line_level_length,
    get_txc_map_lta,
    is_stale,
)

STALENESS_STATUS = [
    "42 day look ahead is incomplete",
    "Service hasn't been updated within a year",
    "OTC variation not published",
]


def create_columns(header_accessor_list):
    columns = [
        CSVColumn(header=header, accessor=accessor)
        for header, accessor in header_accessor_list
    ]
    return columns


def get_line_level_otc_map_lta(lta_list) -> Dict[str, OTCService]:
    """
    Get a dictionary which includes all OTC Services for an organisation.
    """
    services_subquery_list = [
        x.registration_numbers.values("id")
        for x in lta_list
        if x.registration_numbers.values("id")
    ]

    if len(lta_list) > 0:
        weca_services_list = get_weca_services_register_numbers(lta_list[0].ui_lta)
        if weca_services_list:
            services_subquery_list.append(weca_services_list)

    if services_subquery_list:
        final_subquery = None
        for service_queryset in services_subquery_list:
            if final_subquery is None:
                final_subquery = service_queryset
            else:
                final_subquery = final_subquery | service_queryset
        final_subquery = final_subquery.distinct()

        return {
            (
                f"{split_service_number}",
                f"{service.registration_number.replace('/', ':')}",
            ): service
            for service in OTCService.objects.prefetch_related(
                "registration"
            ).get_all_otc_data_for_lta(final_subquery)
            for split_service_number in service.service_number.split("|")
        }
    else:
        return {}


def get_all_otc_map_lta(lta_list) -> Dict[str, OTCService]:
    """
    Get a dictionary which includes all OTC Services for an organisation.
    """
    services_subquery_list = [
        x.registration_numbers.values("id")
        for x in lta_list
        if x.registration_numbers.values("id")
    ]

    if len(lta_list) > 0:
        weca_services_list = get_weca_services_register_numbers(lta_list[0].ui_lta)
        if weca_services_list:
            services_subquery_list.append(weca_services_list)

    if services_subquery_list:
        final_subquery = None
        for service_queryset in services_subquery_list:
            if final_subquery is None:
                final_subquery = service_queryset
            else:
                final_subquery = final_subquery | service_queryset
        final_subquery = final_subquery.distinct()

        return {
            service.registration_number.replace("/", ":"): service
            for service in OTCService.objects.prefetch_related(
                "registration"
            ).get_all_otc_data_for_lta(final_subquery)
        }
    else:
        return {}


def get_seasonal_service_map(lta_list) -> Dict[str, SeasonalService]:
    """
    Get a dictionary which includes all the Seasonal Services
    for an organisation.
    """
    services_subquery_list = [
        x.registration_numbers.values("id")
        for x in lta_list
        if x.registration_numbers.values("id")
    ]

    if len(lta_list) > 0:
        weca_services_list = get_weca_services_register_numbers(lta_list[0].ui_lta)
        if weca_services_list:
            services_subquery_list.append(weca_services_list)

    if services_subquery_list:
        final_subquery = None
        for service_queryset in services_subquery_list:
            if final_subquery is None:
                final_subquery = service_queryset
            else:
                final_subquery = final_subquery | service_queryset
        final_subquery = final_subquery.distinct()

        return {
            service.registration_number.replace("/", ":"): service
            for service in SeasonalService.objects.filter(
                licence__organisation__licences__number__in=Subquery(
                    final_subquery.values("licence__number")
                )
            )
            .add_registration_number()
            .add_seasonal_status()
        }
    else:
        return {}


def get_service_code_exemption_map(lta_list) -> Dict[str, ServiceCodeExemption]:
    services_subquery_list = [
        x.registration_numbers.values("id")
        for x in lta_list
        if x.registration_numbers.values("id")
    ]

    if len(lta_list) > 0:
        weca_services_list = get_weca_services_register_numbers(lta_list[0].ui_lta)
        if weca_services_list:
            services_subquery_list.append(weca_services_list)

    if services_subquery_list:
        final_subquery = None
        for service_queryset in services_subquery_list:
            if final_subquery is None:
                final_subquery = service_queryset
            else:
                final_subquery = final_subquery | service_queryset
        final_subquery = final_subquery.distinct()

        return {
            service.registration_number.replace("/", ":"): service
            for service in ServiceCodeExemption.objects.add_registration_number().filter(
                licence__organisation__licences__number__in=Subquery(
                    final_subquery.values("licence__number")
                )
            )
        }
    else:
        return {}


class LocalAuthorityView(BaseListView):
    template_name = "browse/local_authority.html"
    model = LocalAuthority
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["updated_result"] = (
            self.get_queryset().values("ui_lta_name_trimmed").distinct().count()
        )
        context["q"] = self.request.GET.get("q", "")
        context["ordering"] = self.request.GET.get("ordering", "ui_lta_name_trimmed")
        all_ltas_current_page = context["object_list"]

        names = []
        name_set = set()
        lta_list_per_ui_ltas = {}

        all_ltas = self.get_model_objects().all()
        for lta in all_ltas:
            lta_list_per_ui_ltas.setdefault(lta.ui_lta_name_trimmed, []).append(lta)
            cleaned_name = lta.ui_lta_name_trimmed.replace("\xa0", " ")
            if cleaned_name not in name_set:
                names.append(cleaned_name)
                name_set.add(cleaned_name)

        ltas = {"names": names}
        context["ltas"] = ltas

        for lta in all_ltas_current_page:
            lta_list = lta_list_per_ui_ltas[lta.ui_lta_name_trimmed]
            setattr(lta, "auth_ids", [x.id for x in lta_list])
            context["total_in_scope_in_season_services"] = len(
                get_in_scope_in_season_lta_service_numbers(lta_list)
            )
            context[
                "total_services_requiring_attention"
            ] = get_requires_attention_data_lta_line_level_length(lta_list)

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
            setattr(
                lta,
                "services_require_attention_percentage",
                context["services_require_attention_percentage"],
            )

        return context

    def get_queryset(self):
        qs = self.get_model_objects().order_by(*self.get_ordering())
        return qs.distinct("ui_lta_name_trimmed")

    def get_model_objects(self):
        qs = self.model.objects.filter(ui_lta__name__isnull=False).annotate(
            ui_lta_name_trimmed=Trim("ui_lta__name")
        )

        search_term = self.request.GET.get("q", "").strip()
        if search_term:
            qs = qs.filter(ui_lta_name_trimmed__icontains=search_term)

        return qs

    def get_ordering(self):
        ordering = self.request.GET.get("ordering", "ui_lta_name_trimmed")
        if isinstance(ordering, str):
            ordering = (ordering,)
        return ordering


class LocalAuthorityDetailView(BaseDetailView):
    template_name = "browse/local_authority/local_authority_detail.html"
    model = LocalAuthority

    def get_object(self, queryset=None):
        combined_authority_ids = self.request.GET.get("auth_ids")
        if combined_authority_ids:
            combined_authority_ids = [
                int(lta_id.replace("[", "").replace("]", ""))
                for lta_id in combined_authority_ids.split(",")
            ]
        qs = self.model.objects.get(id=combined_authority_ids[0])
        return qs

    def get_context_data(self, **kwargs):
        is_avl_require_attention_active = flag_is_active(
            "", "is_avl_require_attention_active"
        )
        context = super().get_context_data(**kwargs)
        combined_authority_ids = self.request.GET.get("auth_ids")
        lta_objs = []
        context["auth_ids"] = combined_authority_ids

        if combined_authority_ids:
            combined_authority_ids = [
                int(lta_id.replace("[", "").replace("]", ""))
                for lta_id in combined_authority_ids.split(",")
            ]

        for combined_authority_id in combined_authority_ids:
            lta_objs.append(self.model.objects.get(id=combined_authority_id))

        context["total_in_scope_in_season_services"] = len(
            get_in_scope_in_season_lta_service_numbers(lta_objs)
        )

        context[
            "total_services_requiring_attention"
        ] = get_requires_attention_data_lta_line_level_length(lta_objs)

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

        context["is_avl_require_attention_active"] = is_avl_require_attention_active

        return context


class LocalAuthorityComplianceReportView(View):
    def get(self, *args, **kwargs):
        return self.render_to_response()

    def render_to_response(self):
        lta_objs = []
        combined_authority_ids = self.request.GET.get("auth_ids")

        if combined_authority_ids:
            combined_authority_ids = [
                int(lta_id.replace("[", "").replace("]", ""))
                for lta_id in combined_authority_ids.split(",")
            ]

        for combined_authority_id in combined_authority_ids:
            lta_objs.append(LocalAuthority.objects.get(id=combined_authority_id))

        updated_ui_lta_name = lta_objs[0].ui_lta_name().replace(",", " ").strip()

        csv_filename = f"{updated_ui_lta_name} compliance report.csv"

        csv_export = LTAComplianceReportCSV(lta_objs)
        file_ = csv_export.to_string()
        response = HttpResponse(file_, content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={csv_filename}"
        return response


class LocalAuthorityExportView(View):
    def get(self, *args, **kwargs):
        return self.render_to_response()

    def render_to_response(self):
        lta_objs = []
        combined_authority_ids = self.request.GET.get("auth_ids")

        if combined_authority_ids:
            combined_authority_ids = [
                int(lta_id.replace("[", "").replace("]", ""))
                for lta_id in combined_authority_ids.split(",")
            ]

        for combined_authority_id in combined_authority_ids:
            lta_objs.append(LocalAuthority.objects.get(id=combined_authority_id))

        updated_ui_lta_name = lta_objs[0].ui_lta_name().replace(",", " ").strip()

        csv_filename = (
            f"{updated_ui_lta_name}_detailed service code export detailed export.csv"
        )

        csv_export = LTACSV(lta_objs)
        file_ = csv_export.to_string()
        response = HttpResponse(file_, content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={csv_filename}"
        return response


class LocalAuthorityLineLevelExportView(View):
    def get(self, *args, **kwargs):
        return self.render_to_response()

    def render_to_response(self):
        lta_objs = []
        combined_authority_ids = self.request.GET.get("auth_ids")

        if combined_authority_ids:
            combined_authority_ids = [
                int(lta_id.replace("[", "").replace("]", ""))
                for lta_id in combined_authority_ids.split(",")
            ]

        for combined_authority_id in combined_authority_ids:
            lta_objs.append(LocalAuthority.objects.get(id=combined_authority_id))

        updated_ui_lta_name = lta_objs[0].ui_lta_name().replace(",", " ").strip()

        csv_filename = f"{updated_ui_lta_name}_detailed line level service code export detailed export.csv"

        csv_export = LTALineLevelCSV(lta_objs)
        file_ = csv_export.to_string()
        response = HttpResponse(file_, content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={csv_filename}"
        return response


class LTAComplianceReportCSV(CSVBuilder, LTACSVHelper):
    columns = create_columns(header_accessor_data_compliance_report)

    def _update_data(
        self,
        service: Optional[OTCService],
        service_number: Optional[str],
        file_attribute: Optional[TXCFileAttributes],
        seasonal_service: Optional[SeasonalService],
        exempted: Optional[bool],
        staleness_status: Optional[str],
        require_attention: str,
        traveline_region: str,
        ui_lta_name: str,
        avl_published_status: str,
        error_in_avl_to_timetable_matching: str,
        avl_requires_attention: str,
        overall_requires_attention: str,
        dq_require_attention: str,
    ) -> None:
        self._object_list.append(
            {
                "require_attention": require_attention,
                "scope_status": exempted,
                "otc_licence_number": service and service.otc_licence_number,
                "otc_registration_number": service and service.registration_number,
                "otc_service_number": service_number,
                "otc_operator": service
                and service.operator
                and service.operator.operator_name,
                "otc_licence": service and service.licence,
                "otc_service_type_description": service
                and service.service_type_description,
                "otc_variation_number": service and service.variation_number,
                "otc_effective_date": service and service.effective_date,
                "otc_received_date": service and service.received_date,
                "operator_name": file_attribute and file_attribute.organisation_name,
                "licence_number": file_attribute and file_attribute.licence_number,
                "service_code": file_attribute and file_attribute.service_code,
                "line_name": file_attribute
                and self.modify_dataset_line_name(file_attribute.line_names),
                "operating_period_start_date": file_attribute
                and (file_attribute.operating_period_start_date),
                "operating_period_end_date": file_attribute
                and (file_attribute.operating_period_end_date),
                "revision_number": file_attribute and file_attribute.revision_number,
                "last_modified_date": file_attribute
                and (file_attribute.modification_datetime.date()),
                "dataset_id": file_attribute and file_attribute.revision.dataset_id,
                "xml_filename": file_attribute and file_attribute.filename,
                "seasonal_status": seasonal_service
                and seasonal_service.seasonal_status,
                "seasonal_start": seasonal_service and seasonal_service.start,
                "seasonal_end": seasonal_service and seasonal_service.end,
                "staleness_status": staleness_status,
                "effective_seasonal_start_date": seasonal_service
                and seasonal_service.start - timedelta(days=42),
                "effective_stale_date_end_date": file_attribute
                and file_attribute.effective_stale_date_end_date,
                "effective_stale_date_last_modified_date": file_attribute
                and file_attribute.effective_stale_date_last_modified_date,
                "last_modified_lt_effective_stale_date_otc": service
                and file_attribute
                and (
                    file_attribute.modification_datetime.date()
                    < service.effective_stale_date_otc_effective_date
                ),
                "effective_stale_date_otc_effective_date": service
                and (service.effective_stale_date_otc_effective_date),
                "national_operator_code": file_attribute
                and file_attribute.national_operator_code,
                "traveline_region": traveline_region,
                "ui_lta_name": ui_lta_name,
                "otc_licence_expiry_date": service and service.licence.expiry_date,
                "avl_published_status": avl_published_status,
                "error_in_avl_to_timetable_matching": error_in_avl_to_timetable_matching,
                "avl_requires_attention": avl_requires_attention,
                "overall_requires_attention": overall_requires_attention,
                "dq_require_attention": dq_require_attention,
            }
        )

    def __init__(self, combined_authorities):
        super().__init__()
        self._combined_authorities = combined_authorities
        self._object_list = []
        self.otc_service_traveline_region = {}
        self.otc_service_ui_ltas = {}
        self.weca_traveline_region_status = {}
        self.otc_traveline_region_status = {}

    def modify_dataset_line_name(self, line_names: list) -> str:
        return " ".join(line_name for line_name in line_names)

    def get_overall_requires_attention(
        self,
        timetable_requires_attention: Optional[str],
        avl_requires_attention: Optional[str],
        exempted: Optional[bool],
        seasonal_service: Optional[SeasonalService],
    ) -> str:
        """
        Returns value for 'Requires attention' column based on the following logic:
            If 'Scope Status' = Out of Scope OR 'Seasonal Status' = Out of Season,
            then 'Requires attention' = No.
            If 'Timetables requires attention' = No AND 'AVL requires attention' = No,
            then 'Requires attention' = No.
            If 'Timetables requires attention' = Yes OR 'AVL requires attention' = Yes,
            then 'Requires attention' = Yes.
        Args:
            otc_service (dict): OTC Service dictionary

        Returns:
            str: Yes or No for 'Requires attention' column
        """
        if exempted or (seasonal_service and not seasonal_service.seasonal_status):
            return "No"
        if (timetable_requires_attention == "No") and (avl_requires_attention == "No"):
            return "No"
        return "Yes"

    def _get_require_attention(
        self,
        exempted: Optional[bool],
        seasonal_service: Optional[SeasonalService],
        service: Optional[OTCService],
        file_attribute: Optional[TXCFileAttributes],
        staleness_status: Optional[str],
        dq_require_attention: Optional[str],
    ) -> str:
        if exempted or (seasonal_service and not seasonal_service.seasonal_status):
            return "No"
        if file_attribute is not None:
            registered_status = True if service.otc_licence_number else False
            published_status = True if file_attribute.revision.dataset_id else False

            if (
                registered_status
                and (not seasonal_service or seasonal_service.seasonal_status)
                and (not exempted)
                and published_status
                and (staleness_status == "Up to date")
                and dq_require_attention == "No"
            ):
                return "No"
        return "Yes"

    def get_avl_published_status(
        self, operator_ref, line_name, synced_in_last_month
    ) -> str:
        """
        Returns value for 'AVL Published Status' column.

        Args:
            operator_ref (str): National Operator Code
            line_name (str): Service Number
            synced_in_last_month: Records from ABODS API

        Returns:
            str: Yes or No for 'AVL Published Status' column
        """
        if f"{line_name}__{operator_ref}" in synced_in_last_month:
            return "Yes"
        return "No"

    def get_error_in_avl_to_timetable_matching(self, operator_ref, line_name) -> str:
        """
        Returns value for 'Error in AVL to Timetable Matching' column.

        Args:
            operator_ref (str): National Operator Code
            line_name (str): Service Number

        Returns:
            str: Yes or No for 'Error in AVL to Timetable Matching' column
        """
        uncounted_activity_df = get_vehicle_activity_operatorref_linename()

        if not uncounted_activity_df.loc[
            (uncounted_activity_df["OperatorRef"] == operator_ref)
            & (
                uncounted_activity_df["LineRef"].isin(
                    [line_name, line_name.replace(" ", "_")]
                )
            )
        ].empty:
            return "Yes"
        return "No"

    def get_avl_requires_attention(
        self, avl_published_status: str, error_in_avl_to_timetable_matching: str
    ) -> str:
        """
        Returns value for 'AVL requires attention' column based on the following logic:
            If both 'AVL Published Status' equal to Yes and 'Error in AVL to Timetable Matching' equal to No,
            then 'AVL requires attention' = No.
            else
            the value 'AVL requires attention' = Yes.

        Args:
            avl_published_status (str): Value of 'AVL Published Status'
            error_in_avl_to_timetable_matching (str): Value of 'Error in AVL to Timetable Matching'

        Returns:
            str: Yes or No for 'AVL requires attention' column
        """
        if (avl_published_status == "Yes") and (
            error_in_avl_to_timetable_matching == "No"
        ):
            return "No"
        return "Yes"

    def get_otc_service_traveline_region(
        self, ui_ltas: List[UILta], ui_ltas_dict_key: Tuple[UILta]
    ) -> str:
        """Returns a pipe "|" seprate list of all the traveline regions
        the UI LTAs belongs to, Dict will be prepared for the values

        Args:
            ui_ltas (List[UILta]): List of UI LTAs
            ui_ltas_dict_key (Tuple[UILta]): Tuple of UI LTAs to be used
            as key for the dictionary

        Returns:
            str: pipe "|" seprated string of UI LTA's
        """
        if ui_ltas_dict_key not in self.otc_service_traveline_region:
            self.otc_service_traveline_region[
                ui_ltas_dict_key
            ] = get_service_traveline_regions(ui_ltas)
        return self.otc_service_traveline_region[ui_ltas_dict_key]

    def get_otc_ui_lta(
        self, ui_ltas: List[UILta], ui_ltas_dict_key: Tuple[UILta]
    ) -> str:
        """Return a pipe "|" seprate string of the UI LTA names for the service
        dictionary of the ui ltas will be maintained in order to minimize the
        manipulations

        Args:
            ui_ltas (List[UILta]): List of UI LTAs the service belongs to
            ui_ltas_dict_key (Tuple[UILta]): Tuple of UI LTAs to make key in dict

        Returns:
            str: Pipe "|" seprated list of UI LTAs
        """
        if ui_ltas_dict_key not in self.otc_service_ui_ltas:
            self.otc_service_ui_ltas[ui_ltas_dict_key] = ui_ltas_string(ui_ltas)
        return self.otc_service_ui_ltas[ui_ltas_dict_key]

    def get_is_english_region_otc(
        self,
        ui_ltas: List[UILta],
        ui_ltas_dict_key: Tuple[UILta],
        naptan_adminarea_df: pd.DataFrame,
    ) -> bool:
        """
        Find if the annotated key is_english_region for naptan admin area is True or
        False for any of the UI LTAs this service belongs to

        Args:
            ui_ltas (List[UILta]): List of UI LTAs the service belongs to
            ui_ltas_dict_key (Tuple[UILta]): Tuple value of UI LTAs for keys
            naptan_adminarea_df (pd.DataFrame): Dataframe for the admin area values

        Returns:
            bool: Returns True is the atco code passed belongs to an enlish region
        """
        if ui_ltas_dict_key not in self.otc_traveline_region_status:
            self.otc_traveline_region_status[
                ui_ltas_dict_key
            ] = not naptan_adminarea_df.empty and any(
                (
                    naptan_adminarea_df[
                        naptan_adminarea_df["ui_lta_id"].isin(
                            [ui_lta.id for ui_lta in ui_ltas]
                        )
                    ]
                )["is_english_region"]
            )
        return self.otc_traveline_region_status[ui_ltas_dict_key]

    def get_is_english_region_weca(
        self, atco_code: str, naptan_adminarea_df: pd.DataFrame
    ) -> bool:
        """Find if the annotated key is_english_region is True or False for
        The provided atco code
        For weca services if atco code belongs to an Naptan Admin area
        Such services will be considered in english region.

        Args:
            atco_code (str): Atco code to be checked
            naptan_adminarea_df (pd.DataFrame): Naptan admin areas list

        Returns:
            bool: Returns True is the atco code passed belongs to an enlish region
        """
        if atco_code not in self.weca_traveline_region_status:
            self.weca_traveline_region_status[
                atco_code
            ] = not naptan_adminarea_df.empty and any(
                (naptan_adminarea_df[naptan_adminarea_df["atco_code"] == atco_code])[
                    "is_english_region"
                ]
            )
        return self.weca_traveline_region_status[atco_code]

    def get_otc_service_bods_data(self, lta_list) -> None:
        """
        Compares an LTA's OTC and WECA Services dictionaries list with
        TXCFileAttributes dictionaries list and the SeasonalService list
        to determine which OTC and WECA Services require attention and which
        doesn't ie. not live in BODS at all, or live but meeting new
        Staleness conditions.
        """
        ui_lta = lta_list[0].ui_lta
        otc_map = get_line_level_otc_map_lta(lta_list)
        txcfa_map = get_line_level_txc_map_lta(lta_list)
        dq_critical_observation_map = get_dq_critical_observation_services_map(
            txcfa_map
        )
        seasonal_service_map = get_seasonal_service_map(lta_list)
        service_code_exemption_map = get_service_code_exemption_map(lta_list)
        naptan_adminarea_df = get_all_naptan_atco_df()
        traveline_region_map_weca = get_weca_traveline_region_map(ui_lta)
        service_number_registration_number_map = set(otc_map)
        service_number_registration_number_map = sorted(
            service_number_registration_number_map
        )
        abods_registry = AbodsRegistery()
        synced_in_last_month = abods_registry.records()

        for (
            service_number,
            registration_number,
        ) in service_number_registration_number_map:
            service = otc_map.get((service_number, registration_number))
            file_attribute = txcfa_map.get((service_number, registration_number))
            seasonal_service = seasonal_service_map.get(registration_number)
            exemption = service_code_exemption_map.get(registration_number)

            if service.api_type in [API_TYPE_WECA, API_TYPE_EP]:
                is_english_region = self.get_is_english_region_weca(
                    service.atco_code, naptan_adminarea_df
                )
                ui_lta_name = ui_lta.name
                traveline_region = traveline_region_map_weca.get(service.atco_code, "")
            else:
                (
                    is_english_region,
                    ui_lta_name,
                    traveline_region,
                ) = self.get_otc_service_details(service, naptan_adminarea_df)

            exempted = False
            if not (
                not (exemption and exemption.registration_code) and is_english_region
            ):
                exempted = True

            dq_require_attention = "No"
            if (registration_number, service_number) in dq_critical_observation_map:
                dq_require_attention = "Yes"

            staleness_status = "Up to date"
            if file_attribute is None:
                require_attention = self._get_require_attention(
                    exempted,
                    seasonal_service,
                    service,
                    None,
                    staleness_status,
                    dq_require_attention,
                )
            elif service and is_stale(service, file_attribute):
                rad = evaluate_staleness(service, file_attribute)
                staleness_status = STALENESS_STATUS[rad.index(True)]
                require_attention = self._get_require_attention(
                    exempted,
                    seasonal_service,
                    service,
                    file_attribute,
                    staleness_status,
                    dq_require_attention,
                )
            else:
                require_attention = "No"

            if file_attribute is not None:
                avl_published_status = self.get_avl_published_status(
                    file_attribute.national_operator_code,
                    service_number,
                    synced_in_last_month,
                )
                error_in_avl_to_timetable_matching = (
                    self.get_error_in_avl_to_timetable_matching(
                        file_attribute.national_operator_code,
                        service_number,
                    )
                )
            else:
                avl_published_status = self.get_avl_published_status(
                    "", service_number, synced_in_last_month
                )
                error_in_avl_to_timetable_matching = (
                    self.get_error_in_avl_to_timetable_matching("", service_number)
                )

            avl_requires_attention = self.get_avl_requires_attention(
                avl_published_status,
                error_in_avl_to_timetable_matching,
            )

            overall_requires_attention = self.get_overall_requires_attention(
                require_attention,
                avl_requires_attention,
                exempted,
                seasonal_service,
                dq_require_attention,
            )

            self._update_data(
                service,
                service_number,
                file_attribute,
                seasonal_service,
                exempted,
                staleness_status,
                require_attention,
                traveline_region,
                ui_lta_name,
                avl_published_status,
                error_in_avl_to_timetable_matching,
                avl_requires_attention,
                overall_requires_attention,
                dq_require_attention,
            )

    def get_queryset(self):
        self.get_otc_service_bods_data(self._combined_authorities)
        return self._object_list


class LTACSV(CSVBuilder, LTACSVHelper):
    columns = create_columns(header_accessor_data)

    def _update_data(
        self,
        service: Optional[OTCService],
        file_attribute: Optional[TXCFileAttributes],
        seasonal_service: Optional[SeasonalService],
        exempted: Optional[bool],
        staleness_status: Optional[str],
        require_attention: str,
        traveline_region: str,
        ui_lta_name: str,
    ) -> None:
        self._object_list.append(
            {
                "require_attention": require_attention,
                "scope_status": exempted,
                "otc_licence_number": service and service.otc_licence_number,
                "otc_registration_number": service and service.registration_number,
                "otc_service_number": service and service.service_number,
                "operator_name": file_attribute and file_attribute.organisation_name,
                "licence_number": file_attribute and file_attribute.licence_number,
                "service_code": file_attribute and file_attribute.service_code,
                "line_name": file_attribute
                and self.modify_dataset_line_name(file_attribute.line_names),
                "operating_period_start_date": file_attribute
                and (file_attribute.operating_period_start_date),
                "operating_period_end_date": file_attribute
                and (file_attribute.operating_period_end_date),
                "revision_number": file_attribute and file_attribute.revision_number,
                "last_modified_date": file_attribute
                and (file_attribute.modification_datetime.date()),
                "dataset_id": file_attribute and file_attribute.revision.dataset_id,
                "xml_filename": file_attribute and file_attribute.filename,
                "seasonal_status": seasonal_service
                and seasonal_service.seasonal_status,
                "seasonal_start": seasonal_service and seasonal_service.start,
                "seasonal_end": seasonal_service and seasonal_service.end,
                "staleness_status": staleness_status,
                "effective_seasonal_start_date": seasonal_service
                and seasonal_service.start - timedelta(days=42),
                "effective_stale_date_end_date": file_attribute
                and file_attribute.effective_stale_date_end_date,
                "effective_stale_date_last_modified_date": file_attribute
                and file_attribute.effective_stale_date_last_modified_date,
                "last_modified_lt_effective_stale_date_otc": service
                and file_attribute
                and (
                    file_attribute.modification_datetime.date()
                    < service.effective_stale_date_otc_effective_date
                ),
                "effective_stale_date_otc_effective_date": service
                and (service.effective_stale_date_otc_effective_date),
                "national_operator_code": file_attribute
                and file_attribute.national_operator_code,
                "traveline_region": traveline_region,
                "ui_lta_name": ui_lta_name,
            }
        )

    def __init__(self, combined_authorities):
        super().__init__()
        self._combined_authorities = combined_authorities
        self._object_list = []
        self.otc_service_traveline_region = {}
        self.otc_service_ui_ltas = {}
        self.weca_traveline_region_status = {}
        self.otc_traveline_region_status = {}

    def modify_dataset_line_name(self, line_names: list) -> str:
        return " ".join(line_name for line_name in line_names)

    def _get_require_attention(
        self,
        exempted: Optional[bool],
        seasonal_service: Optional[SeasonalService],
    ) -> str:
        if exempted or (seasonal_service and not seasonal_service.seasonal_status):
            return "No"
        return "Yes"

    def get_otc_service_traveline_region(
        self, ui_ltas: List[UILta], ui_ltas_dict_key: Tuple[UILta]
    ) -> str:
        """Returns a pipe "|" seprate list of all the traveline regions
        the UI LTAs belongs to, Dict will be prepared for the values

        Args:
            ui_ltas (List[UILta]): List of UI LTAs
            ui_ltas_dict_key (Tuple[UILta]): Tuple of UI LTAs to be used
            as key for the dictionary

        Returns:
            str: pipe "|" seprated string of UI LTA's
        """
        if ui_ltas_dict_key not in self.otc_service_traveline_region:
            self.otc_service_traveline_region[
                ui_ltas_dict_key
            ] = get_service_traveline_regions(ui_ltas)
        return self.otc_service_traveline_region[ui_ltas_dict_key]

    def get_otc_ui_lta(
        self, ui_ltas: List[UILta], ui_ltas_dict_key: Tuple[UILta]
    ) -> str:
        """Return a pipe "|" seprate string of the UI LTA names for the service
        dictionary of the ui ltas will be maintained in order to minimize the
        manipulations

        Args:
            ui_ltas (List[UILta]): List of UI LTAs the service belongs to
            ui_ltas_dict_key (Tuple[UILta]): Tuple of UI LTAs to make key in dict

        Returns:
            str: Pipe "|" seprated list of UI LTAs
        """
        if ui_ltas_dict_key not in self.otc_service_ui_ltas:
            self.otc_service_ui_ltas[ui_ltas_dict_key] = ui_ltas_string(ui_ltas)
        return self.otc_service_ui_ltas[ui_ltas_dict_key]

    def get_is_english_region_otc(
        self,
        ui_ltas: List[UILta],
        ui_ltas_dict_key: Tuple[UILta],
        naptan_adminarea_df: pd.DataFrame,
    ) -> bool:
        """Find if the annotated key is_english_region for naptan admin area is True or False for
        any of the UI LTAs this service belongs to

        Args:
            ui_ltas (List[UILta]): List of UI LTAs the service belongs to
            ui_ltas_dict_key (Tuple[UILta]): Tuple value of UI LTAs for keys
            naptan_adminarea_df (pd.DataFrame): Dataframe for the admin area values

        Returns:
            bool: Returns True is the atco code passed belongs to an enlish region
        """
        if ui_ltas_dict_key not in self.otc_traveline_region_status:
            self.otc_traveline_region_status[
                ui_ltas_dict_key
            ] = not naptan_adminarea_df.empty and any(
                (
                    naptan_adminarea_df[
                        naptan_adminarea_df["ui_lta_id"].isin(
                            [ui_lta.id for ui_lta in ui_ltas]
                        )
                    ]
                )["is_english_region"]
            )
        return self.otc_traveline_region_status[ui_ltas_dict_key]

    def get_is_english_region_weca(
        self, atco_code: str, naptan_adminarea_df: pd.DataFrame
    ) -> bool:
        """Find if the annotated key is_english_region is True or False for
        The provided atco code
        For weca services if atco code belongs to an Naptan Admin area
        Such services will be considered in english region.

        Args:
            atco_code (str): Atco code to be checked
            naptan_adminarea_df (pd.DataFrame): Naptan admin areas list

        Returns:
            bool: Returns True is the atco code passed belongs to an enlish region
        """
        if atco_code not in self.weca_traveline_region_status:
            self.weca_traveline_region_status[
                atco_code
            ] = not naptan_adminarea_df.empty and any(
                (naptan_adminarea_df[naptan_adminarea_df["atco_code"] == atco_code])[
                    "is_english_region"
                ]
            )
        return self.weca_traveline_region_status[atco_code]

    def get_otc_service_bods_data(self, lta_list) -> None:
        """
        Compares an LTA's OTC and WECA Services dictionaries list with
        TXCFileAttributes dictionaries list and the SeasonalService list
        to determine which OTC and WECA Services require attention and which
        doesn't ie. not live in BODS at all, or live but meeting new
        Staleness conditions.
        """
        ui_lta = lta_list[0].ui_lta
        otc_map = get_all_otc_map_lta(lta_list)
        txcfa_map = get_txc_map_lta(lta_list)
        seasonal_service_map = get_seasonal_service_map(lta_list)
        service_code_exemption_map = get_service_code_exemption_map(lta_list)
        naptan_adminarea_df = get_all_naptan_atco_df()
        traveline_region_map_weca = get_weca_traveline_region_map(ui_lta)
        services_code = set(otc_map)
        services_code = sorted(services_code)

        for service_code in services_code:
            service = otc_map.get(service_code)
            file_attribute = txcfa_map.get(service_code)
            seasonal_service = seasonal_service_map.get(service_code)
            exemption = service_code_exemption_map.get(service_code)

            if service.api_type in [API_TYPE_WECA, API_TYPE_EP]:
                is_english_region = self.get_is_english_region_weca(
                    service.atco_code, naptan_adminarea_df
                )
                ui_lta_name = ui_lta.name
                traveline_region = traveline_region_map_weca.get(service.atco_code, "")
            else:
                (
                    is_english_region,
                    ui_lta_name,
                    traveline_region,
                ) = self.get_otc_service_details(service, naptan_adminarea_df)

            exempted = False
            if not (
                not (exemption and exemption.registration_code) and is_english_region
            ):
                exempted = True

            staleness_status = "Up to date"
            if file_attribute is None:
                require_attention = self._get_require_attention(
                    exempted, seasonal_service
                )
            elif service and is_stale(service, file_attribute):
                rad = evaluate_staleness(service, file_attribute)
                staleness_status = STALENESS_STATUS[rad.index(True)]
                require_attention = self._get_require_attention(
                    exempted, seasonal_service
                )
            else:
                require_attention = "No"

            self._update_data(
                service,
                file_attribute,
                seasonal_service,
                exempted,
                staleness_status,
                require_attention,
                traveline_region,
                ui_lta_name,
            )

    def get_queryset(self):
        self.get_otc_service_bods_data(self._combined_authorities)
        return self._object_list


class LTALineLevelCSV(CSVBuilder, LTACSVHelper):
    columns = create_columns(header_accessor_data_line_level)

    def _update_data(
        self,
        service: Optional[OTCService],
        service_number: Optional[str],
        file_attribute: Optional[TXCFileAttributes],
        seasonal_service: Optional[SeasonalService],
        exempted: Optional[bool],
        staleness_status: Optional[str],
        require_attention: str,
        traveline_region: str,
        ui_lta_name: str,
    ) -> None:
        self._object_list.append(
            {
                "require_attention": require_attention,
                "scope_status": exempted,
                "otc_licence_number": service and service.otc_licence_number,
                "otc_registration_number": service and service.registration_number,
                "otc_service_number": service_number,
                "otc_operator": service
                and service.operator
                and service.operator.operator_name,
                "otc_licence": service and service.licence,
                "otc_service_type_description": service
                and service.service_type_description,
                "otc_variation_number": service and service.variation_number,
                "otc_effective_date": service and service.effective_date,
                "otc_received_date": service and service.received_date,
                "operator_name": file_attribute and file_attribute.organisation_name,
                "licence_number": file_attribute and file_attribute.licence_number,
                "service_code": file_attribute and file_attribute.service_code,
                "line_name": file_attribute
                and self.modify_dataset_line_name(file_attribute.line_names),
                "operating_period_start_date": file_attribute
                and (file_attribute.operating_period_start_date),
                "operating_period_end_date": file_attribute
                and (file_attribute.operating_period_end_date),
                "revision_number": file_attribute and file_attribute.revision_number,
                "last_modified_date": file_attribute
                and (file_attribute.modification_datetime.date()),
                "dataset_id": file_attribute and file_attribute.revision.dataset_id,
                "xml_filename": file_attribute and file_attribute.filename,
                "seasonal_status": seasonal_service
                and seasonal_service.seasonal_status,
                "seasonal_start": seasonal_service and seasonal_service.start,
                "seasonal_end": seasonal_service and seasonal_service.end,
                "staleness_status": staleness_status,
                "effective_seasonal_start_date": seasonal_service
                and seasonal_service.start - timedelta(days=42),
                "effective_stale_date_end_date": file_attribute
                and file_attribute.effective_stale_date_end_date,
                "effective_stale_date_last_modified_date": file_attribute
                and file_attribute.effective_stale_date_last_modified_date,
                "last_modified_lt_effective_stale_date_otc": service
                and file_attribute
                and (
                    file_attribute.modification_datetime.date()
                    < service.effective_stale_date_otc_effective_date
                ),
                "effective_stale_date_otc_effective_date": service
                and (service.effective_stale_date_otc_effective_date),
                "national_operator_code": file_attribute
                and file_attribute.national_operator_code,
                "traveline_region": traveline_region,
                "ui_lta_name": ui_lta_name,
                "otc_licence_expiry_date": service and service.licence.expiry_date,
            }
        )

    def __init__(self, combined_authorities):
        super().__init__()
        self._combined_authorities = combined_authorities
        self._object_list = []
        self.otc_service_traveline_region = {}
        self.otc_service_ui_ltas = {}
        self.weca_traveline_region_status = {}
        self.otc_traveline_region_status = {}

    def modify_dataset_line_name(self, line_names: list) -> str:
        return " ".join(line_name for line_name in line_names)

    def _get_require_attention(
        self,
        exempted: Optional[bool],
        seasonal_service: Optional[SeasonalService],
    ) -> str:
        if exempted or (seasonal_service and not seasonal_service.seasonal_status):
            return "No"
        return "Yes"

    def get_otc_service_traveline_region(
        self, ui_ltas: List[UILta], ui_ltas_dict_key: Tuple[UILta]
    ) -> str:
        """Returns a pipe "|" seprate list of all the traveline regions
        the UI LTAs belongs to, Dict will be prepared for the values

        Args:
            ui_ltas (List[UILta]): List of UI LTAs
            ui_ltas_dict_key (Tuple[UILta]): Tuple of UI LTAs to be used
            as key for the dictionary

        Returns:
            str: pipe "|" seprated string of UI LTA's
        """
        if ui_ltas_dict_key not in self.otc_service_traveline_region:
            self.otc_service_traveline_region[
                ui_ltas_dict_key
            ] = get_service_traveline_regions(ui_ltas)
        return self.otc_service_traveline_region[ui_ltas_dict_key]

    def get_otc_ui_lta(
        self, ui_ltas: List[UILta], ui_ltas_dict_key: Tuple[UILta]
    ) -> str:
        """Return a pipe "|" seprate string of the UI LTA names for the service
        dictionary of the ui ltas will be maintained in order to minimize the
        manipulations

        Args:
            ui_ltas (List[UILta]): List of UI LTAs the service belongs to
            ui_ltas_dict_key (Tuple[UILta]): Tuple of UI LTAs to make key in dict

        Returns:
            str: Pipe "|" seprated list of UI LTAs
        """
        if ui_ltas_dict_key not in self.otc_service_ui_ltas:
            self.otc_service_ui_ltas[ui_ltas_dict_key] = ui_ltas_string(ui_ltas)
        return self.otc_service_ui_ltas[ui_ltas_dict_key]

    def get_is_english_region_otc(
        self,
        ui_ltas: List[UILta],
        ui_ltas_dict_key: Tuple[UILta],
        naptan_adminarea_df: pd.DataFrame,
    ) -> bool:
        """Find if the annotated key is_english_region for naptan admin area is True or False for
        any of the UI LTAs this service belongs to

        Args:
            ui_ltas (List[UILta]): List of UI LTAs the service belongs to
            ui_ltas_dict_key (Tuple[UILta]): Tuple value of UI LTAs for keys
            naptan_adminarea_df (pd.DataFrame): Dataframe for the admin area values

        Returns:
            bool: Returns True is the atco code passed belongs to an enlish region
        """
        if ui_ltas_dict_key not in self.otc_traveline_region_status:
            self.otc_traveline_region_status[
                ui_ltas_dict_key
            ] = not naptan_adminarea_df.empty and any(
                (
                    naptan_adminarea_df[
                        naptan_adminarea_df["ui_lta_id"].isin(
                            [ui_lta.id for ui_lta in ui_ltas]
                        )
                    ]
                )["is_english_region"]
            )
        return self.otc_traveline_region_status[ui_ltas_dict_key]

    def get_is_english_region_weca(
        self, atco_code: str, naptan_adminarea_df: pd.DataFrame
    ) -> bool:
        """Find if the annotated key is_english_region is True or False for
        The provided atco code
        For weca services if atco code belongs to an Naptan Admin area
        Such services will be considered in english region.

        Args:
            atco_code (str): Atco code to be checked
            naptan_adminarea_df (pd.DataFrame): Naptan admin areas list

        Returns:
            bool: Returns True is the atco code passed belongs to an enlish region
        """
        if atco_code not in self.weca_traveline_region_status:
            self.weca_traveline_region_status[
                atco_code
            ] = not naptan_adminarea_df.empty and any(
                (naptan_adminarea_df[naptan_adminarea_df["atco_code"] == atco_code])[
                    "is_english_region"
                ]
            )
        return self.weca_traveline_region_status[atco_code]

    def get_otc_service_bods_data(self, lta_list) -> None:
        """
        Compares an LTA's OTC and WECA Services dictionaries list with
        TXCFileAttributes dictionaries list and the SeasonalService list
        to determine which OTC and WECA Services require attention and which
        doesn't ie. not live in BODS at all, or live but meeting new
        Staleness conditions.
        """
        ui_lta = lta_list[0].ui_lta
        otc_map = get_line_level_otc_map_lta(lta_list)
        txcfa_map = get_line_level_txc_map_lta(lta_list)
        seasonal_service_map = get_seasonal_service_map(lta_list)
        service_code_exemption_map = get_service_code_exemption_map(lta_list)
        naptan_adminarea_df = get_all_naptan_atco_df()
        traveline_region_map_weca = get_weca_traveline_region_map(ui_lta)
        service_number_registration_number_map = set(otc_map)
        service_number_registration_number_map = sorted(
            service_number_registration_number_map
        )

        for (
            service_number,
            registration_number,
        ) in service_number_registration_number_map:
            service = otc_map.get((service_number, registration_number))
            file_attribute = txcfa_map.get((service_number, registration_number))
            seasonal_service = seasonal_service_map.get(registration_number)
            exemption = service_code_exemption_map.get(registration_number)

            if service.api_type in [API_TYPE_WECA, API_TYPE_EP]:
                is_english_region = self.get_is_english_region_weca(
                    service.atco_code, naptan_adminarea_df
                )
                ui_lta_name = ui_lta.name
                traveline_region = traveline_region_map_weca.get(service.atco_code, "")
            else:
                (
                    is_english_region,
                    ui_lta_name,
                    traveline_region,
                ) = self.get_otc_service_details(service, naptan_adminarea_df)

            exempted = False
            if not (
                not (exemption and exemption.registration_code) and is_english_region
            ):
                exempted = True

            staleness_status = "Up to date"
            if file_attribute is None:
                require_attention = self._get_require_attention(
                    exempted, seasonal_service
                )
            elif service and is_stale(service, file_attribute):
                rad = evaluate_staleness(service, file_attribute)
                staleness_status = STALENESS_STATUS[rad.index(True)]
                require_attention = self._get_require_attention(
                    exempted, seasonal_service
                )
            else:
                require_attention = "No"

            self._update_data(
                service,
                service_number,
                file_attribute,
                seasonal_service,
                exempted,
                staleness_status,
                require_attention,
                traveline_region,
                ui_lta_name,
            )

    def get_queryset(self):
        self.get_otc_service_bods_data(self._combined_authorities)
        return self._object_list
