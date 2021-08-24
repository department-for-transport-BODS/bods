from datetime import datetime, timedelta

import factory
import faker
import pytest
import pytz
from django.test import override_settings
from django.utils.timezone import now
from django_hosts import reverse
from freezegun import freeze_time

from config import hosts
from transit_odp.data_quality.factories.report import PTIObservationFactory
from transit_odp.fares.factories import FaresMetadataFactory
from transit_odp.naptan.factories import AdminAreaFactory, StopPointFactory
from transit_odp.organisation.constants import (
    AVLType,
    FaresType,
    FeedStatus,
    TimetableType,
)
from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetRevisionFactory,
    FaresDatasetRevisionFactory,
    OrganisationFactory,
    TXCFileAttributesFactory,
)
from transit_odp.organisation.models import Dataset, DatasetRevision, Organisation
from transit_odp.pipelines.factories import (
    DatasetETLTaskResultFactory,
    RemoteDatasetHealthCheckCountFactory,
)
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.transmodel.factories import ServicePatternFactory
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db

FAKER = faker.Faker()


class TestOrganisationQuerySet:
    # TODO - test add_org_admin_count
    # TODO - test add_org_staff_count

    # Filters
    def test_has_published_feeds(self):
        """Tests the queryset is annotated with the total dataset count
        (excluding drafts)"""
        orgs = OrganisationFactory.create_batch(2)
        DatasetRevisionFactory(dataset__organisation=orgs[0], is_published=False)
        DatasetRevisionFactory(dataset__organisation=orgs[1], is_published=False)
        DatasetRevisionFactory(dataset__organisation=orgs[1], is_published=True)
        qs = Organisation.objects.has_published_datasets()
        assert len(qs) == 1
        assert qs[0] == orgs[1]

    # Annotations
    def test_add_dataset_count(self):
        """Tests the queryset is annotated with the total dataset count
        (including drafts)"""
        # Setup
        orgs = OrganisationFactory.create_batch(2)
        DatasetRevisionFactory(dataset__organisation=orgs[0], is_published=False)
        DatasetRevisionFactory(dataset__organisation=orgs[1], is_published=False)
        DatasetRevisionFactory(dataset__organisation=orgs[1], is_published=True)
        qs = Organisation.objects.add_dataset_count()

        assert len(qs) == 2
        for org in qs:
            if org.id == orgs[0].id:
                assert org.dataset_count == 1
            else:
                assert org.dataset_count == 2

    def test_add_published_dataset_count(self):
        """Tests the queryset is annotated with the total dataset count
        (excluding drafts)"""
        orgs = OrganisationFactory.create_batch(2)
        DatasetRevisionFactory(dataset__organisation=orgs[0], is_published=False)
        DatasetRevisionFactory(dataset__organisation=orgs[1], is_published=False)
        DatasetRevisionFactory(dataset__organisation=orgs[1], is_published=True)
        qs = Organisation.objects.add_published_dataset_count()
        assert len(qs) == 2
        for org in qs:
            if org.id == orgs[0].id:
                assert org.published_dataset_count == 0
            else:
                assert org.published_dataset_count == 1

    @pytest.mark.parametrize("has_user", [True, False])
    def test_add_registration_complete(self, has_user):
        """Tests annotation `add_registration_complete` which should add
        `registration_complete=True` when the organisation has at least one user and
        `=False` otherwise."""
        org = OrganisationFactory()
        if has_user:
            UserFactory(organisations=(org,), account_type=AccountType.org_admin.value)
        result = Organisation.objects.add_registration_complete().first()
        assert result == org
        assert result.registration_complete is has_user

    def test_published_operator_count(self):

        org1 = OrganisationFactory()

        DatasetFactory(organisation=org1, dataset_type=TimetableType)
        DatasetFactory(organisation=org1, dataset_type=AVLType)
        DatasetFactory(organisation=org1, dataset_type=FaresType)

        fetched_org = Organisation.objects.add_published_dataset_count_types().first()

        assert fetched_org.published_avl_count == 1
        assert fetched_org.published_fares_count == 1
        assert fetched_org.published_timetable_count == 1

    def test_published_operator_count_without_avl(self):
        org1 = OrganisationFactory()

        DatasetFactory(organisation=org1, dataset_type=TimetableType)
        DatasetFactory(organisation=org1, dataset_type=FaresType)

        fetched_org = Organisation.objects.add_published_dataset_count_types().first()

        assert fetched_org.published_avl_count == 0
        assert fetched_org.published_fares_count == 1
        assert fetched_org.published_timetable_count == 1

    def test_add_unregistered_service_count(self):
        organisation = OrganisationFactory(licence_required=True)
        timetable_revision = DatasetRevisionFactory(dataset__organisation=organisation)
        TXCFileAttributesFactory.create_batch(
            3,
            revision=timetable_revision,
            service_code=factory.Sequence(lambda n: f"UZ0000{n:03}"),
        )
        TXCFileAttributesFactory.create_batch(
            2,
            revision=timetable_revision,
        )

        orgs = Organisation.objects.add_unregistered_service_count()
        org = orgs.first()
        assert org.unregistered_service_count == 3

    def test_add_number_of_services_valid_operating_date(self):
        organisation = OrganisationFactory(licence_required=True)
        now = datetime.today()
        before = now - timedelta(days=2)
        after = now + timedelta(days=2)

        timetable_revision = DatasetRevisionFactory(dataset__organisation=organisation)
        TXCFileAttributesFactory.create_batch(
            3,
            revision=timetable_revision,
            operating_period_start_date=before,
            operating_period_end_date=after,
        )
        TXCFileAttributesFactory.create_batch(
            2,
            revision=timetable_revision,
            operating_period_start_date=after,
        )

        orgs = Organisation.objects.add_number_of_services_valid_operating_date()
        org = orgs.first()
        assert org.number_of_services_valid_operating_date == 3

    def test_add_published_services_with_future_start_date(self):
        organisation = OrganisationFactory(licence_required=True)
        now = datetime.today()
        before = now - timedelta(days=2)
        after = now + timedelta(days=2)

        timetable_revision = DatasetRevisionFactory(dataset__organisation=organisation)
        TXCFileAttributesFactory.create_batch(
            3,
            revision=timetable_revision,
            operating_period_start_date=before,
            operating_period_end_date=after,
        )
        TXCFileAttributesFactory.create_batch(
            2,
            revision=timetable_revision,
            operating_period_start_date=after,
        )

        orgs = Organisation.objects.add_published_services_with_future_start_date()
        org = orgs.first()
        assert org.published_services_with_future_start_date == 2

    def test_number_of_fares_products(self):
        organisation = OrganisationFactory(licence_required=True, nocs=0)
        fares_revision = FaresDatasetRevisionFactory(dataset__organisation=organisation)
        FaresMetadataFactory(revision=fares_revision, num_of_fare_products=10)

        orgs = Organisation.objects.add_number_of_fare_products()
        org = orgs.first()
        assert org.total_fare_products == 10


