import csv
import io
import zipfile
from datetime import timedelta

import pytest
from django.utils import timezone
from freezegun import freeze_time

from config.hosts import DATA_HOST
from transit_odp.browse.exports import get_feed_status
from transit_odp.common.utils import reverse_path
from transit_odp.common.utils.cast import to_int_or_value
from transit_odp.organisation.constants import DatasetType, FaresType, TimetableType
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    DatasetRevisionFactory,
    OrganisationFactory,
)
from transit_odp.site_admin.csv.dailyaggregates import (
    get_daily_aggregates_csv,
    get_daily_aggregates_df,
)
from transit_odp.site_admin.csv.dailyconsumer import get_consumer_breakdown_df
from transit_odp.site_admin.exports import (
    AgentUserCSV,
    ConsumerCSV,
    DatasetPublishingCSV,
    OperationalStatsCSV,
    PublisherCSV,
    RawConsumerRequestCSV,
    create_metrics_archive,
    pretty_account_name,
)
from transit_odp.site_admin.factories import (
    APIRequestFactory,
    OperationalStatsFactory,
    ResourceRequestCounterFactory,
)
from transit_odp.site_admin.models import MetricsArchive
from transit_odp.users.constants import (
    AgentUserType,
    DeveloperType,
    OrgAdminType,
    OrgStaffType,
)
from transit_odp.users.factories import InvitationFactory, UserFactory

pytestmark = pytest.mark.django_db


class TestPublisherCSV:
    @pytest.mark.parametrize(
        "is_active, user_status, user_type",
        [
            (True, "Active", OrgStaffType),
            (False, "Inactive", OrgStaffType),
            (None, "Pending", OrgStaffType),
            (True, "Active", OrgAdminType),
            (False, "Inactive", OrgAdminType),
            (None, "Pending", OrgAdminType),
        ],
    )
    def test_active_publisher_to_string(self, is_active, user_status, user_type):

        invitation = InvitationFactory(account_type=user_type)
        if is_active is not None:
            user = UserFactory(
                account_type=user_type, is_active=is_active, email=invitation.email
            )
            user.save()
            invitation.save()

        publisher_csv = PublisherCSV()
        actual = publisher_csv.to_string()
        csvfile = io.StringIO(actual)
        reader = csv.reader(csvfile.getvalue().splitlines())
        headers, first_row = list(reader)

        assert headers == [
            "Operator",
            "Account type",
            "Email",
            "User Status",
            "Key Contact",
        ]
        assert first_row == [
            invitation.organisation.name,
            "Standard" if user_type is OrgStaffType else "Admin",
            invitation.email,
            user_status,
            "yes" if invitation.organisation.key_contact else "no",
        ]


