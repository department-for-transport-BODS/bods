import io
import logging
import tempfile
import zipfile
from collections import namedtuple
from datetime import date, datetime
from typing import BinaryIO, Optional
from zipfile import ZIP_DEFLATED

from django.contrib.auth import get_user_model
from django.core.files.base import File
from django.db.models import Case, CharField, OuterRef, Q, Subquery, Value, When
from django.db.models.expressions import F
from django.db.models.functions import Concat

from transit_odp.avl.csv.catalogue import get_avl_data_catalogue_csv
from transit_odp.browse.exports import (
    LOCATION_FILENAME,
    ORGANISATION_FILENAME,
    OTC_EMPTY_WARNING,
    OVERALL_FILENAME,
    TIMETABLE_FILENAME,
    get_feed_status,
)
from transit_odp.common.csv import CSVBuilder, CSVColumn
from transit_odp.common.utils import (
    get_dataset_type_from_path_info,
    remove_query_string_param,
)
from transit_odp.feedback.models import Feedback, SatisfactionRating
from transit_odp.organisation.constants import EXPIRED, DatasetType
from transit_odp.organisation.csv import EmptyDataFrame
from transit_odp.organisation.csv.consumer_feedback import ConsumerFeedbackAdminCSV
from transit_odp.organisation.csv.organisation import get_organisation_catalogue_csv
from transit_odp.organisation.csv.overall import get_overall_data_catalogue_csv
from transit_odp.organisation.models import Dataset, ServiceCodeExemption
from transit_odp.site_admin.csv import (
    DAILY_AGGREGATES_FILENAME,
    DAILY_CONSUMER_FILENAME,
    get_consumer_breakdown_csv,
    get_daily_aggregates_csv,
)
from transit_odp.site_admin.models import APIRequest, MetricsArchive, OperationalStats
from transit_odp.timetables.csv import get_timetable_catalogue_csv
from transit_odp.users.constants import (
    AgentUserType,
    DeveloperType,
    OrgAdminType,
    OrgStaffType,
)
from transit_odp.users.models import Invitation

User = get_user_model()
CSVFile = namedtuple("CSVFile", "name, builder")
logger = logging.getLogger(__name__)


def pretty_account_name(account_type: Optional[int]) -> str:
    if account_type == OrgAdminType:
        return "Admin"
    elif account_type == OrgStaffType:
        return "Standard"
    elif account_type == AgentUserType:
        return "Agent"
    return "System"


def service_code_to_status(service_code: str) -> str:
    if service_code is None or service_code == "":
        return ""
    if service_code[:2] == "UZ":
        return "Unregistered"
    return "Registered"


def get_org_fares_count(org) -> int:
    if org.total_fare_products:
        return org.total_fare_products
    else:
        return 0


class ConsumerCSV(CSVBuilder):
    """A CSVBuilder class for creating Consumer CSV strings"""

    columns = [
        CSVColumn(header="Name", accessor=lambda u: u.get_full_name()),
        CSVColumn(header="Org Name", accessor="dev_organisation"),
        CSVColumn(header="Email", accessor="email"),
        CSVColumn(
            header="Status", accessor=lambda u: "Active" if u.is_active else "Inactive"
        ),
        CSVColumn(header="Last log-in", accessor="last_login"),
        CSVColumn(header="Notes", accessor="notes"),
    ]
    queryset = User.objects.filter(account_type=DeveloperType).order_by("pk")


class PublisherCSV(CSVBuilder):
    """A CSVBuilder class for creating Publisher CSV strings"""

    columns = [
        CSVColumn(header="Operator", accessor="publisher_organisation"),
        CSVColumn(header="Account type", accessor="pretty_account_name"),
        CSVColumn(header="Email", accessor="email"),
        CSVColumn(header="User Status", accessor="user_status"),
        CSVColumn(header="Key Contact", accessor="key_contact"),
    ]

    def get_queryset(self):
        # TODO include agent users with a record per agent user org
        when_is_inactive = When(
            Q(is_active=False), then=Value("Inactive", output_field=CharField())
        )
        when_is_active = When(
            Q(is_active=True), then=Value("Active", output_field=CharField())
        )
        when_key_contact = When(
            is_key_contact=True,
            then=Value("yes", output_field=CharField()),
        )

        user_subquery = Subquery(
            User.objects.filter(email=OuterRef("email"))
            .exclude(account_type=AgentUserType)
            .values_list("is_active")[:1]
        )
        return (
            Invitation.objects.select_related("organisation")
            .annotate(publisher_organisation=F("organisation__name"))
            .annotate(is_active=user_subquery)
            .annotate(
                user_status=Case(
                    when_is_inactive,
                    when_is_active,
                    default=Value("Pending", output_field=CharField()),
                    output_field=CharField(),
                )
            )
            .annotate(
                key_contact=Case(
                    when_key_contact,
                    default=Value("no", output_field=CharField()),
                    output_field=CharField(),
                )
            )
            .exclude(account_type=AgentUserType)
            .order_by("pk")
        )