@pytest.fixture
def revision_data():
    now = datetime.utcnow().replace(tzinfo=pytz.utc)
    datasets = DatasetFactory.create_batch(3, live_revision=None)
    kwargs_list = [
        # dataset 1 has 3 live revisions
        {
            "created": now - timedelta(hours=2),
            "dataset": datasets[0],
            "is_published": True,
        },
        {
            "created": now - timedelta(hours=1),
            "dataset": datasets[0],
            "is_published": True,
        },
        {
            "created": now,
            "name": "DATASET 1 LIVE REVISION",
            "dataset": datasets[0],
            "is_published": True,
        },
        # dataset 2 has a live + draft revision
        {
            "created": now - timedelta(hours=6),
            "name": "DATASET 2 LIVE REVISION",
            "dataset": datasets[1],
            "is_published": True,
        },
        {
            "created": now - timedelta(hours=1),
            "dataset": datasets[1],
            "is_published": False,
        },
        # dataset 3 has only a draft revision
        {"created": now, "dataset": datasets[2], "is_published": False},
    ]

    for kwargs in kwargs_list:
        DatasetRevisionFactory(**kwargs)

    return datasets, DatasetRevision.objects.all()


class TestDatasetQuerySet:
    def test_select_related_live_revision_max_queries_2(
        self, django_assert_max_num_queries, revision_data
    ):
        """
        Tests select_related_live_revision sets up efficient access of
        live_revision with a maximum of 2 database hits.

        We can use this method to iterate over a DatasetQuerySet and access the
        related live_revision without incurring
        N database queries.
        """
        datasets, revisions = revision_data

        # There should only be a maximum of 2 database hits
        with django_assert_max_num_queries(2):
            # The select_related_live_revision actually uses prefetch_related
            # underneath, so there should be 2 hits
            for dataset in Dataset.objects.all().select_related_live_revision():
                # test we can iterate over the QuerySet and access live_revision
                # without incurring anymore DB hits
                if dataset.id == datasets[0].id:
                    assert dataset._live_revision[0].name == "DATASET 1 LIVE REVISION"
                elif dataset.id == datasets[1].id:
                    assert dataset._live_revision[0].name == "DATASET 2 LIVE REVISION"
                else:
                    assert dataset._live_revision == []

    def test_get_published(self, revision_data):
        """Tests a DatasetQuerySet is returned filtered by whether the dataset
        is live, i.e. has a published revision"""
        datasets, revisions = revision_data
        actual = Dataset.objects.get_published()
        assert len(actual) == 2
        for dataset in actual:
            assert dataset.id in [datasets[0].id, datasets[1].id]

    def test_get_active(self):
        """Tests queryset is filtered to datasets which have a published revision
        in a non-expired state"""
        # TODO - should remove live/draft statuses since these are analogous to
        # published/not published
        datasets = DatasetFactory.create_batch(3, live_revision=None)
        DatasetRevisionFactory(
            dataset=datasets[0], is_published=True, status=FeedStatus.live.value
        )
        DatasetRevisionFactory(
            dataset=datasets[1], is_published=True, status=FeedStatus.expired.value
        )
        DatasetRevisionFactory(
            dataset=datasets[2], is_published=False, status=FeedStatus.draft.value
        )
        qs = Dataset.objects.get_active()
        assert len(qs) == 1
        assert qs[0].id == datasets[0].id

    def test_search(self):
        """Tests queryset is filtered using keywords to search on live_revision's
        related transmodel entities and dataset attributes.
        """
        admin_areas = [
            AdminAreaFactory(name=name) for name in ["Cambridge", "London", "Leeds"]
        ]
        organisations = [OrganisationFactory(name=name) for name in ["OrgX", "OrgY"]]
        datasets = [
            DatasetFactory(organisation=organisation, live_revision=None)
            for organisation in organisations
        ]
        [
            DatasetRevisionFactory(
                dataset=datasets[0],
                name="DatasetP",
                description="Descriptive",
                admin_areas=admin_areas[:1],
                is_published=True,
            ),
            DatasetRevisionFactory(
                dataset=datasets[1],
                name="DatasetQ",
                description="",
                admin_areas=admin_areas[1:],
                is_published=True,
            ),
        ]

        qs = Dataset.objects.search("DatasetP")
        assert len(qs) == 1
        assert qs[0] == datasets[0]

        qs = Dataset.objects.search("Lon")
        assert len(qs) == 1
        assert qs[0] == datasets[1]

        qs = Dataset.objects.search("org")
        assert len(qs) == 2

        # Search on descrpiption
        qs = Dataset.objects.search("Descriptive")
        assert len(qs) == 1
        assert qs[0] == datasets[0]

    def test_get_local(self):
        """Tests QuerySet filter method to return local datasets"""
        config = {"status": FeedStatus.success.value, "is_published": True}
        local = DatasetRevisionFactory(**config)
        DatasetRevisionFactory(url_link="www.example.com/dataset", **config)
        DatasetRevisionFactory(url_link="www.example.com/dataset", is_published=False)
        revisions = Dataset.objects.get_local()
        assert len(revisions) == 1
        assert revisions[0] == local.dataset

    def test_get_remote(self):
        """Tests QuerySet filter method to return remote datasets"""
        config = {"status": FeedStatus.success.value, "is_published": True}
        DatasetRevisionFactory(**config)
        remote = DatasetRevisionFactory(url_link="www.example.com/dataset", **config)
        DatasetRevisionFactory(url_link="www.example.com/dataset", is_published=False)

        revisions = Dataset.objects.get_remote()
        assert len(revisions) == 1
        assert revisions[0] == remote.dataset

    def test_add_live_data(self):
        """Tests the queryset is annotated with data of the current live revision"""
        now = datetime.utcnow().replace(tzinfo=pytz.utc)

        dataset = DatasetFactory(live_revision=None)
        revision = DatasetRevisionFactory(
            dataset=dataset,
            is_published=True,
            name="My revision",
            description="Some description",
            comment="Some comment",
            url_link="http://www.example.com/data/",
            status="live",
            num_of_lines=15,
            num_of_operators=2,
            num_of_bus_stops=100,
            transxchange_version="1.5",
            imported=now,
            bounding_box="XYXYXY",
            publisher_creation_datetime=now,
            publisher_modified_datetime=now,
            first_expiring_service=now + timedelta(days=30),
            last_expiring_service=now + timedelta(days=30),
            first_service_start=now - timedelta(days=365),
        )
        actual = Dataset.objects.add_live_data().first()

        assert actual.id == dataset.id
        assert actual.name == revision.name
        assert actual.description == revision.description
        assert actual.comment == revision.comment
        assert actual.url_link == revision.url_link
        assert actual.upload_file == revision.upload_file
        assert actual.status == revision.status
        assert actual.num_of_lines == revision.num_of_lines
        assert actual.num_of_operators == revision.num_of_operators
        assert actual.num_of_bus_stops == revision.num_of_bus_stops
        assert actual.transxchange_version == revision.transxchange_version
        assert actual.imported == revision.imported
        assert actual.bounding_box == revision.bounding_box
        assert (
            actual.publisher_creation_datetime == revision.publisher_creation_datetime
        )
        assert (
            actual.publisher_modified_datetime == revision.publisher_modified_datetime
        )
        assert actual.first_expiring_service == revision.first_expiring_service
        assert actual.last_expiring_service == revision.last_expiring_service
        assert actual.first_service_start == revision.first_service_start

    def test_add_admin_area_names(self):
        """Tests admin area names of live revision are aggregated and
        annotated on the dataset queryset"""
        admin_areas = [AdminAreaFactory(name=name) for name in "XZZYY"]
        dataset = DatasetFactory(live_revision=None)
        revision = DatasetRevisionFactory(dataset=dataset, admin_areas=admin_areas)
        assert revision.admin_areas.count() == 5
        assert dataset.live_revision == revision
        qs = Dataset.objects.add_admin_area_names()
        assert qs[0].admin_area_names == "X, Y, Z"

    def test_add_organisation_name(self):
        """Tests organisation name is annotated onto queryset"""
        dataset = DatasetFactory()
        organisation = dataset.organisation
        datasets = Dataset.objects.add_organisation_name()
        assert len(datasets) == 1
        assert datasets[0].organisation_name == organisation.name

    # TODO - test agg_global_feed_stats

    def test_add_download_url(self):
        dataset = DatasetFactory()
        expected_download_url = reverse(
            "feed-download", host=hosts.DATA_HOST, args=[dataset.id]
        )
        result = Dataset.objects.get(id=dataset.id)
        assert result.download_url == expected_download_url


