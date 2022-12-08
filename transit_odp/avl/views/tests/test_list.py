import re
from datetime import date, timedelta

import pytest
from django.db.models.fields import timezone
from django_hosts.resolvers import reverse

import config.hosts
from transit_odp.avl.constants import MORE_DATA_NEEDED, UNDERGOING
from transit_odp.avl.factories import PostPublishingCheckReportFactory
from transit_odp.avl.models import PPCReportType
from transit_odp.organisation.constants import INACTIVE, AVLType
from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetRevisionFactory,
    DraftDatasetFactory,
    OrganisationFactory,
)
from transit_odp.users.factories import OrgStaffFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def sample_data():
    num_datasets = 10
    organisation = OrganisationFactory()
    user = OrgStaffFactory(organisations=(organisation,))
    datasets = DatasetFactory.create_batch(
        num_datasets,
        organisation=organisation,
        dataset_type=AVLType,
    )
    return datasets, user, organisation


class TestAVLListView:
    host = config.hosts.PUBLISH_HOST

    def test_overall_ppc_score(self, client_factory, sample_data):
        """
        GIVEN : some AVL datasets, a tuple of
                vehicle_activities_analysed, and a tuple of
                vehicle_activities_completely_matching we can calculate
                the tuple of scores  and its average

        WHEN  : the PostPublishingCheckReport has been created with the
                1. dataset
                2. vehicle_activities_analysed
                3. vehicle_activities_completely_matching
                4. date

        THEN  : the view should display the ppc overall score and this
                number should be the same of the average calculated in
                GIVEN rounded at the 2nd decimal
        """
        num_matching = [1, 3, 9, 18, 2, 3, 4, 0, 5, 0]
        num_analysed = [2, 4, 10, 20, 6, 7, 5, 3, 5, 10]
        mean = (
            100
            * sum([r[0] / r[1] for r in zip(num_matching, num_analysed)])
            / len(num_matching)
        )

        created_at = timezone.now() - timedelta(days=5)
        datasets, user, organisation = sample_data
        for i, dataset in enumerate(datasets):
            PostPublishingCheckReportFactory(
                dataset=dataset,
                vehicle_activities_analysed=num_analysed[i],
                vehicle_activities_completely_matching=num_matching[i],
                granularity=PPCReportType.WEEKLY,
                created=created_at,
            )

        client = client_factory(host=self.host)
        client.force_login(user=user)
        url = reverse("avl:feed-list", args=[organisation.id], host=self.host)
        response = client.get(url)

        assert round(response.context_data["overall_ppc_score"], 2) == round(mean, 2)

    def test_overall_ppc_score_no_vehicles(self, client_factory, sample_data):
        """
        GIVEN : some AVL datasets

        WHEN  : the PostPublishingCheckReport has been created with the
                1. dataset
                2. vehicle_activities_analysed = None
                3. vehicle_activities_completely_matching = None

        THEN  : the ppc overall should be None
        """
        datasets, user, organisation = sample_data
        for dataset in datasets:
            PostPublishingCheckReportFactory(
                dataset=dataset,
                granularity=PPCReportType.WEEKLY,
                vehicle_activities_analysed=0,
                vehicle_activities_completely_matching=0,
            )
        client = client_factory(host=self.host)
        client.force_login(user=user)
        url = reverse("avl:feed-list", args=[organisation.id], host=self.host)
        response = client.get(url)
        assert response.context_data["overall_ppc_score"] is None

    def test_overall_ppc_score_different_statuses(self, client_factory):
        """
        GIVEN : some AVL datasets with draft, published and inactive status

        WHEN  : the PostPublishingCheckReport has been created with the
                1. dataset
                2. vehicle_activities_analysed
                3. vehicle_activities_completely_matching

        THEN  : the ppc overall score should be based on the published dataset only
        """
        organisation = OrganisationFactory()
        user = OrgStaffFactory(organisations=(organisation,))
        today = date.today()
        dataset = DraftDatasetFactory(
            organisation=organisation,
            contact=user,
            dataset_type=AVLType,
        )
        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=10,
            vehicle_activities_completely_matching=1,
            granularity=PPCReportType.WEEKLY,
            created=today,
        )

        dataset = DatasetFactory(
            organisation=organisation,
            contact=user,
            dataset_type=AVLType,
        )
        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=10,
            vehicle_activities_completely_matching=2,
            granularity=PPCReportType.WEEKLY,
            created=today,
        )

        dataset_revision = DatasetRevisionFactory(
            dataset__dataset_type=AVLType,
            dataset__organisation=organisation,
            dataset__contact=user,
            status=INACTIVE,
        )
        PostPublishingCheckReportFactory(
            dataset=dataset_revision.dataset,
            vehicle_activities_analysed=10,
            vehicle_activities_completely_matching=4,
            granularity=PPCReportType.WEEKLY,
            created=today,
        )

        client = client_factory(host=self.host)
        client.force_login(user=user)
        url = reverse("avl:feed-list", args=[organisation.id], host=self.host)
        response = client.get(url)
        expected_score = 100 * 2 / 10
        assert round(response.context_data["overall_ppc_score"], 0) == round(
            expected_score, 0
        )

    def test_overall_ppc_score_report_selection(self, client_factory):
        """
        GIVEN : an AVL dataset with multiple weekly and daily reports
        THEN  : the ppc overall score should come from the latest weekly report
        """
        organisation = OrganisationFactory()
        user = OrgStaffFactory(organisations=(organisation,))
        today = date.today()
        dataset = DatasetFactory(
            organisation=organisation,
            dataset_type=AVLType,
        )
        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=10,
            vehicle_activities_completely_matching=1,
            granularity=PPCReportType.DAILY,
            created=today,
        )
        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=10,
            vehicle_activities_completely_matching=2,
            granularity=PPCReportType.DAILY,
            created=today - timedelta(days=1),
        )

        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=10,
            vehicle_activities_completely_matching=4,
            granularity=PPCReportType.WEEKLY,
            created=today - timedelta(days=1),
        )

        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=10,
            vehicle_activities_completely_matching=8,
            granularity=PPCReportType.WEEKLY,
            created=today - timedelta(days=8),
        )

        client = client_factory(host=self.host)
        client.force_login(user=user)
        url = reverse("avl:feed-list", args=[organisation.id], host=self.host)
        response = client.get(url)
        expected_score = 100 * 4 / 10
        assert round(response.context_data["overall_ppc_score"], 0) == round(
            expected_score, 0
        )

    def test_overall_ppc_score_new_dataset_ignored(self, client_factory):
        """
        GIVEN : an AVL dataset with multiple weekly and daily reports
        THEN  : the ppc overall score should come from the latest weekly report
        """
        organisation = OrganisationFactory()
        user = OrgStaffFactory(organisations=(organisation,))
        today = date.today()

        dataset = DatasetFactory(
            organisation=organisation,
            dataset_type=AVLType,
        )
        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=10,
            vehicle_activities_completely_matching=1,
            granularity=PPCReportType.WEEKLY,
            created=today,
        )

        dataset = DatasetFactory(
            organisation=organisation,
            dataset_type=AVLType,
        )
        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=10,
            vehicle_activities_completely_matching=2,
            granularity=PPCReportType.DAILY,
            created=today,
        )

        client = client_factory(host=self.host)
        client.force_login(user=user)
        url = reverse("avl:feed-list", args=[organisation.id], host=self.host)
        response = client.get(url)
        expected_score = 100 * 1 / 10
        assert round(response.context_data["overall_ppc_score"], 0) == round(
            expected_score, 0
        )

    def test_overall_ppc_score_datafeed_unavailable(self, client_factory):
        """
        GIVEN : an AVL dataset with multiple weekly and daily reports
        THEN  : the ppc overall score should come from the latest weekly report
        """
        organisation = OrganisationFactory()
        user = OrgStaffFactory(organisations=(organisation,))
        today = date.today()

        dataset = DatasetFactory(
            organisation=organisation,
            dataset_type=AVLType,
        )
        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=10,
            vehicle_activities_completely_matching=1,
            granularity=PPCReportType.WEEKLY,
            created=today,
        )

        dataset = DatasetFactory(
            organisation=organisation,
            dataset_type=AVLType,
            avl_compliance_cached__status=MORE_DATA_NEEDED,
        )
        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=10,
            vehicle_activities_completely_matching=2,
            granularity=PPCReportType.WEEKLY,
            created=today,
        )

        client = client_factory(host=self.host)
        client.force_login(user=user)
        url = reverse("avl:feed-list", args=[organisation.id], host=self.host)
        response = client.get(url)
        expected_score = 100 * 1 / 10
        assert round(response.context_data["overall_ppc_score"], 0) == round(
            expected_score, 0
        )

    def test_table_ppc_score_typical(self, client_factory):
        organisation = OrganisationFactory()
        user = OrgStaffFactory(organisations=(organisation,))
        today = date.today()

        dataset = DatasetFactory(
            organisation=organisation,
            dataset_type=AVLType,
        )
        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=10,
            vehicle_activities_completely_matching=1,
            granularity=PPCReportType.WEEKLY,
            created=today,
        )
        expected_score = "10%"

        client = client_factory(host=self.host)
        client.force_login(user=user)
        url = reverse("avl:feed-list", args=[organisation.id], host=self.host)
        response = client.get(url)
        table = response.context["table"]
        assert len(table.rows) == 1
        row = table.rows[0]
        assert row.get_cell("percent_matching") == expected_score

    def test_table_ppc_score_zero_matching(self, client_factory):
        organisation = OrganisationFactory()
        user = OrgStaffFactory(organisations=(organisation,))
        today = date.today()

        dataset = DatasetFactory(
            organisation=organisation,
            dataset_type=AVLType,
        )
        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=10,
            vehicle_activities_completely_matching=0,
            granularity=PPCReportType.WEEKLY,
            created=today,
        )
        expected_score = "0%"

        client = client_factory(host=self.host)
        client.force_login(user=user)
        url = reverse("avl:feed-list", args=[organisation.id], host=self.host)
        response = client.get(url)
        table = response.context["table"]
        assert len(table.rows) == 1
        row = table.rows[0]
        assert row.get_cell("percent_matching") == expected_score

    def test_table_ppc_score_zero_analysed(self, client_factory):
        organisation = OrganisationFactory()
        user = OrgStaffFactory(organisations=(organisation,))
        today = date.today()

        dataset = DatasetFactory(
            organisation=organisation,
            dataset_type=AVLType,
        )
        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=0,
            vehicle_activities_completely_matching=0,
            granularity=PPCReportType.WEEKLY,
            created=today,
        )
        expected_score = UNDERGOING

        client = client_factory(host=self.host)
        client.force_login(user=user)
        url = reverse("avl:feed-list", args=[organisation.id], host=self.host)
        response = client.get(url)
        table = response.context["table"]
        assert len(table.rows) == 1
        row = table.rows[0]
        assert row.get_cell("percent_matching") == expected_score

    def test_table_ppc_score_none(self, client_factory):
        organisation = OrganisationFactory()
        user = OrgStaffFactory(organisations=(organisation,))

        DatasetFactory(
            organisation=organisation,
            dataset_type=AVLType,
        )
        expected_score = UNDERGOING

        client = client_factory(host=self.host)
        client.force_login(user=user)
        url = reverse("avl:feed-list", args=[organisation.id], host=self.host)
        response = client.get(url)
        table = response.context["table"]
        assert len(table.rows) == 1
        row = table.rows[0]
        assert row.get_cell("percent_matching") == expected_score

    def test_table_ppc_score_dormant(self, client_factory):
        organisation = OrganisationFactory()
        user = OrgStaffFactory(organisations=(organisation,))
        today = date.today()

        dataset = DatasetFactory(
            organisation=organisation,
            dataset_type=AVLType,
            avl_compliance_cached__status=MORE_DATA_NEEDED,
        )
        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=10,
            vehicle_activities_completely_matching=1,
            granularity=PPCReportType.WEEKLY,
            created=today,
        )
        expected_score = MORE_DATA_NEEDED

        client = client_factory(host=self.host)
        client.force_login(user=user)
        url = reverse("avl:feed-list", args=[organisation.id], host=self.host)
        response = client.get(url)
        table = response.context["table"]
        assert len(table.rows) == 1
        row = table.rows[0]
        assert row.get_cell("percent_matching") == expected_score


