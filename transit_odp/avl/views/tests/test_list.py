from datetime import date, timedelta

import pytest
from django.db.models.fields import timezone
from django_hosts.resolvers import reverse

import config.hosts
from transit_odp.avl.constants import MORE_DATA_NEEDED
from transit_odp.avl.factories import PostPublishingCheckReportFactory
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
                granularity="weekly",
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
                granularity="weekly",
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
            dataset_type=AVLType,
        )
        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=10,
            vehicle_activities_completely_matching=1,
            granularity="weekly",
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
            granularity="weekly",
            created=today,
        )

        dataset_revision = DatasetRevisionFactory(
            dataset__dataset_type=AVLType,
            dataset__organisation=organisation,
            status=INACTIVE,
        )
        PostPublishingCheckReportFactory(
            dataset=dataset_revision.dataset,
            vehicle_activities_analysed=10,
            vehicle_activities_completely_matching=4,
            granularity="weekly",
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
            granularity="daily",
            created=today,
        )
        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=10,
            vehicle_activities_completely_matching=2,
            granularity="daily",
            created=today - timedelta(days=1),
        )

        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=10,
            vehicle_activities_completely_matching=4,
            granularity="weekly",
            created=today - timedelta(days=1),
        )

        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=10,
            vehicle_activities_completely_matching=8,
            granularity="weekly",
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
            granularity="weekly",
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
            granularity="daily",
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
            granularity="weekly",
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
            granularity="weekly",
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