class DatasetPublishingCSV(CSVBuilder):
    """A CSVBuilder class for creating Dataset Publisher CSV strings"""

    columns = [
        CSVColumn(header="operator", accessor="organisation_name"),
        CSVColumn(
            header="dataType",
            accessor=lambda dt: DatasetType(dt.dataset_type).name.title(),
        ),
        CSVColumn(header="dataID", accessor="id"),
        CSVColumn(header="status", accessor=get_feed_status),
        CSVColumn(header="lastPublished", accessor="published_at"),
        CSVColumn(header="email", accessor="last_published_by_email"),
        CSVColumn(
            header="accountType",
            accessor=lambda at: pretty_account_name(at.account_type),
        ),
    ]

    def get_queryset(self):
        return (
            Dataset.objects.get_published()
            .add_live_data()
            .add_organisation_name()
            .add_last_published_by_email()
            .annotate(account_type=F("live_revision__published_by__account_type"))
            .exclude(live_revision__status=EXPIRED)
        )


class OperationalStatsCSV(CSVBuilder):
    queryset = OperationalStats.objects.all().order_by("-date")
    columns = [
        CSVColumn(header="Date", accessor="date"),
        CSVColumn(
            header="Unique Registered Service Codes",
            accessor="registered_service_code_count",
        ),
        CSVColumn(
            header="Unique Unregistered Service Codes",
            accessor="unregistered_service_code_count",
        ),
        CSVColumn(header="Number of vehicles", accessor="vehicle_count"),
        CSVColumn(header="Registered Operators", accessor="operator_count"),
        CSVColumn(header="Registered Publishers Users", accessor="operator_user_count"),
        CSVColumn(header="Registered Agents Users", accessor="agent_user_count"),
        CSVColumn(header="Registered Consumers Users", accessor="consumer_count"),
        CSVColumn(header="Timetables datasets", accessor="timetables_count"),
        CSVColumn(
            header="Automatic Vehicle Locations (AVL) data feeds",
            accessor="avl_count",
        ),
        CSVColumn(header="Fares datasets", accessor="fares_count"),
        CSVColumn(
            header="Operators with at least one published timetables dataset",
            accessor="published_timetable_operator_count",
        ),
        CSVColumn(
            header="Operators with at least one published AVL data feed",
            accessor="published_avl_operator_count",
        ),
        CSVColumn(
            header="Operators with at least one published fares dataset",
            accessor="published_fares_operator_count",
        ),
    ]


class AgentUserCSV(CSVBuilder):
    columns = [
        CSVColumn(header="Operator", accessor=lambda n: n[0]),
        CSVColumn(header="Email", accessor=lambda n: n[1]),
        CSVColumn(header="Agent Organisation", accessor=lambda n: n[2]),
    ]

    def get_queryset(self):
        return User.objects.filter(account_type=AgentUserType).values_list(
            "organisations__name", "email", "agent_organisation"
        )


class WebsiteFeedbackCSV(CSVBuilder):
    columns = [
        CSVColumn(header="Date", accessor=lambda fb: fb.date.strftime("%d-%b-%y")),
        CSVColumn(
            header="Rating",
            accessor=lambda fb: SatisfactionRating(fb.satisfaction_rating).label,
        ),
        CSVColumn(header="Page URL", accessor="page_url"),
        CSVColumn(header="Comments", accessor="comment"),
    ]

    def get_queryset(self):
        return Feedback.objects.order_by("date")


class ServiceCodeExemptionsCSV(CSVBuilder):
    columns = [
        CSVColumn(
            header="Organisation", accessor=lambda exem: exem.licence.organisation.name
        ),
        CSVColumn(header="Licence Number", accessor=lambda exem: exem.licence.number),
        CSVColumn(header="Service Code", accessor="registration_number"),
        CSVColumn(header="Justification", accessor="justification"),
        CSVColumn(
            header="Date of exemption",
            accessor=lambda exem: exem.created.isoformat(sep=" "),
        ),
        CSVColumn(header="Exempted by", accessor=lambda exem: exem.exempted_by.email),
    ]

    def get_queryset(self):
        return (
            ServiceCodeExemption.objects.select_related(
                "licence__organisation", "exempted_by"
            )
            .add_registration_number()
            .order_by(
                "licence__organisation__name", "licence__number", "registration_code"
            )
        )