class TestDatasetRevisionQuerySet:
    def test_get_published(self):
        revision = DatasetRevisionFactory(is_published=True)
        DatasetRevisionFactory(is_published=False)
        qs = DatasetRevision.objects.get_published()
        assert len(qs) == 1
        assert qs[0] == revision

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            (FeedStatus.live, True),
            (FeedStatus.warning, False),
            (FeedStatus.expiring, False),
            (FeedStatus.error, False),
            (FeedStatus.draft, False),
            (FeedStatus.pending, False),
            (FeedStatus.indexing, False),
            (FeedStatus.expired, False),
        ],
    )
    def test_get_live(self, test_input, expected):
        DatasetRevisionFactory(status=test_input.value, is_published=True)
        assert DatasetRevision.objects.get_live().exists() == expected

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            (FeedStatus.live, False),
            (FeedStatus.warning, False),
            (FeedStatus.expiring, True),
            (FeedStatus.error, False),
            (FeedStatus.draft, False),
            (FeedStatus.pending, False),
            (FeedStatus.indexing, False),
            (FeedStatus.expired, False),
        ],
    )
    def test_get_expiring(self, test_input, expected):
        DatasetRevisionFactory(status=test_input.value, is_published=True)
        assert DatasetRevision.objects.get_expiring().exists() == expected

    def test_get_local(self):
        """Tests QuerySet filter method to return local datasets"""
        config = {"status": FeedStatus.live.value, "is_published": True}
        local = DatasetRevisionFactory(**config)
        DatasetRevisionFactory(url_link="www.example.com/dataset", **config)
        revisions = DatasetRevision.objects.get_local()
        assert len(revisions) == 1
        assert revisions[0] == local

    def test_get_remote(self):
        """Tests QuerySet filter method to return remote datasets"""
        config = {"status": FeedStatus.live.value, "is_published": True}
        DatasetRevisionFactory(**config)
        remote = DatasetRevisionFactory(url_link="www.example.com/dataset", **config)
        revisions = DatasetRevision.objects.get_remote()
        assert len(revisions) == 1
        assert revisions[0] == remote

    # Test annotations

    @pytest.mark.parametrize("distinct, expected", [(True, 5), (False, 25)])
    def test_add_stop_count(self, distinct: bool, expected: int):
        # Set up
        revision = DatasetRevisionFactory()
        stops = StopPointFactory.create_batch(5)
        ServicePatternFactory.create_batch(5, revision=revision, stops=stops)

        revisions = DatasetRevision.objects.add_stop_count(distinct=distinct)
        assert len(revisions) == 1
        assert revisions[0].stop_count == expected

    # TODO - add test for add_bus_stop_count
    # TODO - add test for add_publisher_email

    def test_add_error_code(self):
        """Tests the QuerySet is annotated with the latest error_code from
        DatasetETLTaskResult"""
        revision = DatasetRevisionFactory()

        with freeze_time(now() - timedelta(minutes=5)):
            DatasetETLTaskResultFactory(
                revision=revision, error_code=DatasetETLTaskResult.SUSPICIOUS_FILE
            )
        task = DatasetETLTaskResultFactory(
            revision=revision, error_code=DatasetETLTaskResult.SYSTEM_ERROR
        )
        actual = DatasetRevision.objects.add_error_code().first()
        assert actual.error_code == task.error_code

    def test_add_error_code_defaults_to_none(self):
        """Tests error_code defaults to empty string if DatasetETLTaskResult
        doesn't exist"""
        DatasetRevisionFactory()
        actual = DatasetRevision.objects.add_error_code().first()
        assert actual.error_code == ""

    def test_is_pti_compliant_is_annotated(self):
        datasets = DatasetFactory.create_batch(7)
        non_compliant_datasets = datasets[:3]
        for dataset in non_compliant_datasets:
            PTIObservationFactory(revision=dataset.live_revision)

        queryset = Dataset.objects.add_is_live_pti_compliant()
        assert queryset.filter(is_pti_compliant=True).count() == 4
        non_compliant_qs = queryset.filter(is_pti_compliant=False)
        assert non_compliant_qs.count() == 3
        assert list(non_compliant_qs.order_by("id").values_list("id", flat=True)) == [
            dataset.id for dataset in non_compliant_datasets
        ]

    def test_old_pti_compliant(self):
        datasets = DatasetFactory.create_batch(6)
        for dataset in datasets[:3]:
            dataset.live_revision.created = datetime(2000, 1, 1)
            dataset.live_revision.save()

        queryset = Dataset.objects.add_is_live_pti_compliant()
        old_datasets = queryset.filter(is_after_pti_compliance_date=False)
        assert old_datasets.count() == 3


