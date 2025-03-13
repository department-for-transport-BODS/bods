import logging
import math
import re
from collections import namedtuple
from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd
import requests
from allauth.account.adapter import get_adapter
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Max
from django.http import FileResponse, Http404, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView
from django.views.generic.detail import BaseDetailView
from django_hosts import reverse
from requests import RequestException
from waffle import flag_is_active

import config.hosts
from transit_odp.avl.require_attention.abods.registery import AbodsRegistery
from transit_odp.avl.require_attention.weekly_ppc_zip_loader import (
    get_vehicle_activity_operatorref_linename,
)
from transit_odp.browse.cfn import generate_signed_url
from transit_odp.browse.constants import LICENCE_NUMBER_NOT_SUPPLIED_MESSAGE
from transit_odp.browse.filters import TimetableSearchFilter
from transit_odp.browse.forms import ConsumerFeedbackForm
from transit_odp.browse.tables import DatasetPaginatorTable
from transit_odp.browse.timetable_visualiser import TimetableVisualiser
from transit_odp.browse.user_feedback import UserFeedback
from transit_odp.browse.views.base_views import (
    BaseSearchView,
    BaseTemplateView,
    ChangeLogView,
)
from transit_odp.common.constants import FeatureFlags
from transit_odp.common.downloaders import GTFSFileDownloader
from transit_odp.common.forms import ConfirmationForm
from transit_odp.common.services import get_gtfs_bucket_service
from transit_odp.common.view_mixins import (
    BaseDownloadFileView,
    DownloadView,
    ResourceCounterMixin,
)
from transit_odp.data_quality.report_summary import Summary
from transit_odp.data_quality.scoring import get_data_quality_rag
from transit_odp.notifications import get_notifications
from transit_odp.organisation.constants import (
    ENGLISH_TRAVELINE_REGIONS,
    DatasetType,
    FeedStatus,
    TimetableType,
    TravelineRegions,
)
from transit_odp.organisation.csv.service_codes import STALENESS_STATUS
from transit_odp.organisation.models import (
    ConsumerFeedback,
    Dataset,
    DatasetRevision,
    DatasetSubscription,
    TXCFileAttributes,
)
from transit_odp.organisation.models.data import SeasonalService, ServiceCodeExemption
from transit_odp.otc.models import Service as OTCService
from transit_odp.pipelines.models import BulkDataArchive, ChangeDataArchive
from transit_odp.publish.requires_attention import (
    FaresRequiresAttention,
    evaluate_staleness,
    get_dq_critical_observation_services_map,
    get_fares_dataset_map,
    get_line_level_txc_map_service_base,
    is_avl_requires_attention,
    is_stale,
)
from transit_odp.site_admin.models import ResourceRequestCounter
from transit_odp.timetables.tables import TimetableChangelogTable
from transit_odp.transmodel.models import BookingArrangements, Service
from transit_odp.users.constants import SiteAdminType

logger = logging.getLogger(__name__)
User = get_user_model()
Regions = namedtuple("Regions", ("region_code", "pretty_name_region_code", "exists"))


