import csv
import io
from datetime import timedelta

import pytest
from django.utils import timezone

from transit_odp.common.utils.cast import to_int_or_value
from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.site_admin.exports import (
    AgentUserCSV,
    APIRequestCSV,
    ConsumerCSV,
    DailyConsumerRequestCSV,
    OperationalStatsCSV,
    OrganisationCSV,
    PublisherCSV,
    RawConsumerRequestCSV,
)
from transit_odp.site_admin.factories import APIRequestFactory, OperationalStatsFactory
from transit_odp.users.constants import (
    AgentUserType,
    DeveloperType,
    OrgAdminType,
    OrgStaffType,
    SiteAdminType,
)
from transit_odp.users.factories import InvitationFactory, UserFactory

pytestmark = pytest.mark.django_db


class TestOrganisationCSV:
    def test_active_organisation_to_string(self, user_factory):
        now = timezone.now()
        org = OrganisationFactory.create()
        UserFactory.create(
            organisations=(org,), account_type=OrgAdminType, last_login=now
        )

        org_csv = OrganisationCSV()
        actual = org_csv.to_string()
        csvfile = io.StringIO(actual)
        reader = csv.reader(csvfile.getvalue().splitlines())
        headers, first_row = list(reader)

        assert headers == ["Name", "Status", "Date Invited", "Last log-in"]
        assert first_row == [org.name, "Active", "", now.isoformat()]

    def test_inactive_organisation_to_string(self, user_factory):
        now = timezone.now()
        org = OrganisationFactory.create(is_active=False)
        UserFactory.create(
            organisations=(org,), account_type=OrgAdminType, last_login=now
        )

        org_csv = OrganisationCSV()
        actual = org_csv.to_string()
        csvfile = io.StringIO(actual)
        reader = csv.reader(csvfile.getvalue().splitlines())
        headers, first_row = list(reader)

        assert headers == ["Name", "Status", "Date Invited", "Last log-in"]
        assert first_row == [org.name, "Inactive", "", now.isoformat()]

    def test_pending_organisation_to_string(self, user_factory):
        site_admin = UserFactory.create(account_type=SiteAdminType)
        invitation = InvitationFactory.create(
            account_type=OrgAdminType, inviter=site_admin
        )
        org = invitation.organisation
        org.is_active = False
        org.save()

        org_csv = OrganisationCSV()
        actual = org_csv.to_string()
        csvfile = io.StringIO(actual)
        reader = csv.reader(csvfile.getvalue().splitlines())
        headers, first_row = list(reader)

        assert headers == ["Name", "Status", "Date Invited", "Last log-in"]
        assert first_row == [
            org.name,
            "Pending invite",
            invitation.sent.isoformat(),
            "",
        ]


class TestPublisherCSV:
    def test_active_publisher_to_string(self):
        now = timezone.now()
        org = OrganisationFactory.create()
        user = UserFactory.create(
            organisations=(org,), account_type=OrgAdminType, last_login=now
        )
        org.key_contact = user
        org.save()
        standard_user = UserFactory.create(
            organisations=(org,), account_type=OrgStaffType
        )

        publisher_csv = PublisherCSV()
        actual = publisher_csv.to_string()
        csvfile = io.StringIO(actual)
        reader = csv.reader(csvfile.getvalue().splitlines())
        headers, first_row, second_row = list(reader)

        assert headers == ["Organisation", "Account Type", "Email", "Key contact"]
        assert first_row == [org.name, "Admin", user.email, "Key contact"]
        assert second_row == [org.name, "Standard", standard_user.email, ""]


class TestConsumerCSV:
    def test_consumers_to_string(self):
        now = timezone.now()
        user = UserFactory.create(
            account_type=DeveloperType, last_login=now, notes="A note"
        )

        consumer_csv = ConsumerCSV()
        actual = consumer_csv.to_string()
        csvfile = io.StringIO(actual)
        reader = csv.reader(csvfile.getvalue().splitlines())
        headers, first_row = list(reader)

        assert headers == [
            "Name",
            "Org Name",
            "Email",
            "Status",
            "Last log-in",
            "Notes",
        ]
        assert first_row == [
            user.first_name + " " + user.last_name,
            user.dev_organisation,
            user.email,
            "Active",
            user.last_login.isoformat(),
            user.notes,
        ]


class TestOperationalStatsCSV:
    def test_operational_stats_to_string(self):
        stats = OperationalStatsFactory()

        actual = OperationalStatsCSV().to_string()
        csvfile = io.StringIO(actual)
        reader = csv.reader(csvfile.getvalue().splitlines())
        headers, first_row = list(reader)
        first_row = [to_int_or_value(v) for v in first_row]

        expected_headers = [
            "Date",
            "Registered Operators",
            "Registered Publishers Users",
            "Registered Agents Users",
            "Registered Consumers Users",
            "Timetables datasets",
            "Automatic Vehicle Locations (AVL) data feeds",
            "Fares datasets",
            "Operators with atleast one published timetables dataset",
            "Operators with atleast one published AVL datafeed",
            "Operators with atleast one published fares dataset",
        ]
        expected_first_row = [
            stats.date.date().isoformat(),
            stats.operator_count,
            stats.operator_user_count,
            stats.agent_user_count,
            stats.consumer_count,
            stats.timetables_count,
            stats.avl_count,
            stats.fares_count,
            stats.published_timetable_operator_count,
            stats.published_avl_operator_count,
            stats.published_fares_operator_count,
        ]
        assert expected_headers == headers
        assert expected_first_row == first_row