def test_organisation_get_remote_dataset():
    expected_count = 4
    DatasetRevisionFactory.create_batch(
        expected_count, is_published=True, url_link=FAKER.uri()
    )
    DatasetRevisionFactory(is_published=False, url_link=FAKER.uri())
    DatasetRevisionFactory(is_published=True, url_link="")
    datasets = Dataset.objects.get_active_remote_datasets()
    assert datasets.count() == expected_count


def test_organisation_get_remote_timetables():
    expected_count = 4
    DatasetRevisionFactory.create_batch(
        expected_count,
        dataset__dataset_type=TimetableType,
        is_published=True,
        url_link=FAKER.uri(),
    )
    DatasetRevisionFactory(
        dataset__dataset_type=FaresType, is_published=True, url_link=FAKER.uri()
    )
    DatasetRevisionFactory(is_published=False, url_link=FAKER.uri())
    DatasetRevisionFactory(is_published=True, url_link="")
    datasets = Dataset.objects.get_remote_timetables()
    assert datasets.count() == expected_count


def test_organisation_get_remote_fares():
    expected_count = 4
    DatasetRevisionFactory.create_batch(
        expected_count,
        dataset__dataset_type=FaresType,
        is_published=True,
        url_link=FAKER.uri(),
    )
    DatasetRevisionFactory(
        dataset__dataset_type=TimetableType, is_published=True, url_link=FAKER.uri()
    )
    DatasetRevisionFactory(is_published=False, url_link=FAKER.uri())
    DatasetRevisionFactory(is_published=True, url_link="")
    datasets = Dataset.objects.get_remote_fares()
    assert datasets.count() == expected_count