class DatasetDetailView(DetailView):
    template_name = "browse/timetables/dataset_detail/index.html"
    model = Dataset

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .get_active_org()
            .get_dataset_type(dataset_type=TimetableType)
            .get_published()
            .get_viewable_statuses()
            .add_admin_area_names()
            .add_live_data()
            .add_nocs()
            .select_related("live_revision")
        )

    def get_distinct_dataset_txc_attributes(self, revision_id):
        txc_attributes = {}
        txc_file_attributes = TXCFileAttributes.objects.filter(revision_id=revision_id)

        for file_attribute in txc_file_attributes:
            licence_number = (
                file_attribute.licence_number
                and file_attribute.licence_number.strip()
                or LICENCE_NUMBER_NOT_SUPPLIED_MESSAGE
            )

            noc_dict = txc_attributes.setdefault(licence_number, {}).setdefault(
                file_attribute.national_operator_code, {}
            )
            for line_name in file_attribute.line_names:
                line_names_dict = noc_dict.setdefault(line_name, set())
                line_names_dict.add(file_attribute.service_code)

        return txc_attributes

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)

        dataset = self.object
        live_revision = dataset.live_revision
        report = live_revision.report.order_by("-created").first()
        dqs_report = live_revision.dqs_report.order_by("-created").first()
        if dqs_report:
            summary = Summary.get_report(dqs_report.id, live_revision.id)
            kwargs["report_id"] = getattr(dqs_report, "id", None)
            kwargs["dq_score"] = None
            kwargs["new_dqs_report"] = True
            kwargs["is_new_data_quality_service_active"] = True
        else:
            summary = getattr(report, "summary", None)
            kwargs["report_id"] = getattr(report, "id", None)
            kwargs["dq_score"] = (
                get_data_quality_rag(report) if report and summary else None
            )
            kwargs["new_dqs_report"] = False
            kwargs["is_new_data_quality_service_active"] = False

        kwargs["summary"] = summary
        kwargs["is_specific_feedback"] = flag_is_active("", "is_specific_feedback")
        user = self.request.user

        kwargs["pk"] = dataset.id
        kwargs["api_root"] = reverse("api:app:api-root", host=config.hosts.DATA_HOST)
        kwargs["admin_areas"] = self.object.admin_area_names
        # Once all the reports are generated we should probably use the queryset
        # annotation get_live_dq_score and calculate the rag from that.

        # Handle errors produced by pipeline
        task = live_revision.etl_results.latest()
        error_code = task.error_code
        kwargs["error"] = bool(error_code)
        kwargs["show_pti"] = (
            live_revision.created.date() >= settings.PTI_START_DATE.date()
        )
        kwargs["pti_enforced_date"] = settings.PTI_ENFORCED_DATE

        is_subscribed = None
        feed_api = None

        if user.is_authenticated:
            is_subscribed = DatasetSubscription.objects.filter(
                dataset=dataset, user=user
            ).exists()
            feed_api = reverse(
                "api:feed-detail", args=[self.object.id], host=config.hosts.DATA_HOST
            )
            feed_api = f"{feed_api}?api_key={user.auth_token}"

        kwargs.update({"notification": is_subscribed, "feed_api": feed_api})
        kwargs["distinct_attributes"] = self.get_distinct_dataset_txc_attributes(
            live_revision.id
        )

        return kwargs