class TestAVLFeedMatchingView:
    host = config.hosts.PUBLISH_HOST

    @pytest.mark.parametrize(
        """vehicle_activities_analysed,
         vehicle_activities_completely_matching,
         granularity,
         expected""",
        (
            (10, 10, PPCReportType.WEEKLY, "100%"),
            (654, 543, PPCReportType.WEEKLY, str(round(543 / 654.0 * 100)) + "%"),
            (234, 0, PPCReportType.WEEKLY, "0%"),
            (344, 322, PPCReportType.DAILY, None),
        ),
    )
    def test_each_feed_ppc_score(
        self,
        client_factory,
        vehicle_activities_analysed,
        vehicle_activities_completely_matching,
        granularity,
        expected,
    ):
        """
        GIVEN : an AVL dataset

        WHEN  : the PostPublishingCheckReport has been created with
                different data to test different scenario
                1. ppc score 100%
                2. ppc score created less then 100%
                3. vehicle_activities_completely_matching = 0 -> 0%
                4. not in database e.g. granularity = daily

        THEN  : the view should display the ppc score for each dataset
                according with the case in WHEN
        """
        organisation = OrganisationFactory()
        user = OrgStaffFactory(organisations=(organisation,))
        today = date.today()
        dataset = DatasetFactory(organisation=organisation, dataset_type=AVLType)
        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=vehicle_activities_analysed,
            vehicle_activities_completely_matching=(
                vehicle_activities_completely_matching
            ),
            granularity=granularity,
            created=today,
        )
        client = client_factory(host=self.host)
        client.force_login(user=user)
        url = reverse(
            "avl:feed-detail", args=(organisation.id, dataset.id), host=self.host
        )
        response = client.get(url)
        assert (
            response.context_data["properties"]["avl_timetables_matching"] == expected
        )

    def test_feed_more_data_needed(self, client_factory):
        """
        GIVEN : an AVL dataset with avl_compliance_cached__status =
                'Unavailable due to dormant feed' (MORE_DATA_NEEDED)

        WHEN  : An invalid PostPublishingCheckReport has been created with
                1. dataset created in GIVEN
                2. granularity = daily

        THEN  : the view should display the table with 2 rows with
                'Unavailable due to dormant feed'
        """
        organisation = OrganisationFactory()
        user = OrgStaffFactory(organisations=(organisation,))
        today = date.today()
        dataset = DatasetFactory(
            organisation=organisation,
            dataset_type=AVLType,
            avl_compliance_cached__status=MORE_DATA_NEEDED,
        )
        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=234,
            vehicle_activities_completely_matching=123,
            granularity=PPCReportType.DAILY,
            created=today,
        )
        client = client_factory(host=self.host)
        client.force_login(user=user)
        url = reverse(
            "avl:feed-detail", args=(organisation.id, dataset.id), host=self.host
        )
        response = client.get(url)

        RE_WORD = re.compile(MORE_DATA_NEEDED)
        occur_more_data_needed = RE_WORD.findall(str(response.content))
        assert len(occur_more_data_needed) == 2

    def test_each_feed_ppc_score_post_publishing_more_rows(
        self,
        client_factory,
    ):
        """
        GIVEN : an AVL dataset

        WHEN  : the PostPublishingCheckReport has been created with
                3 different date

        THEN  : the view should display the ppc score
        """
        organisation = OrganisationFactory()
        user = OrgStaffFactory(organisations=(organisation,))
        today = date.today()
        last_week = today - timedelta(days=7)
        week_before = today - timedelta(days=14)

        dataset = DatasetFactory(organisation=organisation, dataset_type=AVLType)
        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=654,
            vehicle_activities_completely_matching=543,
            granularity=PPCReportType.WEEKLY,
            created=today,
        )
        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=300,
            vehicle_activities_completely_matching=232,
            granularity=PPCReportType.WEEKLY,
            created=last_week,
        )
        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=956,
            vehicle_activities_completely_matching=841,
            granularity=PPCReportType.WEEKLY,
            created=week_before,
        )
        client = client_factory(host=self.host)
        client.force_login(user=user)
        url = reverse(
            "avl:feed-detail", args=(organisation.id, dataset.id), host=self.host
        )
        response = client.get(url)

        expected = str(round(543 / 654.0 * 100)) + "%"
        assert (
            response.context_data["properties"]["avl_timetables_matching"] == expected
        )
