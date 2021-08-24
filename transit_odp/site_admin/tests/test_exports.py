import csv
import io
import zipfile
from datetime import datetime, timedelta

import factory
import pytest
from dateutil import parser
from django.utils import timezone

from config import hosts
from transit_odp.common.utils.cast import to_int_or_value
from transit_odp.data_quality.factories import (
    DataQualityReportFactory,
    PTIValidationResultFactory,
)
from transit_odp.fares.factories import FaresMetadataFactory
from transit_odp.organisation.constants import DatasetType, FaresType, TimetableType
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    DatasetRevisionFactory,
    FaresDatasetRevisionFactory,
    LicenceFactory,
    OperatorCodeFactory,
    OrganisationFactory,
    TXCFileAttributesFactory,
)
from transit_odp.site_admin.exports import (
    AgentUserCSV,
    APIRequestCSV,
    ConsumerCSV,
    DailyConsumerRequestCSV,
    DatasetPublishingCSV,
    OperationalStatsCSV,
    OrganisationCSV,
    PublisherCSV,
    RawConsumerRequestCSV,
    TimetablesDataCatalogueCSV,
    create_metrics_archive,
    pretty_account_name,
    service_code_to_status,
)
from transit_odp.site_admin.factories import APIRequestFactory, OperationalStatsFactory
from transit_odp.site_admin.models import MetricsArchive
from transit_odp.users.constants import (
    AgentUserType,
    DeveloperType,
    OrgAdminType,
    OrgStaffType,
)
from transit_odp.users.factories import InvitationFactory, UserFactory

pytestmark = pytest.mark.django_db


class TestOrganisationCSV:
    def test_organisation_to_csv(self, client_factory):
        organisation = OrganisationFactory(licence_required=True, nocs=0)
        client = client_factory(host=hosts.ADMIN_HOST)
        now = datetime.today()
        before = now - timedelta(days=2)
        after = now + timedelta(days=2)
        user = UserFactory(account_type=OrgAdminType, organisations=(organisation,))
        client.force_login(user)
        nocs = OperatorCodeFactory.create_batch(3, organisation=organisation)
        licences = LicenceFactory.create_batch(3, organisation=organisation)

        invitation = InvitationFactory(
            account_type=OrgAdminType,
            organisation=organisation,
            accepted=True,
            email=user.email,
        )

        timetable_revision = DatasetRevisionFactory(dataset__organisation=organisation)
        # Valid now services
        txc_attributes = TXCFileAttributesFactory.create_batch(
            3,
            revision=timetable_revision,
            operating_period_start_date=before,
            operating_period_end_date=after,
        )
        # Future services
        TXCFileAttributesFactory.create_batch(
            2,
            revision=timetable_revision,
            operating_period_start_date=after,
        )

        # Unregistered services
        TXCFileAttributesFactory.create_batch(
            4,
            revision=timetable_revision,
            operating_period_end_date=before,
            service_code=factory.Sequence(lambda n: f"UZ0000{n:03}"),
        )

        timetable_revision = DatasetRevisionFactory(dataset__organisation=organisation)
        # This is an attribute from a different dateset__live_revision but with
        # the same service code. We do not want this is be discounted
        TXCFileAttributesFactory(
            revision=timetable_revision,
            operating_period_start_date=before,
            operating_period_end_date=after,
            service_code=txc_attributes[1].service_code,
        )

        AVLDatasetRevisionFactory.create_batch(3, dataset__organisation=organisation)
        fares_revision = FaresDatasetRevisionFactory(dataset__organisation=organisation)
        FaresMetadataFactory(revision=fares_revision, num_of_fare_products=10)

        org_csv = OrganisationCSV()
        actual = org_csv.to_string()
        csvfile = io.StringIO(actual)
        reader = csv.reader(csvfile.getvalue().splitlines())
        headers, first_row = list(reader)

        assert headers == [
            "Name",
            "Status",
            "dateInviteAccepted",
            "dateInvited",
            "lastLogin",
            "permitHolder",
            "nationalOperatorCodes",
            "licenceNumbers",
            "numberOfLicences",
            "numberOfServicesWithValidOperatingDates",
            "additionalServicesWithFutureStartDate",
            "unregisteredServices",
            "numberOfFareProducts",
            "numberOfPublishedTimetableDatasets",
            "numberOfPublishedAVLDatasets",
            "numberOfPublishedFaresDatasets",
        ]

        assert first_row[0] == organisation.name, "test name"
        assert first_row[1] == "Active", "test Status"
        assert first_row[2] == user.date_joined.isoformat(), "test dateInviteAccepted"
        assert first_row[3] == invitation.sent.isoformat(), "test dateInvited"
        assert first_row[4] == user.last_login.isoformat(), "test lastLogin"
        assert first_row[5] == "True", "test permitHolder"
        assert first_row[6] == "; ".join(
            [noc.noc for noc in nocs]
        ), "test nationalOperatorCodes"
        assert first_row[7] == "; ".join(
            [licence.number for licence in licences]
        ), "test licenceNumbers"
        assert first_row[8] == "3", "test numberOfLicences"
        assert first_row[9] == "4", "test numberOfServicesWithValidOperatingDates"
        assert first_row[10] == "2", "test additionalServicesWithFutureStartDate"
        assert first_row[11] == "4", "test numberOfUnregisteredServices"
        assert first_row[12] == "10", "test numberOfFareProducts"
        assert first_row[13] == "2", "numberOfPublishedTimetableDatasets"
        assert first_row[14] == "3", "numberOfPublishedAVLDatasets "
        assert first_row[15] == "1", "numberOfPublishedFaresDatasets"


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


