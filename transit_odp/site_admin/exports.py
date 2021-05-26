from django.contrib.auth import get_user_model
from django.db.models import Case, CharField, Count, Min, Value, When
from django.db.models.expressions import F
from django.db.models.functions import TruncDay

from transit_odp.common.csv import CSVBuilder, CSVColumn
from transit_odp.common.utils import remove_query_string_param
from transit_odp.organisation.models import Organisation
from transit_odp.site_admin.models import APIRequest, OperationalStats
from transit_odp.users.constants import (
    AgentUserType,
    DeveloperType,
    OrgAdminType,
    OrgStaffType,
)

User = get_user_model()


def org_status_str(org):
    """Get a pretty organisation status"""
    mapping = {"active": "Active", "inactive": "Inactive", "pending": "Pending invite"}
    return mapping.get(org.status, None)


class OrganisationCSV(CSVBuilder):
    """A CSVBuilder class for creating Organisation CSV strings"""

    columns = [
        CSVColumn(header="Name", accessor="name"),
        CSVColumn(header="Status", accessor=org_status_str),
        CSVColumn(header="Date Invited", accessor="invite_sent"),
        CSVColumn(header="Last log-in", accessor="last_active"),
    ]

    def get_queryset(self):
        return (
            Organisation.objects.all()
            .add_status()
            .add_last_active()
            .add_invite_sent()
            .order_by("pk")
        )


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
        CSVColumn(header="Organisation", accessor="publisher_organisation"),
        CSVColumn(header="Account Type", accessor="pretty_account_name"),
        CSVColumn(header="Email", accessor="email"),
        CSVColumn(header="Key contact", accessor="key_contact"),
    ]

    def get_queryset(self):
        # TODO include agent users with a record per agent user org
        org_users = [OrgAdminType, OrgStaffType]
        when_key_contact = When(
            key_organisation__isnull=False, then=Value("Key contact")
        )

        # using Min here to get the first organisation, this shouldn't
        # be an issue for an org user as they should only have one org.
        return (
            User.objects.filter(account_type__in=org_users)
            .prefetch_related("organisations")
            .annotate(publisher_organisation=Min("organisations__name"))
            .annotate(
                key_contact=Case(
                    when_key_contact, default=Value(""), output_field=CharField()
                )
            )
            .order_by("pk")
        )


class OperationalStatsCSV(CSVBuilder):
    queryset = OperationalStats.objects.all().order_by("-date")
    columns = [
        CSVColumn(header="Date", accessor="date"),
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
            header="Operators with atleast one published timetables dataset",
            accessor="published_timetable_operator_count",
        ),
        CSVColumn(
            header="Operators with atleast one published AVL datafeed",
            accessor="published_avl_operator_count",
        ),
        CSVColumn(
            header="Operators with atleast one published fares dataset",
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


class APIRequestCSV(CSVBuilder):
    """Generates a csv of aggregate APIRequest stats."""

    columns = [
        CSVColumn(header="Date", accessor=lambda r: r["day"].date().isoformat()),
        CSVColumn(
            header="Number of unique consumers",
            accessor=lambda r: r["unique_consumers"],
        ),
        CSVColumn(
            header="Number of API requests", accessor=lambda r: r["total_requests"]
        ),
    ]

    def get_queryset(self):
        return (
            APIRequest.objects.annotate(day=TruncDay("created"))
            .values("day")
            .annotate(
                total_requests=Count("id"),
                unique_consumers=Count("requestor_id", distinct=True),
            )
            .order_by()
        )


class DailyConsumerRequestCSV(CSVBuilder):
    """Generates a csv of daily API requests for a specific user."""

    columns = [
        CSVColumn(header="Date", accessor=lambda r: r["day"].date().isoformat()),
        CSVColumn(header="Consumer ID", accessor=lambda r: r["requestor_id"]),
        CSVColumn(header="Email", accessor=lambda r: r["requestor__email"]),
        CSVColumn(
            header="Number of daily API requests",
            accessor=lambda r: r["total_requests"],
        ),
    ]

    def get_queryset(self):
        return (
            APIRequest.objects.annotate(day=TruncDay("created"))
            .select_related("requestor")
            .values("day", "requestor_id", "requestor__email")
            .annotate(total_requests=Count("id"))
            .order_by("day", "requestor_id")
        )


class RawConsumerRequestCSV(CSVBuilder):
    columns = [
        CSVColumn(header="id", accessor="id"),
        CSVColumn(header="requestor", accessor="requestor_id"),
        CSVColumn(header="Consumer Name", accessor="requestor_name"),
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
                requestor_name=F("requestor__name"),
                requestor_org=F("requestor__dev_organisation"),
                email=F("requestor__email"),
            )
            .order_by("id")
        )
