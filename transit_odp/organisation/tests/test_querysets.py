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
    ERROR,
    EXPIRED,
    INACTIVE,
    LIVE,
    ORG_ACTIVE,
    ORG_INACTIVE,
    ORG_NOT_YET_INVITED,
    ORG_PENDING_INVITE,
    AVLType,
    FaresType,
    FeedStatus,
    TimetableType,
)
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    ConsumerFeedbackFactory,
    DatasetFactory,
    DatasetRevisionFactory,
    FaresDatasetRevisionFactory,
    LicenceFactory,
    OrganisationFactory,
    TXCFileAttributesFactory,
)
from transit_odp.organisation.models import (
    ConsumerFeedback,
    Dataset,
    DatasetRevision,
    Organisation,
    TXCFileAttributes,
)
from transit_odp.organisation.querysets import ANONYMOUS, DATASET_LEVEL, GENERAL_LEVEL
from transit_odp.otc.factories import LicenceModelFactory, ServiceModelFactory
from transit_odp.pipelines.factories import (
    DatasetETLTaskResultFactory,
    RemoteDatasetHealthCheckCountFactory,
)
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.transmodel.factories import ServicePatternFactory
from transit_odp.users.constants import AccountType, OrgAdminType, OrgStaffType
from transit_odp.users.factories import InvitationFactory, UserFactory
from transit_odp.users.models import User

pytestmark = pytest.mark.django_db

FAKER = faker.Faker()