def test_organisation_get_available_remote_timetables():
    expected_count = 4
    DatasetRevisionFactory.create_batch(
        expected_count,
        dataset__dataset_type=TimetableType,
        is_published=True,
        url_link=FAKER.uri(),
    )
    RemoteDatasetHealthCheckCountFactory.create_batch(
        3,
        count=2,
        revision__dataset__dataset_type=TimetableType,
        revision__is_published=True,
        revision__url_link=FAKER.uri(),
    )

    datasets = Dataset.objects.get_available_remote_timetables()
    assert datasets.count() == expected_count


@pytest.mark.parametrize(
    ("dataset_type", "func"),
    [
        (FaresType, "get_available_remote_fares"),
        (TimetableType, "get_available_remote_timetables"),
    ],
)
def test_organisation_get_available_remote(dataset_type, func):
    available_count = 4
    DatasetRevisionFactory.create_batch(
        available_count,
        dataset__dataset_type=dataset_type,
        is_published=True,
        url_link=FAKER.uri(),
    )
    unavailable_count = 3
    RemoteDatasetHealthCheckCountFactory.create_batch(
        unavailable_count,
        count=2,
        revision__dataset__dataset_type=dataset_type,
        revision__is_published=True,
        revision__url_link=FAKER.uri(),
    )

    datasets = getattr(Dataset.objects, func)()
    assert datasets.count() == available_count