class LineMetadataDetailView(DetailView):
    template_name = "browse/timetables/dataset_detail/review_line_metadata.html"
    model = Dataset

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .get_active_org()
            .get_dataset_type(dataset_type=TimetableType)
            .get_published()
            .get_viewable_statuses()
            .add_admin_area_names()
            .add_live_data()
            .add_nocs()
            .select_related("live_revision")
        )

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
        total_page = math.ceil((total_columns_count - 1) / 10)
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

        txc_map = dict(enumerate(txc_file_attributes))
        fares_df = get_fares_dataset_map(txc_map)

        fra = FaresRequiresAttention(None)
        is_fares_compliant = True
        logger.info("Running the fares compliant check")
        for txc_file in txc_file_attributes:
            logger.info("Got fares require attention")
            logger.info(fra.is_fares_requires_attention(txc_file, fares_df))
            if is_fares_compliant:
                is_fares_compliant = not fra.is_fares_requires_attention(
                    txc_file, fares_df
                )
            else:
                break

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
                logger.info("Timetable is compliant")
                is_timetable_compliant = True
            else:
                logger.info("Timetable is not compliant")
                logger.info(txc_file)
                logger.info(len(len(dqs_critical_issues_service_line_map)))
                logger.info(evaluate_staleness(self.service, txc_file))
                logger.info(is_stale(self.service, txc_file))
        else:
            logger.info("Either service or txc file missing")

        return {
            "is_timetable_compliant": is_timetable_compliant,
            "timetables_dataset_id": dataset_id,
            "timetables_valid_files": current_valid_files,
            "timetables_future_dated_files": future_files,
            "timetables_expired_files": expired_files,
        }

    def get_otc_service(self):
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
            }
        return {
            "curr_date": date,
            "timetable": timetable,
            "is_timetable_info_available": is_timetable_info_available,
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

    def get_context_data(self, **kwargs):
        """
        Get the context data for the view.

        This method retrieves various contextual data based on the request parameters
        and the object's attributes.
        """
        line = self.request.GET.get("line")
        service_code = self.request.GET.get("service")

        self.line = line
        self.service_code = service_code
        self.service = self.get_otc_service()
        licence_number = None
        self.service_code_exemption_map = {}
        self.seasonal_service_map = {}
        self.service_inscope = True
        if self.service:
            licence_number = self.service.licence.number
            self.service_code_exemption_map = self.get_service_code_exemption_map(
                licence_number
            )
            self.seasonal_service_map = self.get_seasonal_service_map(licence_number)
            self.service_inscope = self.is_service_in_scope()

        kwargs = super().get_context_data(**kwargs)
        dataset = self.object
        if dataset:
            live_revision = dataset.live_revision
        else:
            live_revision = None
        kwargs["pk"] = dataset.id if dataset else None
        kwargs["service_inscope"] = self.service_inscope

        kwargs["line_name"] = line
        kwargs["service_code"] = service_code

        kwargs["is_specific_feedback"] = flag_is_active("", "is_specific_feedback")
        kwargs["api_root"] = reverse("api:app:api-root", host=config.hosts.DATA_HOST)
        # Get the flag is_timetable_visualiser_active state
        is_timetable_visualiser_active = flag_is_active(
            "", "is_timetable_visualiser_active"
        )
        kwargs["is_timetable_visualiser_active"] = is_timetable_visualiser_active
        kwargs["is_complete_service_pages_active"] = flag_is_active(
            "", FeatureFlags.COMPLETE_SERVICE_PAGES.value
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

            txc_file_attributes = (
                self.get_timetable_files_for_line(live_revision.id, service_code, line)
                .add_service_code(service_code)
                .add_split_linenames()
            )

            if FeatureFlags.COMPLETE_SERVICE_PAGES:
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

    def is_service_in_scope(self) -> bool:
        """check is service is in scope or not system will
        check 3 points to decide in scope Service Exception,
        Seasonal Service Status and Traveling region

        Returns:
            bool: True if in scope else False
        """
        seasonal_service = self.seasonal_service_map.get(
            self.service.registration_number
        )
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

        if not (
            not (exemption and exemption.registration_code) and is_english_region
        ) or (seasonal_service and not seasonal_service.seasonal_status):
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
                licence__organisation__licences__number__in=licence_number
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


class DatasetSubscriptionBaseView(LoginRequiredMixin):
    model = Dataset

    def handle_no_permission(self):
        self.object = self.get_object()
        return render(
            self.request,
            "browse/timetables/feed_subscription_gatekeeper.html",
            context={"object": self.object, "backlink_url": self.get_cancel_url()},
        )

    def get_is_subscribed(self):
        # TODO - memoize
        user = self.request.user
        return user.subscriptions.filter(id=self.object.id).exists()


class DatasetSubscriptionView(DatasetSubscriptionBaseView, UpdateView):
    template_name = "browse/timetables/feed_subscription.html"
    form_class = ConfirmationForm

    def get_queryset(self):
        # Only allow users to subscribe to Datasets which are published
        return (
            super()
            .get_queryset()
            .get_active_org()
            .get_dataset_type(dataset_type=DatasetType.TIMETABLE.value)
            .get_published()
            .add_live_data()
        )

    def get_cancel_url(self):
        # Send user to feed-detail if can't get HTTP_REFERER
        # (more likely to have come from feed-detail because users
        # can only subscribe from that page)
        return self.request.headers.get(
            "Referer",
            reverse("feed-detail", args=[self.object.id], host=self.request.host.name),
        )

    def stash_data(self):
        adapter = get_adapter(self.request)
        adapter.stash_back_url(self.request, self.get_cancel_url())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # pop model instance as form is not a ModelForm
        kwargs.pop("instance", None)
        kwargs.update({"cancel_url": self.get_cancel_url()})
        return kwargs

    def get_form_url(self):
        return reverse(
            "feed-subscription",
            args=[self.object.id],
            host=config.hosts.DATA_HOST,
        )

    def get_context_data(self, **kwargs):
        # the success page needs access to the user's origin url. Can't stash
        # in form_valid because at that point the
        # HTTP_REFERER is the current page
        self.stash_data()
        # set is_subscribed before calling super().get_context_data
        # so that it is available in subsequent call to get_form_kwargs
        self.is_subscribed = self.get_is_subscribed()

        context = super().get_context_data(**kwargs)
        context["is_subscribed"] = self.is_subscribed
        context["backlink_url"] = self.get_cancel_url()
        context["form_url"] = self.get_form_url()
        return context

    def form_valid(self, form):
        user = self.request.user
        is_subscribed = self.get_is_subscribed()

        # Toggle subscription
        if is_subscribed:
            DatasetSubscription.objects.filter(dataset=self.object, user=user).delete()
        else:
            DatasetSubscription.objects.create(user=user, dataset=self.object)

        success_url = reverse(
            "feed-subscription-success",
            args=[self.object.id],
            host=config.hosts.DATA_HOST,
        )
        return redirect(success_url)


class DatasetSubscriptionSuccessView(
    DatasetPaginatorTable, DatasetSubscriptionBaseView, DetailView
):
    template_name = "browse/timetables/feed_subscription_success.html"

    def get_queryset(self):
        # Only allow users to subscribe to Datasets which are published
        return (
            super()
            .get_queryset()
            .get_active_org()
            .get_dataset_type(dataset_type=DatasetType.TIMETABLE.value)
            .get_published()
            .add_live_data()
        )

    def get_back_url(self):
        adapter = get_adapter(self.request)
        if adapter.stash_contains_back_url(self.request):
            return adapter.unstash_back_url(self.request)
        else:
            # Send user to feed-detail if can't retrieve URL (more likely to
            # have come from feed-detail because users
            # can only subscribe from that page)
            return reverse(
                "feed-detail", args=[self.object.id], host=self.request.host.name
            )

    def get_back_button_text(self, previous_url):
        sub_manage_url = reverse("users:feeds-manage", host=config.hosts.DATA_HOST)
        if sub_manage_url in previous_url:
            return _("Go back to manage subscriptions")
        else:
            return _("Go back to data set")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        back_url = self._get_or_update_url(self.request.user, self.get_back_url())
        context.update(
            {
                "subscribe": self.get_is_subscribed(),
                "back_url": back_url,
                "back_button_text": self.get_back_button_text(back_url),
            }
        )
        return context


class DatasetChangeLogView(ChangeLogView):
    template_name = "browse/timetables/feed_change_log.html"
    table_class = TimetableChangelogTable
    dataset_type = DatasetType.TIMETABLE.value


class SearchView(BaseSearchView):
    template_name = "browse/timetables/search.html"
    model = Dataset
    paginate_by = 10
    filterset_class = TimetableSearchFilter
    strict = False

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .get_dataset_type(dataset_type=TimetableType)
            .get_published()
            .get_active_org()
            .get_viewable_statuses()
            .add_organisation_name()
            .add_live_data()
            .add_admin_area_names()
            .order_by(*self.get_ordering())
        )

        keywords = self.request.GET.get("q", "").strip()
        if keywords:
            qs = qs.search(keywords)
        return qs


def _get_gtfs_regions():
    try:
        response = requests.get(
            url=f"{settings.GTFS_API_BASE_URL}/gtfs/regions",
            timeout=180,
        )
        elapsed_time = response.elapsed.total_seconds()
        logger.info(
            f"Request to get GTFS regions took {elapsed_time}s "
            f"- status {response.status_code}"
        )

        return response.json()

    except RequestException:
        return None


def _get_gtfs_file(region):
    try:
        response = requests.get(
            url=f"{settings.GTFS_API_BASE_URL}/gtfs?regionName={region}",
            timeout=180,
            stream=True,
        )
        elapsed_time = response.elapsed.total_seconds()
        logger.info(
            f"Request to get GTFS data took {elapsed_time}s "
            f"- status {response.status_code}"
        )

        return response.raw

    except RequestException:
        return None


class DownloadTimetablesView(LoginRequiredMixin, BaseTemplateView):
    template_name = "browse/timetables/download_timetables.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        bulk_timetable = BulkDataArchive.objects.filter(dataset_type=TimetableType)
        context["show_bulk_archive_url"] = bulk_timetable.filter(
            compliant_archive=False
        ).exists()
        list_traveline_regions = []
        for region_code, pretty_name_region_code in TravelineRegions.choices:
            list_traveline_regions.append(
                Regions(
                    region_code,
                    pretty_name_region_code,
                    bulk_timetable.filter(traveline_regions=region_code).exists(),
                )
            )

        context["show_bulk_traveline_regions"] = list_traveline_regions

        # Get the change archives from the last 7 days. There should be at most one per
        # day, but use LIMIT 7 anyway
        last_week = timezone.now() - timedelta(days=7)
        change_archives = ChangeDataArchive.objects.filter(published_at__gte=last_week)[
            :7
        ]
        context["change_archives"] = change_archives

        is_new_gtfs_api_active = flag_is_active("", "is_new_gtfs_api_active")

        if is_new_gtfs_api_active:
            context["gtfs_regions"] = _get_gtfs_regions()
            context["is_new_gtfs_api_active"] = True
        else:
            downloader = GTFSFileDownloader(get_gtfs_bucket_service)
            context["gtfs_static_files"] = downloader.get_files()
            context["is_new_gtfs_api_active"] = False

        return context


class DownloadRegionalGTFSFileView(BaseDownloadFileView):
    """View for retrieving a GTFS region file from the GTFS API and
    returning it as a StreamingHttpResponse"""

    def get(self, request, *args, **kwargs):
        self.is_new_gtfs_api_active = flag_is_active("", "is_new_gtfs_api_active")
        if self.kwargs.get("id") == TravelineRegions.ALL.lower():
            db_starttime = datetime.now()
            ResourceRequestCounter.from_request(request)
            db_endtime = datetime.now()
            logger.info(
                f"""Database call for GTFS ResourceRequestCounter took
                {(db_endtime - db_starttime).total_seconds()} seconds"""
            )
        return self.render_to_response()

    def render_to_response(self):
        id_ = self.kwargs.get("id", None)

        if self.is_new_gtfs_api_active:
            gtfs_region_file = self.get_download_file()
            if gtfs_region_file is None:
                raise Http404
            response = StreamingHttpResponse(
                gtfs_region_file, content_type="application/zip"
            )
            response[
                "Content-Disposition"
            ] = f'attachment; filename="itm_{id_}_gtfs.zip"'
        else:
            gtfs = self.get_download_file(id_)
            if gtfs.file is None:
                raise Http404
            response = FileResponse(
                gtfs.file, filename=gtfs.filename, as_attachment=True
            )

        return response

    def get_download_file(self, id_=None):
        if self.is_new_gtfs_api_active:
            id_ = self.kwargs.get("id", None)
            gtfs_file = _get_gtfs_file(id_)
        else:
            s3_start = datetime.now()
            downloader = GTFSFileDownloader(get_gtfs_bucket_service)
            gtfs_file = downloader.download_file_by_id(id_)
            s3_endtime = datetime.now()
            logger.info(
                f"""S3 bucket download for GTFS took
                {(s3_endtime - s3_start).total_seconds()} seconds"""
            )

        return gtfs_file


class DownloadBulkDataArchiveView(ResourceCounterMixin, DownloadView):
    def get_object(self, queryset=None):
        db_starttime = datetime.now()
        try:
            bulk_data_archive = BulkDataArchive.objects.filter(
                dataset_type=TimetableType,
                compliant_archive=False,
                traveline_regions="All",
            ).earliest()  # as objects are already ordered by '-created' in model Meta
            db_endtime = datetime.now()
            logger.info(
                f"""Database call for bulk archive took
                {(db_endtime - db_starttime).total_seconds()} seconds"""
            )
            return bulk_data_archive
        except BulkDataArchive.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": BulkDataArchive._meta.verbose_name}
            )

    def get_download_file(self):
        is_direct_s3_url_active = flag_is_active("", "is_direct_s3_url_active")
        if is_direct_s3_url_active:
            return generate_signed_url(self.object.data.name)
        s3_start = datetime.now()
        data = self.object.data
        s3_endtime = datetime.now()
        logger.info(
            f"""S3 bucket download for bulk archive took
            {(s3_endtime - s3_start).total_seconds()} seconds"""
        )
        return data

    def render_to_response(self, **response_kwargs):
        is_direct_s3_url_active = flag_is_active("", "is_direct_s3_url_active")
        if is_direct_s3_url_active:
            download_file = self.get_download_file()
            return redirect(download_file)
        super().render_to_response(**response_kwargs)