class TestDasetPublishingCSV:
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
        assert first_row[3] == revision.status
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
            "Number of vehicles",
            "Registered Operators",
            "Registered Publishers Users",
            "Registered Agents Users",
            "Registered Consumers Users",
            "Timetables datasets",
            "Automatic Vehicle Locations (AVL) data feeds",
            "Fares datasets",
            "Operators with at least one published timetables dataset",
            "Operators with at least one published AVL datafeed",
            "Operators with at least one published fares dataset",
        ]
        expected_first_row = [
            stats.date.date().isoformat(),
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
        assert first[3] == consumer1.name
        assert first[4] == consumer1.dev_organisation
        assert first[5] == consumer1.email
        assert first[6] == request.path_info
        assert first[7] == request.query_string
        assert first[8] == request.created.isoformat()


class TestTimetablesDataCatalogueCSV:
    @pytest.mark.parametrize(
        ("pti_count", "service_code"),
        [
            (1, "ABC123"),
            (1, "UZABC123"),
            (0, "ABC123"),
            (0, "UZABC123"),
        ],
    )
    def test_to_string(self, pti_count, service_code):
        txc = TXCFileAttributesFactory(service_code=service_code)
        DataQualityReportFactory(revision=txc.revision, score=0.5)
        PTIValidationResultFactory(revision=txc.revision, count=pti_count)

        actual = TimetablesDataCatalogueCSV().to_string()
        csvfile = io.StringIO(actual)
        reader = csv.reader(csvfile.getvalue().splitlines())
        rows = list(reader)

        expected_headers = [
            "serviceStatus",
            "organisationName",
            "datasetId",
            "dqScore",
            "bodsCompliant",
            "lastUpdatedDate",
            "XMLFileName",
            "licenceNumber",
            "nationalOperatorCode",
            "serviceCode",
            "publicUseFlag",
            "operatingPeriodStartDate",
            "operatingPeriodEndDate",
            "serviceRevisionNumber",
            "lineName",
        ]
        assert len(rows) == 2
        headers, first = rows
        assert expected_headers == headers
        assert first[0] == service_code_to_status(service_code)
        assert first[1] == txc.revision.dataset.organisation.name
        assert int(first[2]) == txc.revision.dataset.id
        assert first[3] == "50%"
        assert first[4] == "no" if pti_count > 0 else "yes"
        assert parser.parse(first[5]) == txc.revision.published_at
        assert first[6] == txc.filename
        assert first[7] == txc.licence_number
        assert first[8] == txc.national_operator_code
        assert first[9] == txc.service_code
        assert eval(first[10]) == txc.public_use
        assert first[11] == txc.operating_period_start_date
        assert first[12] == txc.operating_period_end_date
        assert first[13] == txc.revision_number
        assert first[14] == "; ".join(txc.line_names)

    @pytest.mark.parametrize(
        ("service_code", "expected"),
        [("ABC123", "Registered"), ("UZABC123", "Unregistered"), ("", ""), (None, "")],
    )
    def test_service_code_to_status(self, service_code, expected):
        result = service_code_to_status(service_code)
        assert result == expected


class TestAPIRequestArchive:
    def count_entries_in_csv(self, archive):
        expected_files = [
            "dailyaggregates.csv",
            "dailyconsumerbreakdown.csv",
            "rawapimetrics.csv",
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