@pytest.mark.parametrize(
    ("dataset_type", "func"),
    [
        (FaresType, "get_unavailable_remote_fares"),
        (TimetableType, "get_unavailable_remote_timetables"),
    ],
)
def test_organisation_get_unavailable_remote(dataset_type, func):
    available_count = 4
    DatasetRevisionFactory.create_batch(
        available_count,
        dataset__dataset_type=dataset_type,
        is_published=True,
        url_link=FAKER.uri(),
    )
    unavailable_count = 3
    RemoteDatasetHealthCheckCountFactory.create_batch(
        unavailable_count,
        count=2,
        revision__dataset__dataset_type=dataset_type,
        revision__is_published=True,
        revision__url_link=FAKER.uri(),
    )

    datasets = getattr(Dataset.objects, func)()
    assert datasets.count() == unavailable_count


@override_settings(PTI_START_DATE=datetime(2021, 4, 1))
def test_get_compliant_timetables_all_compliant():
    compliant_datasets = 5
    DatasetRevisionFactory.create_batch(
        compliant_datasets,
        dataset__dataset_type=TimetableType,
        is_published=True,
        url_link=FAKER.uri(),
        created=datetime(2021, 5, 1, tzinfo=pytz.utc),
    )
    datasets = Dataset.objects.get_compliant_timetables()
    assert datasets.count() == compliant_datasets