class CFNDownloadBulkDataArchiveView(DownloadBulkDataArchiveView):
    def get_download_file(self):
        return generate_signed_url(self.object.data.name)

    def render_to_response(self, **response_kwargs):
        download_file = self.get_download_file()
        return redirect(download_file)


class DownloadBulkDataArchiveRegionsView(DownloadView):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object(kwargs["region_code"])
        return self.render_to_response()

    def get_object(self, region_code: str = "All"):
        db_starttime = datetime.now()
        try:
            region_bulk_data_archive = BulkDataArchive.objects.filter(
                dataset_type=TimetableType,
                compliant_archive=False,
                traveline_regions=region_code,
            ).earliest()  # as objects are already ordered by '-created' in model Meta
            db_endtime = datetime.now()
            logger.info(
                f"""Database call for region-wise bulk archive
                took {(db_endtime - db_starttime).total_seconds()} seconds"""
            )
            return region_bulk_data_archive
        except BulkDataArchive.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": BulkDataArchive._meta.verbose_name}
            )

    def get_download_file(self, *args):
        s3_start = datetime.now()
        data = self.object.data
        s3_endtime = datetime.now()
        logger.info(
            f"""S3 bucket download for region-wise bulk archive took
            {(s3_endtime - s3_start).total_seconds()} seconds"""
        )
        return data