def create_operational_exports_file() -> BinaryIO:
    buffer_ = io.BytesIO()
    today = date.today().isoformat()
    files = (
        CSVFile("publishers.csv", PublisherCSV),
        CSVFile("consumers.csv", ConsumerCSV),
        CSVFile("stats.csv", OperationalStatsCSV),
        CSVFile("agents.csv", AgentUserCSV),
        CSVFile("datasetpublishing.csv", DatasetPublishingCSV),
        CSVFile("feedback_report_operator_breakdown.csv", ConsumerFeedbackAdminCSV),
        CSVFile("websiteFeedbackResponses.csv", WebsiteFeedbackCSV),
        CSVFile(
            f"{today}-Service codes exempt from BODS reporting.csv",
            ServiceCodeExemptionsCSV,
        ),
    )

    with zipfile.ZipFile(buffer_, mode="w", compression=ZIP_DEFLATED) as zin:
        for file_ in files:
            Builder = file_.builder
            zin.writestr(file_.name, Builder().to_string())

        prefix = "Pandas - to_csv - "
        logger.info(prefix + f"Generating {ORGANISATION_FILENAME}")
        try:
            zin.writestr(ORGANISATION_FILENAME, get_organisation_catalogue_csv())
        except EmptyDataFrame as exc:
            logger.warning(OTC_EMPTY_WARNING, exc_info=exc)

        logger.info(prefix + f"Generating {TIMETABLE_FILENAME}")
        try:
            zin.writestr(TIMETABLE_FILENAME, get_timetable_catalogue_csv())

        except EmptyDataFrame as exc:
            logger.warning(OTC_EMPTY_WARNING, exc_info=exc)

        logger.info(prefix + f"Generating {OVERALL_FILENAME}")
        try:
            zin.writestr(OVERALL_FILENAME, get_overall_data_catalogue_csv())
        except EmptyDataFrame:
            pass

        logger.info(prefix + f"Generating {LOCATION_FILENAME}")
        try:
            zin.writestr(LOCATION_FILENAME, get_avl_data_catalogue_csv())
        except EmptyDataFrame:
            pass

    buffer_.seek(0)
    return buffer_


class RawConsumerRequestCSV(CSVBuilder):
    columns = [
        CSVColumn(
            header="datatype",
            accessor=lambda r: get_dataset_type_from_path_info(r.path_info),
        ),
        CSVColumn(header="id", accessor="id"),
        CSVColumn(header="requestor", accessor="requestor_id"),
        CSVColumn(header="Consumer Name", accessor="requestor_full_name"),
        CSVColumn(header="Consumer Organisation", accessor="requestor_org"),
        CSVColumn(header="Consumer Email", accessor="email"),
        CSVColumn(header="path_info", accessor="path_info"),
        CSVColumn(
            header="query_string",
            accessor=lambda r: remove_query_string_param(r.query_string, "api_key"),
        ),
        CSVColumn(header="created", accessor="created"),
    ]

    def get_queryset(self):
        return (
            APIRequest.objects.select_related("requestor")
            .annotate(
                requestor_full_name=Concat(
                    F("requestor__first_name"),
                    Value(" ", output_field=CharField()),
                    F("requestor__last_name"),
                    output_field=CharField(),
                ),
                requestor_org=F("requestor__dev_organisation"),
                email=F("requestor__email"),
            )
            .order_by("id")
        )


class APIRequestArchive:
    def __init__(self, start: datetime, end: datetime):
        self.start = start
        self.end = end

    @property
    def filename(self):
        return f"api_requests_{self.start:%B_%Y}.zip"

    def zip_as_file(self, archive):
        with zipfile.ZipFile(archive, mode="w", compression=ZIP_DEFLATED) as zin:

            builder = RawConsumerRequestCSV()
            builder.queryset = builder.get_queryset().filter(
                created__range=(self.start, self.end)
            )

            csvfile = builder.to_temporary_file()
            zin.write(csvfile.name, "rawapimetrics.csv")
            csvfile.close()

            csvfile = get_consumer_breakdown_csv(self.start, self.end)
            zin.write(csvfile.name, DAILY_CONSUMER_FILENAME)
            csvfile.close()

            csvfile = get_daily_aggregates_csv(self.start, self.end)
            zin.write(csvfile.name, DAILY_AGGREGATES_FILENAME)
            csvfile.close()

        archive.seek(0)
        return File(archive, name=self.filename)


def create_metrics_archive(start, end):
    archive = APIRequestArchive(start=start, end=end)
    with tempfile.TemporaryFile() as tmpfile:
        defaults = {"end": end.date(), "archive": archive.zip_as_file(archive=tmpfile)}
        MetricsArchive.objects.update_or_create(start=start.date(), defaults=defaults)