class TestAgentUserCSV:
    def test_active_publisher_to_string(self):
        now = timezone.now()
        org1, org2 = [OrganisationFactory.create() for _ in range(2)]
        user = UserFactory.create(
            organisations=(org1, org2), account_type=AgentUserType, last_login=now
        )

        agent_csv = AgentUserCSV()
        actual = agent_csv.to_string()
        csvfile = io.StringIO(actual)
        reader = csv.reader(csvfile.getvalue().splitlines())
        headers, first_row, second_row = list(reader)

        assert headers == ["Operator", "Email", "Agent Organisation"]
        assert first_row == [org1.name, user.email, user.agent_organisation]
        assert second_row == [org2.name, user.email, user.agent_organisation]


class TestAPIRequestCSV:
    def get_csv_rows(self):
        actual = APIRequestCSV().to_string()
        csvfile = io.StringIO(actual)
        reader = csv.reader(csvfile.getvalue().splitlines())
        rows = list(reader)
        return rows

    def test_no_api_requests_to_string(self):
        expected_headers = [
            "Date",
            "Number of unique consumers",
            "Number of API requests",
        ]
        rows = self.get_csv_rows()
        headers, *_ = rows
        assert len(rows) == 1
        assert expected_headers == headers

    def test_requests_from_multiple_users(self):
        consumer1 = UserFactory()
        APIRequestFactory.create_batch(5, requestor=consumer1)

        consumer2 = UserFactory()
        APIRequestFactory.create_batch(3, requestor=consumer2)

        yesterday = timezone.now() - timedelta(days=1)
        APIRequestFactory.create_batch(4, requestor=consumer2, created=yesterday)

        _, first, second = self.get_csv_rows()

        day, consumer_count, request_count = first
        assert day == yesterday.date().isoformat()
        assert consumer_count == "1"
        assert request_count == "4"

        day, consumer_count, request_count = second
        assert day == timezone.now().date().isoformat()
        assert consumer_count == "2"
        assert request_count == "8"


class TestDailyConsumerRequestCSV:
    def get_csv_rows(self):
        actual = DailyConsumerRequestCSV().to_string()
        csvfile = io.StringIO(actual)
        reader = csv.reader(csvfile.getvalue().splitlines())
        rows = list(reader)
        return rows

    def test_no_api_requests(self):
        expected_headers = [
            "Date",
            "Consumer ID",
            "Email",
            "Number of daily API requests",
        ]
        rows = self.get_csv_rows()
        headers, *_ = rows
        assert len(rows) == 1
        assert expected_headers == headers

    def test_requests_from_multiple_users(self):
        consumer1 = UserFactory()
        APIRequestFactory.create_batch(5, requestor=consumer1)

        consumer2 = UserFactory()
        APIRequestFactory.create_batch(3, requestor=consumer2)

        yesterday = timezone.now() - timedelta(days=1)
        APIRequestFactory.create_batch(4, requestor=consumer2, created=yesterday)

        _, first, second, third = self.get_csv_rows()

        day, consumer_id, email, request_count = first
        assert day == yesterday.date().isoformat()
        assert consumer_id == str(consumer2.id)
        assert email == str(consumer2.email)
        assert request_count == "4"

        day, consumer_id, email, request_count = second
        assert day == timezone.now().date().isoformat()
        assert consumer_id == str(consumer1.id)
        assert email == str(consumer1.email)
        assert request_count == "5"

        day, consumer_id, email, request_count = third
        assert day == timezone.now().date().isoformat()
        assert consumer_id == str(consumer2.id)
        assert email == str(consumer2.email)
        assert request_count == "3"


class TestRawConsumerRequestsAPICSV:
    def get_csv_rows(self):
        actual = RawConsumerRequestCSV().to_string()
        csvfile = io.StringIO(actual)
        reader = csv.reader(csvfile.getvalue().splitlines())
        rows = list(reader)
        return rows

    def test_no_api_requests(self):
        expected_headers = [
            "id",
            "requestor",
            "Consumer Name",
            "Consumer Organisation",
            "Consumer Email",
            "path_info",
            "query_string",
            "created",
        ]
        rows = self.get_csv_rows()
        headers, *_ = rows
        assert len(rows) == 1
        assert expected_headers == headers

    def test_requests_from_multiple_users(self):
        api_request_count = 5
        consumer1 = UserFactory()
        request = APIRequestFactory(requestor=consumer1)
        APIRequestFactory.create_batch(api_request_count, requestor=consumer1)

        header, first, *rows = self.get_csv_rows()

        assert len(rows) + 1 == api_request_count + 1
        assert first[1] == str(consumer1.id)
        assert first[2] == consumer1.name
        assert first[3] == consumer1.dev_organisation
        assert first[4] == consumer1.email
        assert first[5] == request.path_info
        assert first[6] == request.query_string
        assert first[7] == request.created.isoformat()
