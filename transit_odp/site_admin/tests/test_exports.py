import csv
import io
import zipfile
from datetime import date, timedelta

import pytest
from django.utils import timezone
from django_hosts.resolvers import reverse
from freezegun import freeze_time

import config.hosts
from config.hosts import DATA_HOST
from transit_odp.avl.constants import MORE_DATA_NEEDED, UNDERGOING
from transit_odp.avl.factories import PostPublishingCheckReportFactory
from transit_odp.avl.models import PPCReportType
from transit_odp.browse.exports import get_feed_status
from transit_odp.common.utils import reverse_path
from transit_odp.common.utils.cast import to_int_or_value
from transit_odp.feedback.factories import FeedbackFactory
from transit_odp.feedback.models import SatisfactionRating
from transit_odp.organisation.constants import (
    AVLType,
    DatasetType,
    FaresType,
    TimetableType,
)
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    DatasetFactory,
    DatasetRevisionFactory,
    LicenceFactory,
    OrganisationFactory,
    ServiceCodeExemptionFactory,
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
    ServiceCodeExemptionsCSV,
    WebsiteFeedbackCSV,
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
from transit_odp.users.factories import InvitationFactory, OrgStaffFactory, UserFactory

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
            "% AVL to Timetables feed matching score",
            "Latest matching report URL",
            "% Operator overall AVL to Timetables matching",
            "Archived matching reports URL",
        ]
        assert first_row[0] == revision.dataset.organisation.name
        assert first_row[1] == DatasetType(revision.dataset.dataset_type).name.title()
        assert first_row[2] == str(revision.dataset.id)
        assert first_row[3] == get_feed_status(revision.dataset)
        assert first_row[4] == revision.published_at.isoformat()
        assert first_row[5] == revision.published_by.email
        assert first_row[6] == pretty_account_name(revision.published_by.account_type)

    def test_active_publisher_to_string_last_four_columns(self, client_factory):
        host = config.hosts.PUBLISH_HOST
        organisation = OrganisationFactory()
        user = OrgStaffFactory(organisations=(organisation,))
        today = date.today()

        dataset1 = DatasetFactory(
            organisation=organisation,
            dataset_type=AVLType,
        )
        dataset2 = DatasetFactory(
            organisation=organisation,
            dataset_type=AVLType,
        )
        dataset3 = DatasetFactory(
            organisation=organisation,
            dataset_type=AVLType,
            live_revision__status="inactive",
        )
        dataset4 = DatasetFactory(
            organisation=organisation,
            dataset_type=AVLType,
            avl_compliance_cached__status=MORE_DATA_NEEDED,
        )
        dataset5 = DatasetFactory(
            organisation=organisation,
            dataset_type=AVLType,
        )

        DatasetFactory(
            organisation=organisation, dataset_type=AVLType, avl_compliance_cached=None
        )

        PostPublishingCheckReportFactory(
            dataset=dataset1,
            vehicle_activities_analysed=10,
            vehicle_activities_completely_matching=1,
            granularity=PPCReportType.WEEKLY,
            created=today,
        )
        PostPublishingCheckReportFactory(
            dataset=dataset2,
            vehicle_activities_analysed=230,
            vehicle_activities_completely_matching=120,
            granularity=PPCReportType.WEEKLY,
            created=today - timedelta(days=7),
        )
        PostPublishingCheckReportFactory(
            dataset=dataset3,
            vehicle_activities_analysed=100,
            vehicle_activities_completely_matching=20,
            granularity=PPCReportType.WEEKLY,
            created=today - timedelta(days=7),
        )
        PostPublishingCheckReportFactory(
            dataset=dataset4,
            vehicle_activities_analysed=0,
            vehicle_activities_completely_matching=0,
            granularity=PPCReportType.WEEKLY,
            created=today,
        )
        PostPublishingCheckReportFactory(
            dataset=dataset5,
            vehicle_activities_analysed=0,
            vehicle_activities_completely_matching=0,
            created=today,
        )
        dataset_publishing_csv = DatasetPublishingCSV()
        actual = dataset_publishing_csv.to_string()
        csvfile = io.StringIO(actual)
        reader = csv.reader(csvfile.getvalue().splitlines())

        (
            headers,
            first_row,
            second_row,
            third_row,
            fourth_row,
            fifth_row,
            sixth_row,
        ) = list(reader)
        assert headers == [
            "operator",
            "dataType",
            "dataID",
            "status",
            "lastPublished",
            "email",
            "accountType",
            "% AVL to Timetables feed matching score",
            "Latest matching report URL",
            "% Operator overall AVL to Timetables matching",
            "Archived matching reports URL",
        ]

        client = client_factory(host=host)
        client.force_login(user=user)
        url_report_dataset1 = reverse(
            "avl:download-matching-report",
            args=(organisation.id, dataset1.id),
            host=host,
        )
        url_report_dataset2 = reverse(
            "avl:download-matching-report",
            args=(organisation.id, dataset2.id),
            host=host,
        )
        url_overall = reverse(
            "ppc-archive",
            args=(organisation.id,),
            host=host,
        )

        FIRST_DATASET_PERCENTAGE = "10%"
        SECOND_DATASET_PERCENTAGE = "52%"
        TOTAL_PERCENTAGE = "31%"

        assert first_row[0] == dataset1.organisation.name
        assert first_row[1] == DatasetType(dataset1.dataset_type).name.title()
        assert first_row[2] == str(dataset1.id)
        assert first_row[3] == get_feed_status(dataset1)
        assert first_row[7] == FIRST_DATASET_PERCENTAGE
        assert first_row[8] == url_report_dataset1
        assert first_row[9] == TOTAL_PERCENTAGE
        assert first_row[10] == url_overall

        assert second_row[7] == SECOND_DATASET_PERCENTAGE
        assert second_row[8] == url_report_dataset2
        assert second_row[9] == TOTAL_PERCENTAGE
        assert second_row[10] == url_overall

        assert third_row[7] == ""
        assert third_row[8] == ""
        assert third_row[9] == ""
        assert third_row[10] == ""

        assert fourth_row[7] == MORE_DATA_NEEDED
        assert fourth_row[8] == ""
        assert fourth_row[9] == TOTAL_PERCENTAGE
        assert fourth_row[10] == url_overall

        assert fifth_row[7] == UNDERGOING
        assert fifth_row[8] == ""
        assert fifth_row[9] == TOTAL_PERCENTAGE
        assert fifth_row[10] == url_overall

        assert sixth_row[7] == UNDERGOING


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
        ResourceRequestCounterFactory(counter=5, requestor=consumer1)

        consumer2 = UserFactory()
        ResourceRequestCounterFactory(
            counter=3, requestor=consumer2, path_info="/fares/download/bulk_archive"
        )

        yesterday = timezone.now() - timedelta(days=1)
        ResourceRequestCounterFactory(
            counter=4,
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


class TestWebsiteFeedbackCSV:
    @freeze_time("2022-02-01")
    def test_website_feedback_to_string(self):
        num_rows = 3
        for i in range(num_rows):
            FeedbackFactory(date=date.today() - timedelta(days=i))

        feedback_csv = WebsiteFeedbackCSV()
        actual = feedback_csv.to_string()
        csvfile = io.StringIO(actual)
        reader = csv.reader(csvfile.getvalue().splitlines())
        lines = list(reader)
        assert len(lines) == num_rows + 1

        header = lines[0]
        assert header == [
            "Date",
            "Rating",
            "Page URL",
            "Comments",
        ]
        assert lines[1][0] == "30-Jan-22"
        assert lines[2][0] == "31-Jan-22"
        assert lines[3][0] == "01-Feb-22"

        ratings = [s.label for s in SatisfactionRating]
        for i in range(1, num_rows + 1):
            assert lines[i][1] in ratings


class TestServiceCodeExemptionsCSV:
    def test_headers(self):
        exemptions_csv = ServiceCodeExemptionsCSV()
        csv_file = io.StringIO(exemptions_csv.to_string())
        reader = csv.reader(csv_file.getvalue().splitlines())
        lines = list(reader)
        header = lines[0]
        expected_header = [
            "Organisation",
            "Licence Number",
            "Service Code",
            "Justification",
            "Date of exemption",
            "Exempted by",
        ]
        assert header == expected_header

    @freeze_time("2022-10-31 10:11:12.123456")
    def test_single_row(self):
        org = OrganisationFactory()
        lic = LicenceFactory(organisation=org)
        user = UserFactory(organisations=(org,))
        exemption = ServiceCodeExemptionFactory(licence=lic, exempted_by=user)

        exemptions_csv = ServiceCodeExemptionsCSV()
        csv_file = io.StringIO(exemptions_csv.to_string())
        reader = csv.reader(csv_file.getvalue().splitlines())
        lines = list(reader)

        assert len(lines) == 2
        data = lines[1]
        assert len(data) == 6
        assert data[0] == org.name
        assert data[1] == lic.number
        assert data[2] == lic.number + "/" + str(exemption.registration_code)
        assert data[3] == exemption.justification
        assert data[4] == "2022-10-31 10:11:12.123456+00:00"
        assert data[5] == user.email

    def test_ordering(self):
        org1_name = "ORGB"
        org1 = OrganisationFactory(name=org1_name)
        user1 = UserFactory(organisations=(org1,))
        org1_lic1 = LicenceFactory(organisation=org1, number="PS000001")
        org1_lic2 = LicenceFactory(organisation=org1, number="PA000001")
        service_codes_org1 = [(org1_lic1, 1), (org1_lic2, 1), (org1_lic2, 2)]
        for lic, code in service_codes_org1:
            ServiceCodeExemptionFactory(
                licence=lic,
                exempted_by=user1,
                registration_code=code,
            )

        org2_name = "ORGA"
        org2 = OrganisationFactory(name=org2_name)
        user2 = UserFactory(organisations=(org2,))
        org2_lic1 = LicenceFactory(organisation=org2, number="PS000002")
        service_codes_org2 = [(org2_lic1, 150), (org2_lic1, 19)]
        for lic, code in service_codes_org2:
            ServiceCodeExemptionFactory(
                licence=lic,
                exempted_by=user2,
                registration_code=code,
            )

        exemptions_csv = ServiceCodeExemptionsCSV()
        csv_file = io.StringIO(exemptions_csv.to_string())
        reader = csv.reader(csv_file.getvalue().splitlines())
        lines = list(reader)

        assert len(lines) == 6
        assert lines[1][0] == org2_name
        assert lines[2][0] == org2_name
        assert lines[3][0] == org1_name
        assert lines[4][0] == org1_name
        assert lines[5][0] == org1_name

        assert lines[1][2] == "PS000002/19"
        assert lines[2][2] == "PS000002/150"
        assert lines[3][2] == "PA000001/1"
        assert lines[4][2] == "PA000001/2"
        assert lines[5][2] == "PS000001/1"