@override_settings(PTI_START_DATE=datetime(2021, 4, 1))
def test_get_compliant_timetables_mixed():
    compliant_datasets_count = 5
    DatasetRevisionFactory.create_batch(
        compliant_datasets_count,
        dataset__dataset_type=TimetableType,
        is_published=True,
        url_link=FAKER.uri(),
        created=datetime(2021, 5, 1, tzinfo=pytz.utc),
    )

    pre_pti_datasets = 2
    DatasetRevisionFactory.create_batch(
        pre_pti_datasets,
        dataset__dataset_type=TimetableType,
        is_published=True,
        url_link=FAKER.uri(),
        created=datetime(2021, 3, 1, tzinfo=pytz.utc),
    )

    non_compliant_datasets_count = 3
    for _ in range(non_compliant_datasets_count):
        revision = DatasetRevisionFactory(
            dataset__dataset_type=TimetableType, is_published=True, url_link=FAKER.uri()
        )
        PTIObservationFactory(revision=revision)

    all_datasets = Dataset.objects.all()
    total_dataset_count = (
        compliant_datasets_count + non_compliant_datasets_count + pre_pti_datasets
    )
    assert all_datasets.count() == total_dataset_count

    datasets = Dataset.objects.get_compliant_timetables()
    assert datasets.count() == compliant_datasets_count


def test_add_latest_task_progress_status():
    """
    Given a revision with multiple DatasetETLTaskResults
    When calling add_latest_task_status and add_latest_task_progress
    Then the revision should be annotated with the status and progress of the
    latest DatasetETLTaskResult (i.e. the one with the largest created datetime)
    """
    revision = DatasetRevisionFactory()
    for days in range(4, 1):
        created = now() - timedelta(days=days)
        DatasetETLTaskResultFactory(
            revision=revision,
            progress=100,
            status=DatasetETLTaskResult.SUCCESS,
            created=created,
        )
    DatasetETLTaskResultFactory(
        revision=revision,
        progress=45,
        status=DatasetETLTaskResult.PENDING,
        created=now(),
    )

    revisions = (
        DatasetRevision.objects.add_latest_task_progress().add_latest_task_status()
    )

    assert revisions.last().latest_task_progress == 45
    assert revisions.last().latest_task_status == DatasetETLTaskResult.PENDING


def test_get_stuck_timetables():
    """
    Given a set of revisions in the "stuck" and "unstuck" state.
    When calling the get_stuck_revisions queryset method.
    Then only return timetables that are stuck (i.e. `latest_task_progress` less
    than 99%, `latest_task_status` not SUCCESS/FAILURE and `created` over a day ago.)
    """
    created = datetime(2021, 1, 1, 12, 12, 12, tzinfo=pytz.utc)
    success_revision = DatasetRevisionFactory(
        dataset__dataset_type=TimetableType, created=created
    )
    DatasetETLTaskResultFactory(
        revision=success_revision, progress=100, status=DatasetETLTaskResult.SUCCESS
    )
    failed_revision = DatasetRevisionFactory(
        dataset__dataset_type=TimetableType, created=created
    )
    DatasetETLTaskResultFactory(
        revision=failed_revision, progress=30, status=DatasetETLTaskResult.FAILURE
    )
    stuck_revision = DatasetRevisionFactory(
        dataset__dataset_type=TimetableType, created=created
    )
    DatasetETLTaskResultFactory(
        revision=stuck_revision, progress=35, status=DatasetETLTaskResult.PENDING
    )

    stuck_revisions = DatasetRevision.objects.get_stuck_revisions()

    assert stuck_revisions.count() == 1
    assert stuck_revisions.last() == stuck_revision