class TestDatasetPublishingCSV:
    @pytest.mark.parametrize(
        "factory, dataset_type, user_type",
        [
            (DatasetRevisionFactory, TimetableType, OrgStaffType),
            (DatasetRevisionFactory, FaresType, OrgStaffType),
            (AVLDatasetRevisionFactory, None, OrgStaffType),
            (DatasetRevisionFactory, TimetableType, OrgAdminType),
            (DatasetRevisionFactory, FaresType, OrgAdminType),
            (AVLDatasetRevisionFactory, None, OrgAdminType),
        ],
    )
    def test_active_publisher_to_string(self, factory, dataset_type, user_type):

        user = UserFactory(account_type=user_type)
        if dataset_type is not None:
            revision = factory(published_by=user, dataset__dataset_type=dataset_type)
        else:
            revision = factory(published_by=user)

        dataset_publishing_csv = DatasetPublishingCSV()
        actual = dataset_publishing_csv.to_string()
        csvfile = io.StringIO(actual)
        reader = csv.reader(csvfile.getvalue().splitlines())
        headers, first_row = list(reader)

        assert headers == [
            "operator",
            "dataType",
            "dataID",
            "status",
            "lastPublished",
            "email",
            "accountType",
        ]
        assert first_row[0] == revision.dataset.organisation.name
        assert first_row[1] == DatasetType(revision.dataset.dataset_type).name.title()
        assert first_row[2] == str(revision.dataset.id)
        assert first_row[3] == get_feed_status(revision.dataset)
        assert first_row[4] == revision.published_at.isoformat()
        assert first_row[5] == revision.published_by.email
        assert first_row[6] == pretty_account_name(revision.published_by.account_type)


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
            "Unique Registered Service Codes",
            "Unique Unregistered Service Codes",
            "Number of vehicles",
            "Registered Operators",
            "Registered Publishers Users",
            "Registered Agents Users",
            "Registered Consumers Users",
            "Timetables datasets",
            "Automatic Vehicle Locations (AVL) data feeds",
            "Fares datasets",
            "Operators with at least one published timetables dataset",
            "Operators with at least one published AVL data feed",
            "Operators with at least one published fares dataset",
        ]
        expected_first_row = [
            stats.date.date().isoformat(),
            stats.registered_service_code_count,
            stats.unregistered_service_code_count,
            stats.vehicle_count,
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
    expected_headers = [
        "Date",
        "Number of unique consumers",
        "Number of API requests",
        "Number of total timetables downloads (using download all)",
        "Number of total location data downloads (using download all)",
        "Number of total fares data downloads (using download all)",
    ]

    def get_csv_rows(self):
        start = timezone.now() - timedelta(days=2)
        end = timezone.now()
        csv_string = get_daily_aggregates_df(start, end).to_csv(index=False)
        reader = csv.reader(csv_string.splitlines())
        rows = list(reader)
        return rows

    def test_no_api_requests_to_string(self):

        rows = self.get_csv_rows()
        headers, *_ = rows
        assert len(rows) == 1
        assert self.expected_headers == headers

    def test_headers_of_csv_file(self):
        start = timezone.now() - timedelta(days=2)
        end = timezone.now()
        consumer1 = UserFactory()
        APIRequestFactory.create_batch(5, requestor=consumer1)

        consumer2 = UserFactory()
        APIRequestFactory.create_batch(3, requestor=consumer2)

        yesterday = timezone.now() - timedelta(days=1)
        APIRequestFactory.create_batch(4, requestor=consumer2, created=yesterday)

        csvfile = get_daily_aggregates_csv(start, end)
        with open(csvfile.name, "r") as csv_:
            reader = csv.reader(csv_)
            headers, *rows = list(reader)

        assert headers == self.expected_headers

    @freeze_time("18/03/21 11:17:12")
    def test_requests_from_multiple_users(self):
        ResourceRequestCounterFactory(requestor=None, counter=10)
        consumer1 = UserFactory()
        APIRequestFactory.create_batch(5, requestor=consumer1)

        consumer2 = UserFactory()
        APIRequestFactory.create_batch(3, requestor=consumer2)

        yesterday = timezone.now() - timedelta(days=1)
        APIRequestFactory.create_batch(4, requestor=consumer2, created=yesterday)

        _, first, second = self.get_csv_rows()

        day, consumer_count, request_count, _, _, _ = first
        assert day == yesterday.date().isoformat()
        assert consumer_count == "1"
        assert request_count == "4"

        day, consumer_count, request_count, _, _, _ = second
        assert day == timezone.now().date().isoformat()
        assert consumer_count == "2"
        assert request_count == "8"

    @pytest.mark.parametrize(
        "view_name, csv_index",
        [
            ("downloads-bulk", 3),
            ("downloads-fares-bulk", 5),
            ("downloads-avl-bulk", 4),
        ],
        ids=["timetables", "fares", "avls"],
    )
    def test_requests_from_multiple_users_for_multiple_downloads(
        self, view_name, csv_index
    ):
        ResourceRequestCounterFactory(requestor=None, counter=10)
        resource = reverse_path(view_name, host=DATA_HOST)
        consumer1 = UserFactory()
        APIRequestFactory.create_batch(5, requestor=consumer1)
        ResourceRequestCounterFactory(
            counter=5, requestor=consumer1, path_info=resource
        )

        consumer2 = UserFactory()
        APIRequestFactory.create_batch(3, requestor=consumer2)
        ResourceRequestCounterFactory(
            counter=3, requestor=consumer2, path_info=resource
        )

        yesterday = timezone.now() - timedelta(days=1)
        APIRequestFactory.create_batch(4, requestor=consumer2, created=yesterday)
        ResourceRequestCounterFactory(
            counter=4, requestor=consumer2, date=yesterday.date(), path_info=resource
        )

        _, row1, row2 = self.get_csv_rows()

        assert row1[0] == yesterday.date().isoformat()
        assert row1[1] == "1"
        assert row1[2] == "4"
        assert row1[csv_index] == "4"

        assert row2[0] == timezone.now().date().isoformat()
        assert row2[1] == "2"
        assert row2[2] == "8"
        assert row2[csv_index] == "8"


class TestDailyConsumerRequestCSV:
    def get_csv_rows(self):
        start = timezone.now() - timedelta(days=2)
        end = timezone.now()
        csv_string = get_consumer_breakdown_df(start, end).to_csv(index=False)
        reader = csv.reader(csv_string.splitlines())
        rows = list(reader)
        return rows

    def test_no_api_requests(self):
        expected_headers = [
            "Date",
            "Consumer ID",
            "Email",
            "Number of daily API requests",
            "Number of timetables daily downloads (using Download all)",
            "Number of location data daily downloads (using Download all)",
            "Number of fares daily downloads (using Download all)",
        ]
        rows = self.get_csv_rows()
        headers, *_ = rows
        assert len(rows) == 1
        assert expected_headers == headers

    def test_api_requests_from_multiple_users(self):
        consumer1 = UserFactory()
        APIRequestFactory.create_batch(5, requestor=consumer1)

        consumer2 = UserFactory()
        APIRequestFactory.create_batch(3, requestor=consumer2)

        yesterday = timezone.now() - timedelta(days=1)
        APIRequestFactory.create_batch(4, requestor=consumer2, created=yesterday)

        _, first, second, third = self.get_csv_rows()

        day, consumer_id, email, request_count, _, _, _ = first
        assert day == yesterday.date().isoformat()
        assert consumer_id == str(consumer2.id)
        assert email == str(consumer2.email)
        assert request_count == "4"

        day, consumer_id, email, request_count, _, _, _ = second
        assert day == timezone.now().date().isoformat()
        assert consumer_id == str(consumer1.id)
        assert email == str(consumer1.email)
        assert request_count == "5"

        day, consumer_id, email, request_count, _, _, _ = third
        assert day == timezone.now().date().isoformat()
        assert consumer_id == str(consumer2.id)
        assert email == str(consumer2.email)
        assert request_count == "3"

    def test_both_api_users_and_request_users(self):
        ResourceRequestCounterFactory(requestor=None, counter=10)
        apiuser = UserFactory()
        APIRequestFactory.create_batch(5, requestor=apiuser)

        requestuser = UserFactory()
        ResourceRequestCounterFactory(requestor=requestuser)

        super_user = UserFactory()
        APIRequestFactory.create_batch(5, requestor=super_user)
        ResourceRequestCounterFactory(requestor=super_user, counter=3)

        _, first, second, third = self.get_csv_rows()

        _, consumer_id, _, api, timetables, fares, avls = first
        assert consumer_id == str(apiuser.id)
        assert api == "5"
        assert (timetables, fares, avls) == ("0", "0", "0")

        _, consumer_id, _, api, timetables, fares, avls = second
        assert consumer_id == str(super_user.id)
        assert api == "5"
        assert timetables == "3"
        assert (avls, fares) == ("0", "0")

        _, consumer_id, _, api, timetables, fares, avls = third
        assert consumer_id == str(requestuser.id)
        assert timetables == "1"
        assert (fares, avls) == ("0", "0")

    def test_download_requests_from_multiple_users(self):
        ResourceRequestCounterFactory(requestor=None, counter=10)
        consumer1 = UserFactory()
        ResourceRequestCounterFactory.create_batch(5, requestor=consumer1)

        consumer2 = UserFactory()
        ResourceRequestCounterFactory.create_batch(
            3, requestor=consumer2, path_info="/fares/download/bulk_archive"
        )

        yesterday = timezone.now() - timedelta(days=1)
        ResourceRequestCounterFactory.create_batch(
            4,
            requestor=consumer2,
            date=yesterday.date(),
            path_info="/avl/download/bulk_archive",
        )

        _, first, second, third = self.get_csv_rows()

        day, consumer_id, email, _, timetables, avls, fares = first
        assert day == yesterday.date().isoformat()
        assert consumer_id == str(consumer2.id)
        assert email == str(consumer2.email)
        assert avls == "4"
        assert fares == "0"
        assert timetables == "0"

        day, consumer_id, email, _, timetables, avls, fares = second
        assert day == timezone.now().date().isoformat()
        assert consumer_id == str(consumer1.id)
        assert email == str(consumer1.email)
        assert timetables == "5"
        assert fares == "0"
        assert avls == "0"

        day, consumer_id, email, _, timetables, avls, fares = third
        assert day == timezone.now().date().isoformat()
        assert consumer_id == str(consumer2.id)
        assert email == str(consumer2.email)
        assert fares == "3"
        assert timetables == "0"
        assert avls == "0"


class TestRawConsumerRequestsAPICSV:
    def get_csv_rows(self):
        actual = RawConsumerRequestCSV().to_string()
        csvfile = io.StringIO(actual)
        reader = csv.reader(csvfile.getvalue().splitlines())
        rows = list(reader)
        return rows

    def test_no_api_requests(self):
        expected_headers = [
            "datatype",
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
        api_metrics_csv = ["Timetable", "Fares", "GTFS VM", "SIRI VM"]

        header, first, *rows = self.get_csv_rows()

        assert len(rows) + 1 == api_request_count + 1
        assert first[0] in api_metrics_csv
        assert first[1] == str(request.id)
        assert first[2] == str(consumer1.id)
        assert first[3] == f"{consumer1.first_name} {consumer1.last_name}"
        assert first[4] == consumer1.dev_organisation
        assert first[5] == consumer1.email
        assert first[6] == request.path_info
        assert first[7] == request.query_string
        assert first[8] == request.created.isoformat()


class TestAPIRequestArchive:
    def count_entries_in_csv(self, archive):
        expected_files = [
            "rawapimetrics.csv",
            "dailyconsumerbreakdown.csv",
            "dailyaggregates.csv",
        ]
        with zipfile.ZipFile(archive, "r") as z:
            assert expected_files == [name for name in z.namelist()]
            with z.open("dailyaggregates.csv") as csvfile:
                return len(csvfile.readlines()) - 1

    def test_filtering_creates_one_entry_with_one_line(self):
        now = timezone.now()
        yesterday = now - timedelta(days=1)
        APIRequestFactory.create_batch(5, created=yesterday)
        create_metrics_archive(yesterday, now)
        archive_qs = MetricsArchive.objects.all()

        assert archive_qs.count() == 1
        archive = archive_qs.first()

        assert archive.end == now.date()
        assert archive.start == yesterday.date()
        assert self.count_entries_in_csv(archive.archive) == 1

    def test_running_task_twice_creates_one_entry_with_two_lines(self):
        start = timezone.datetime(2021, 6, 1)
        first_day = timezone.datetime(2021, 6, 2)
        APIRequestFactory.create_batch(5, created=start)
        create_metrics_archive(start, first_day)

        second_day = timezone.datetime(2021, 6, 2)
        APIRequestFactory.create_batch(5, created=first_day)
        create_metrics_archive(start, second_day)

        archive_qs = MetricsArchive.objects.all()

        assert archive_qs.count() == 1
        archive = archive_qs.first()

        assert archive.start == start.date()
        assert archive.end == second_day.date()
        assert self.count_entries_in_csv(archive.archive) == 2

    def test_two_start_dates_creates_two_entries(self):
        start = timezone.datetime(2021, 6, 1)
        first_day = timezone.datetime(2021, 6, 30)
        APIRequestFactory.create_batch(5, created=first_day)
        create_metrics_archive(start, first_day)

        new_start = timezone.datetime(2021, 7, 1)
        second_day = timezone.datetime(2021, 7, 2)
        APIRequestFactory.create_batch(5, created=second_day)
        create_metrics_archive(new_start, second_day)

        archive_qs = MetricsArchive.objects.all()
        assert archive_qs.count() == 2
        for archive in archive_qs:
            assert self.count_entries_in_csv(archive.archive) == 1
