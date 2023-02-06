from datetime import date

import factory
import pytest
from django_hosts.resolvers import reverse

import config.hosts
from transit_odp.avl.factories import PostPublishingCheckReportFactory
from transit_odp.avl.models import PPCReportType
from transit_odp.organisation.constants import AVLType
from transit_odp.organisation.factories import DatasetFactory, OrganisationFactory
from transit_odp.users.factories import OrgStaffFactory

pytestmark = pytest.mark.django_db


class TestAvlFeedDetailView:
    host = config.hosts.PUBLISH_HOST

    def test_download_link_ppc_report(
        self,
        client_factory,
    ):
        """
        GIVEN : an AVL dataset

        WHEN  : PostPublishingCheckReport has been created with
                a file

        THEN  : the view should attached the file created in WHEN
        """
        organisation = OrganisationFactory()
        user = OrgStaffFactory(organisations=(organisation,))
        today = date.today()
        dataset = DatasetFactory(organisation=organisation, dataset_type=AVLType)
        filename = "dUmMy_FiLe.zip"
        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=10,
            vehicle_activities_completely_matching=10,
            granularity=PPCReportType.WEEKLY,
            file=factory.django.FileField(filename=filename),
            created=today,
        )

        client = client_factory(host=self.host)
        client.force_login(user=user)
        url = reverse(
            "avl:download-matching-report",
            args=(organisation.id, dataset.id),
            host=self.host,
        )
        response = client.get(url)
        assert response.get("Content-Disposition") == f"attachment; filename={filename}"

    def test_same_score_between_weekly_report_dataset_page(
        self,
        client_factory,
    ):
        organisation = OrganisationFactory()
        user = OrgStaffFactory(organisations=(organisation,))
        today = date.today()
        dataset = DatasetFactory(organisation=organisation, dataset_type=AVLType)
        PostPublishingCheckReportFactory(
            dataset=dataset,
            vehicle_activities_analysed=200,
            vehicle_activities_completely_matching=175,
            granularity=PPCReportType.WEEKLY,
            created=today,
        )

        client = client_factory(host=self.host)
        client.force_login(user=user)
        url_feed_detail = reverse(
            "avl:feed-detail",
            args=(organisation.id, dataset.id),
            host=self.host,
        )
        response = client.get(url_feed_detail)
        ppc_score_feed = response.context_data.get("properties").get(
            "avl_timetables_matching"
        )
        url_list_view = reverse(
            "avl:feed-list", args=(organisation.id,), host=self.host
        )
        response = client.get(url_list_view)
        table = response.context["table"]
        row = table.rows[0]
        ppc_score_table = row.get_cell("percent_matching")
        assert ppc_score_table == ppc_score_feed