class DownloadCompliantBulkDataArchiveView(DownloadView):
    def get_object(self, queryset=None):
        try:
            return (
                BulkDataArchive.objects.filter(
                    dataset_type=TimetableType, compliant_archive=True
                )
                .order_by("-created")
                .first()
            )
        except BulkDataArchive.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": BulkDataArchive._meta.verbose_name}
            )

    def get_download_file(self):
        return self.object.data


class DownloadChangeDataArchiveView(DownloadView):
    slug_url_kwarg = "published_at"
    slug_field = "published_at"
    model = ChangeDataArchive

    def setup(self, request, *args, **kwargs):
        """Initialize attributes shared by all view methods."""
        published_at = kwargs.pop("published_at")

        try:
            # Try to parse published_at into a date object
            published_at = datetime.strptime(published_at, "%Y-%m-%d").date()
        except ValueError as e:
            raise Http404 from e

        super().setup(request, *args, published_at=published_at, **kwargs)

    def get_queryset(self):
        # Get the change archives from the last 7 days.
        last_week = timezone.now() - timedelta(days=7)
        return ChangeDataArchive.objects.filter(published_at__gte=last_week)

    def get_download_file(self):
        return self.object.data


class DatasetDownloadView(ResourceCounterMixin, BaseDetailView):
    dataset_type = DatasetType.TIMETABLE.value

    def get_queryset(self):
        if self.request.GET.get("is_review", None) == "true":
            return Dataset.objects.get_active_org()
        else:
            return (
                Dataset.objects.get_active_org()
                .get_dataset_type(dataset_type=self.dataset_type)
                .get_published()
                .select_related("live_revision")
            )

    def render_to_response(self, context, **response_kwargs):
        dataset = self.object
        if dataset:
            if self.request.GET.get("is_review", None) == "true":
                revision = dataset.revisions.latest()
            else:
                revision = dataset.live_revision

            if (
                self.request.GET.get("get_working", None) == "true"
                and revision.status == FeedStatus.error.value
            ):
                # get previous working revision
                revision = dataset.revisions.filter(
                    status=FeedStatus.live.value
                ).latest()

            if revision:
                return FileResponse(revision.upload_file.open("rb"), as_attachment=True)
            else:
                raise Http404(
                    _("No %(verbose_name)s found matching the query")
                    % {"verbose_name": DatasetRevision._meta.verbose_name}
                )


