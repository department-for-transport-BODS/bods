from datetime import datetime, timedelta

import pytest
import pytz
from django.utils.timezone import now
from django_hosts import reverse
from freezegun import freeze_time

from config import hosts
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
    OrganisationFactory,
)
from transit_odp.organisation.models import Dataset, DatasetRevision, Organisation
from transit_odp.pipelines.factories import DatasetETLTaskResultFactory
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.transmodel.factories import ServicePatternFactory
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


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

        assert fetched_org.published_avl_count is None
        assert fetched_org.published_fares_count == 1
        assert fetched_org.published_timetable_count == 1


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