class TestOrganisationQuerySet:
    # TODO - test add_org_admin_count
    # TODO - test add_org_staff_count

    def test_is_abods_organisation(self):
        abods_organisation = OrganisationFactory(
            is_abods_global_viewer=True, name="dummy_aboads_org", short_name="dummy org"
        )
        assert abods_organisation.is_abods_global_viewer == True
        assert abods_organisation.name == "dummy_aboads_org"

        bods_organisation = OrganisationFactory(
            name="dummy_bods_org", short_name="dummy org"
        )
        assert bods_organisation.is_abods_global_viewer == False
        assert bods_organisation.name == "dummy_bods_org"

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

    def test_add_licence_string(self):
        org = OrganisationFactory(licence_required=True)
        licences = LicenceFactory.create_batch(3, organisation=org)
        expected_licence_string = ":".join([lic.number for lic in licences])

        org_qs = Organisation.objects.add_licence_string(delimiter=":")
        org1 = org_qs.first()
        assert org1.licence_string == expected_licence_string

    def test_number_of_licences(self):
        org = OrganisationFactory(licence_required=True)
        num_licences = 3
        LicenceFactory.create_batch(num_licences, organisation=org)

        org_qs = Organisation.objects.add_number_of_licences()
        org1 = org_qs.first()
        assert org1.number_of_licences == num_licences

    def test_add_permit_holder(self):
        unlicensed_org = OrganisationFactory(licence_required=False)
        licensed_org = OrganisationFactory(licence_required=True)
        LicenceFactory.create_batch(3, organisation=licensed_org)
        undecided_org = OrganisationFactory()

        orgs = Organisation.objects.add_permit_holder()
        assert orgs.get(id=unlicensed_org.id).permit_holder == "FALSE"
        assert orgs.get(id=licensed_org.id).permit_holder == "TRUE"
        assert orgs.get(id=undecided_org.id).permit_holder == "UNKNOWN"

    def test_add_total_number_of_subscriptions(self):
        org = OrganisationFactory()
        tom = UserFactory()
        dick = UserFactory()
        harry = UserFactory()

        DatasetFactory(organisation=org, subscribers=[tom, dick])
        DatasetFactory(organisation=org, subscribers=[tom, harry])

        org = Organisation.objects.add_total_subscriptions().first()

        assert org.total_subscriptions == 4

    @pytest.mark.parametrize(
        ("is_active", "accounts_type", "expected"),
        [
            (False, [], ORG_NOT_YET_INVITED),
            (
                False,
                [
                    OrgAdminType,
                ],
                ORG_PENDING_INVITE,
            ),
            (False, [OrgAdminType, OrgStaffType], ORG_INACTIVE),
            (True, [OrgAdminType, OrgStaffType], ORG_ACTIVE),
        ],
    )
    def test_statuses(self, is_active, accounts_type, expected):
        org = OrganisationFactory.create(is_active=is_active)
        organisations = (org,) if expected != ORG_PENDING_INVITE else None
        for account_type in accounts_type:
            inviter = UserFactory(
                account_type=account_type, organisations=organisations
            )
            InvitationFactory.create(
                organisation=org, account_type=OrgAdminType, inviter=inviter
            )

        assert org.get_status() == expected

    def test_get_organisation_name(self):
        licence_number = "PD0000099"
        otc_operator_name = "test_org_1"
        num_otc_services = 10
        service_codes = [f"{licence_number}:{n}" for n in range(num_otc_services)]
        service_numbers = [f"Line{n}" for n in range(num_otc_services)]

        org1 = OrganisationFactory(name="test_org_1")
        LicenceFactory(organisation=org1, number=licence_number)
        otc_lic = LicenceModelFactory(number=licence_number)
        ServiceModelFactory(
            licence=otc_lic,
            registration_number=service_codes[0],
            service_number=service_numbers[0],
        )

        operator_name = Organisation.objects.get_organisation_name(licence_number)
        assert operator_name == otc_operator_name


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
            "name": "DATASET_LEVEL 1 LIVE REVISION",
            "dataset": datasets[0],
            "is_published": True,
        },
        # dataset 2 has a live + draft revision
        {
            "created": now - timedelta(hours=6),
            "name": "DATASET_LEVEL 2 LIVE REVISION",
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
                    assert (
                        dataset._live_revision[0].name
                        == "DATASET_LEVEL 1 LIVE REVISION"
                    )
                elif dataset.id == datasets[1].id:
                    assert (
                        dataset._live_revision[0].name
                        == "DATASET_LEVEL 2 LIVE REVISION"
                    )
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

    def test_get_only_active_datasets_bulk_archive(self):
        """
        Tests queryset is filtered to exclude datasets which have an inactive status
        """
        datasets = DatasetFactory.create_batch(2, live_revision=None)
        DatasetRevisionFactory(
            dataset=datasets[0], is_published=True, status=FeedStatus.live.value
        )
        DatasetRevisionFactory(
            dataset=datasets[1], is_published=True, status=FeedStatus.inactive.value
        )
        qs = Dataset.objects.get_only_active_datasets_bulk_archive()
        assert len(qs) == 1
        assert qs[0].id != datasets[1].id
        assert qs[0].id == datasets[0].id

    def test_search(self):
        """Tests queryset is filtered using keywords to search on live_revision's
        related transmodel entities and dataset attributes.
        """
        admin_areas = [
            AdminAreaFactory(name=name) for name in ["Cambridge", "London", "Leeds"]
        ]
        org_name_to_noc = {"OrgX": ["alpha", "bravo"], "OrgY": ["gamma", "delta"]}
        organisations = [
            OrganisationFactory(name=name, nocs=org_name_to_noc[name])
            for name in org_name_to_noc.keys()
        ]
        datasets = [
            DatasetFactory(organisation=organisation, live_revision=None)
            for organisation in organisations
        ]
        revision = DatasetRevisionFactory(
            dataset=datasets[0],
            name="DatasetP",
            description="Descriptive",
            admin_areas=admin_areas[:1],
            is_published=True,
        )
        stops = [StopPointFactory(admin_area=admin_areas[0])]
        FaresMetadataFactory(revision=revision, stops=stops)

        revision = DatasetRevisionFactory(
            dataset=datasets[1],
            name="DatasetQ",
            description="",
            admin_areas=admin_areas[1:],
            is_published=True,
        )
        stops = [
            StopPointFactory(admin_area=admin_area) for admin_area in admin_areas[1:]
        ]
        FaresMetadataFactory(revision=revision, stops=stops)

        qs = Dataset.objects.search("Lon")
        assert len(qs) == 1
        assert qs[0] == datasets[1]

        qs = Dataset.objects.search("org")
        assert len(qs) == 2

        qs = Dataset.objects.search("Descriptive")
        assert len(qs) == 1
        assert qs[0] == datasets[0]

        qs = Dataset.objects.search("bravo")
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

    def test_get_viewable_statuses(self):
        """
        GIVEN a set of Timetables with various statuses, live, inactive, expired and
        error.
        WHEN calling get_viewable_statuses
        THEN only timetables with the live and inactive statuses will be returned.
        """
        live_count = 4
        DatasetRevisionFactory.create_batch(live_count, status=LIVE)
        inactive_count = 3
        DatasetRevisionFactory.create_batch(inactive_count, status=INACTIVE)

        DatasetRevisionFactory.create_batch(2, status=ERROR)
        DatasetRevisionFactory.create_batch(4, status=EXPIRED)

        datasets = Dataset.objects.get_viewable_statuses().select_related(
            "live_revision"
        )
        assert datasets.count() == live_count + inactive_count
        for dataset in datasets:
            assert dataset.live_revision.status in [LIVE, INACTIVE]

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

    def test_add_profile_nocs(self):
        org = OrganisationFactory(nocs=["test1", "test2", "test3"])
        DatasetFactory(organisation=org)

        result = Dataset.objects.add_profile_nocs("; ").first()
        assert result.profile_nocs == "test1; test2; test3"

    def test_add_live_name(self):
        name = "dataset name"
        DatasetRevisionFactory(name=name)

        result = Dataset.objects.add_live_name().first()
        assert result.name == name

    def test_add_live_filename(self):
        name = "dataset.xml"
        DatasetRevisionFactory(upload_file=name)
        result = Dataset.objects.add_live_filename().first()
        assert result.upload_filename == name

    @pytest.mark.parametrize(
        "status, expected",
        [("live", "published"), ("inactive", "inactive"), ("expired", "expired")],
    )
    def test_add_pretty_status(self, status, expected):
        DatasetRevisionFactory(status=status)
        result = Dataset.objects.add_pretty_status().first()
        assert result.status == expected

    @pytest.mark.parametrize(
        "status, expected",
        [("live", "published"), ("inactive", "inactive"), ("error", "published")],
    )
    def test_add_pretty_status_for_avl(self, status, expected):
        AVLDatasetRevisionFactory(status=status)
        result = Dataset.objects.add_pretty_status().first()
        assert result.status == expected

    @pytest.mark.parametrize(
        "dataset_type, expected",
        [
            (TimetableType, "Timetables"),
            (AVLType, "Automatic Vehicle Locations"),
            (FaresType, "Fares"),
        ],
    )
    def test_add_pretty_dataset_type(self, dataset_type, expected):
        DatasetRevisionFactory(dataset__dataset_type=dataset_type)
        result = Dataset.objects.add_pretty_dataset_type().first()
        assert result.dataset_type_pretty == expected

    def test_add_last_updated_including_avl(self):
        past = datetime(2020, 12, 25)
        current = now()
        DatasetRevisionFactory(
            dataset__dataset_type=TimetableType, published_at=current
        )
        DatasetRevisionFactory(
            dataset__dataset_type=AVLType,
            published_at=past,
            dataset__avl_feed_last_checked=current,
        )
        results = Dataset.objects.add_last_updated_including_avl()
        for result in results:
            assert result.last_updated == current

    def test_add_last_published_by_email(self):
        org_user1 = UserFactory()
        # First revision, published by org_user1
        first_revision = DatasetRevisionFactory(published_by=org_user1)
        dataset = first_revision.dataset
        org_user2 = UserFactory()
        # Second revision, published by org_user2
        DatasetRevisionFactory(dataset=dataset, published_by=org_user2)
        # Third revision, draft by org_user1
        DatasetRevisionFactory(
            dataset=dataset,
            published_by=org_user1,
            is_published=False,
            status=FeedStatus.draft.value,
        )
        # Fourth revision, published by system (no user)
        DatasetRevisionFactory(dataset=dataset, published_by=None)
        results = Dataset.objects.add_last_published_by_email()
        assert results.first().last_published_by_email == org_user2.email


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


class TestTXCFileAttributesQueryset:
    def test_get_active_live_revisions(self):
        """
        Given we have datasets with multiple previously published revisions
        and therefore txc file attributes
        When we apply the queryset method
        Then we filter out file attributes that do not belong to a live revision
        """

        for _ in range(5):
            dataset = DatasetFactory(live_revision=None)
            for _ in range(3):
                r = DatasetRevisionFactory(dataset=dataset)
                TXCFileAttributesFactory(revision=r)

            latest_revision = DatasetRevisionFactory(dataset=dataset)
            TXCFileAttributesFactory(revision=latest_revision, origin="latest")

        file_attributes = TXCFileAttributes.objects.get_active_live_revisions()
        assert file_attributes.count() == 5
        for fa in file_attributes:
            assert fa.origin == "latest"

    def test_service_code_in_multiple_datasets(self):
        """
        Given we have a service code that is shared across multiple datasets
        When we apply the queryset method get_active_txc_files
        Then we pick the txc attribute (service_code) that belongs to the latest
        dataset
        """

        for number in range(3):
            service_code = f"PF0000{number}"
            revision = DatasetRevisionFactory(name=f"old{number}", is_published=True)
            TXCFileAttributesFactory(revision=revision, service_code=service_code)
            revision = DatasetRevisionFactory(name=f"new{number}", is_published=True)
            TXCFileAttributesFactory(revision=revision, service_code=service_code)

        file_attributes = TXCFileAttributes.objects.get_active_txc_files()
        assert file_attributes.count() == 3
        for fa in file_attributes:
            assert fa.revision.name[:3] == "new"

    def test_repeating_service_codes_in_same_dataset_higher_revision(self):
        """
        Given we have a service code that is shared across multiple TxC files in the
        same dataset when we apply the queryset method get_active_txc_files
        Then we pick the txc attribute (service_code) that belongs to the latest
        revision_number, modification_datetime, latest operating_period_start_date
        and finally sorted by filename in descending order
        """

        for number in range(3):
            service_code = f"PF0000{number}"
            revision = DatasetRevisionFactory(name=f"old{number}", is_published=True)
            TXCFileAttributesFactory(
                revision=revision,
                revision_number=2,
                service_code=service_code,
                modification_datetime=datetime(2022, 10, 26, 0, 0, tzinfo=pytz.UTC),
                operating_period_start_date=datetime(2020, 12, 25, 0, 0),
            )
            TXCFileAttributesFactory(
                revision=revision,
                revision_number=1,
                service_code=service_code,
                modification_datetime=datetime(2022, 10, 23, 0, 0, tzinfo=pytz.UTC),
                operating_period_start_date=datetime(2021, 1, 1, 0, 0),
            )

        file_attributes = TXCFileAttributes.objects.get_active_txc_files()
        assert file_attributes.count() == 3
        for fa in file_attributes:
            assert fa.revision_number == 2
            assert fa.modification_datetime == datetime(
                2022, 10, 26, 0, 0, tzinfo=pytz.UTC
            )
            assert fa.operating_period_start_date == datetime(2020, 12, 25, 0, 0).date()

    def test_repeating_service_codes_in_same_dataset_higher_modification_dt(self):
        """
        Given we have a service code that is shared across multiple TxC files in the
        same dataset when we apply the queryset method get_active_txc_files
        Then we pick the txc attribute (service_code) that belongs to the latest
        revision_number, modification_datetime, latest operating_period_start_date
        and finally sorted by filename in descending order
        """
        for number in range(3):
            service_code = f"PF0000{number}"
            revision = DatasetRevisionFactory(name=f"old{number}", is_published=True)
            TXCFileAttributesFactory(
                revision=revision,
                revision_number=2,
                service_code=service_code,
                modification_datetime=datetime(2022, 10, 26, 0, 0, tzinfo=pytz.UTC),
                operating_period_start_date=datetime(2020, 12, 25, 0, 0),
            )
            TXCFileAttributesFactory(
                revision=revision,
                revision_number=2,
                service_code=service_code,
                modification_datetime=datetime(2022, 10, 23, 0, 0, tzinfo=pytz.UTC),
                operating_period_start_date=datetime(2021, 1, 1, 0, 0),
            )

        file_attributes = TXCFileAttributes.objects.get_active_txc_files()
        assert file_attributes.count() == 3
        for fa in file_attributes:
            assert fa.revision_number == 2
            assert fa.modification_datetime == datetime(
                2022, 10, 26, 0, 0, tzinfo=pytz.UTC
            )
            assert fa.operating_period_start_date == datetime(2020, 12, 25, 0, 0).date()

    def test_repeating_service_codes_in_same_dataset_all_same_sort_by_filename(self):
        """
        Given we have a service code that is shared across multiple TxC files in the
        same dataset when we apply the queryset method get_active_txc_files
        Then we pick the txc attribute (service_code) that belongs to the latest
        revision_number, modification_datetime, latest operating_period_start_date
        and finally sorted by filename in descending order
        """
        for number in range(3):
            service_code = f"PF0000{number}"
            revision = DatasetRevisionFactory(name=f"old{number}", is_published=True)
            TXCFileAttributesFactory(
                revision=revision,
                revision_number=3,
                service_code=service_code,
                modification_datetime=datetime(2022, 10, 23, 0, 0, tzinfo=pytz.UTC),
                operating_period_start_date=datetime(2021, 1, 1, 0, 0),
                filename="AMSY_32S_AMSYPC00011412032_20230108_-_4cd2921b-0bd5-4e9b-8fcf-9706375c8375.xml",
            )
            TXCFileAttributesFactory(
                revision=revision,
                revision_number=3,
                service_code=service_code,
                modification_datetime=datetime(2022, 10, 23, 0, 0, tzinfo=pytz.UTC),
                operating_period_start_date=datetime(2021, 1, 1, 0, 0),
                filename="AMSY_32S_AMSYPC00011412032_20230108_-_c033128f-cffd-4e45-a78d-f0ff648957bc.xml",
            )

        file_attributes = TXCFileAttributes.objects.get_active_txc_files()
        assert file_attributes.count() == 3
        for fa in file_attributes:
            assert fa.revision_number == 3
            assert fa.modification_datetime == datetime(
                2022, 10, 23, 0, 0, tzinfo=pytz.UTC
            )
            assert fa.operating_period_start_date == datetime(2021, 1, 1, 0, 0).date()
            assert (
                fa.filename
                == "AMSY_32S_AMSYPC00011412032_20230108_-_c033128f-cffd-4e45-a78d-f0ff648957bc.xml"
            )


class TestConsumerFeedbackQuerySet:
    def test_anon_consumer_details(self):
        ConsumerFeedbackFactory(consumer=None)
        feedback = ConsumerFeedback.objects.add_consumer_details().first()
        assert feedback.username == ANONYMOUS
        assert feedback.email == ANONYMOUS

    def test_consumer_details(self):
        ConsumerFeedbackFactory()
        feedback = ConsumerFeedback.objects.add_consumer_details().first()
        consumer = User.objects.first()
        assert feedback.username == consumer.username
        assert feedback.email == consumer.email

    @pytest.mark.parametrize(
        "factory,expected",
        [
            (DatasetRevisionFactory, "Timetables"),
            (AVLDatasetRevisionFactory, "Automatic Vehicle Locations"),
            (FaresDatasetRevisionFactory, "Fares"),
        ],
    )
    def test_add_dataset_type(self, factory, expected):
        revision = factory()
        ConsumerFeedbackFactory(dataset=revision.dataset)
        feedback = ConsumerFeedback.objects.add_dataset_type().first()
        assert feedback.dataset_type == expected

    def test_add_feedback_type_dataset_level(self):
        ConsumerFeedbackFactory()
        feedback = ConsumerFeedback.objects.add_feedback_type().first()
        assert feedback.feedback_type == DATASET_LEVEL

    def test_add_feedback_type_general_level(self):
        ConsumerFeedbackFactory(dataset=None)
        feedback = ConsumerFeedback.objects.add_feedback_type().first()
        assert feedback.feedback_type == GENERAL_LEVEL

    def test_consumer_counts_per_day(self):
        """
        Create feedback objects so we have 1 on day 1 2 on day 2 3 on day 3 ...
        then add 1 feedback to all datasets so the counts look like this:
        7,7,7,7,7,7,7  6,6,6,6,6,6  5,5,5,5,5  4,4,4,4  3,3,3  2,2 1
        Also include general feedback for completeness
        """
        timenow = now()
        for counter in range(7):
            dataset = DatasetFactory()
            with freeze_time(timenow - timedelta(days=counter)):
                ConsumerFeedbackFactory.create_batch(counter, dataset=dataset)
                ConsumerFeedbackFactory(dataset=None)

        # This happens "today" so should be counted in all totals
        for dataset in Dataset.objects.all():
            ConsumerFeedbackFactory(dataset=dataset)

        feedback = (
            ConsumerFeedback.objects.add_date()
            .exclude(dataset_id=None)
            .add_total_issues_per_dataset()
            .order_by("-count")
            .values_list("count", flat=True)
        )
        expected = []
        for i in range(7, 0, -1):
            expected += [i] * i

        assert list(feedback) == expected