class UserFeedbackView(LoginRequiredMixin, CreateView):
    template_name = "browse/timetables/user_feedback.html"
    form_class = ConsumerFeedbackForm
    model = ConsumerFeedback
    dataset = None

    def get(self, request, *args, **kwargs):
        self.dataset = get_object_or_404(
            Dataset.objects.select_related("live_revision", "organisation"),
            id=self.kwargs.get("pk"),
        )
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.dataset = get_object_or_404(
            Dataset.objects.select_related("live_revision"), id=self.kwargs.get("pk")
        )
        return super().post(request, *args, **kwargs)

    def get_feedback_details(self) -> dict:
        """
        Get the details from the request query params and DB
        """

        live_revision = self.dataset.live_revision
        revision_id = live_revision.id

        service_name = self.request.GET.get("service", None)
        line_name = self.request.GET.get("line", None)
        journey_code = self.request.GET.get("journey_code", None)
        stop = self.request.GET.get("stop", None)
        direction = self.request.GET.get("direction", None)
        atco_code = self.request.GET.get("atco_code", None)

        user_feedback = UserFeedback(
            revision_id,
            service_name,
            line_name,
            stop,
            direction,
            atco_code,
            journey_code,
        )
        # If service name is not found in query string of url
        if not service_name:
            return user_feedback.default()
        else:
            if journey_code or stop:
                # If vehicle journey code is available
                if journey_code:
                    qs = user_feedback.get_qs_journey_code()
                # Check whether the stop info is there
                if stop:
                    qs = user_feedback.get_qs_stop()
            else:
                qs = user_feedback.get_qs_service()

            if qs:
                return user_feedback.data(qs)
            else:
                return user_feedback.default()

    def get_initial(self):
        initial_data = {
            "dataset_id": self.dataset.id,
            "organisation_id": self.dataset.organisation.id,
            "consumer_id": self.request.user.id,
        }
        data: dict = self.get_feedback_details()

        initial_data["service_id"] = data["service_id"]
        initial_data["vehicle_journey_id"] = data["vehicle_journey_id"]
        initial_data["revision_id"] = data["revision_id"]
        initial_data["service_pattern_stop_id"] = data["service_pattern_stop_id"]
        initial_data["service_pattern_id"] = data["service_pattern_id"]

        return initial_data

    @transaction.atomic
    def form_valid(self, form):
        client = get_notifications()
        response = super().form_valid(form)
        admins = User.objects.filter(account_type=SiteAdminType)
        emails = [email["email"] for email in admins.values()]
        emails.append(self.request.user.email)

        for email in emails:
            client.send_dataset_feedback_consumer_copy(
                dataset_id=self.dataset.id,
                contact_email=email,
                dataset_name=self.dataset.live_revision.name,
                publisher_name=self.dataset.organisation.name,
                feedback=self.object.feedback,
                time_now=None,
            )

        client.send_feedback_notification(
            dataset_id=self.dataset.id,
            contact_email=self.dataset.contact.email,
            dataset_name=self.dataset.live_revision.name,
            feedback=self.object.feedback,
            feed_detail_link=self.dataset.feed_detail_url,
            developer_email=self.request.user.email if self.object.consumer else None,
        )

        return response

    def get_success_url(self):
        service_name = self.request.GET.get("service", None)
        line_name = self.request.GET.get("line", None)

        success_url = reverse(
            "feed-feedback-success",
            args=[self.dataset.id],
            host=config.hosts.DATA_HOST,
        )
        if service_name and line_name:
            success_url += f"?line={line_name}&service={service_name}"
        return success_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        back_url = reverse(
            "feed-detail",
            args=[self.dataset.id],
            host=config.hosts.DATA_HOST,
        )
        context["dataset"] = self.dataset

        data: dict = self.get_feedback_details()
        context["revision_id"] = data["revision_id"]
        # If service code and line are found in DB
        if data["service_id"]:
            context["service"] = data["service_name"]
            context["line_name"] = data["line_name"]
            back_url = reverse(
                "feed-line-detail",
                args=[self.dataset.id],
                host=config.hosts.DATA_HOST,
            )
            back_url += f"?line={data['line_name']}&service={data['service_name']}"
        # If vehicle journey details are found in DB
        if data["vehicle_journey_id"]:
            context["journey_start_time"] = data["start_time"]
            context["direction"] = data["direction"]
        # If stop details are found in DB
        if data["service_pattern_stop_id"]:
            context["stop_name"] = data["stop_name"]
            context["atco_code"] = data["atco_code"]
        context["back_url"] = back_url

        return context


class UserFeedbackSuccessView(LoginRequiredMixin, TemplateView):
    template_name = "browse/timetables/user_feedback_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        object_id = self.kwargs["pk"]
        url = reverse("feed-line-detail", args=[object_id], host=config.hosts.DATA_HOST)

        service_name = self.request.GET.get("service", None)
        line_name = self.request.GET.get("line", None)

        if service_name and line_name:
            url += f"?line={line_name}&service={service_name}"
        context["back_link"] = url
        return context
