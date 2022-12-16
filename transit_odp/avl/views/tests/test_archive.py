import datetime
import io
import statistics
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import factory
import pytest
from django_hosts.resolvers import reverse
from freezegun import freeze_time

import config.hosts
from transit_odp.avl.factories import PostPublishingCheckReportFactory
from transit_odp.avl.models import PPCReportType
from transit_odp.avl.views.archive import AVLFeedArchiveView
from transit_odp.organisation.constants import AVLType
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    DatasetFactory,
    OrganisationFactory,
)
from transit_odp.users.factories import OrgStaffFactory
from transit_odp.users.views.mixins import OrgUserViewMixin

pytestmark = pytest.mark.django_db

AVL_VIEWS = "transit_odp.avl.views."
TEST_DATA = Path(__file__).resolve().parent / "data"


class TestAVLFeedArchiveViewDataset:
    host = config.hosts.PUBLISH_HOST

    def test_view_permission_mixin(self):
        assert issubclass(AVLFeedArchiveView, OrgUserViewMixin)

    @pytest.mark.skip("Doesn't work in the pipeline due to --numprocesses")
    @patch(AVL_VIEWS + "archive.CAVLService")
    def test_archive_successful(self, get_service, client_factory):
        client = client_factory(host=self.host)
        mock_cavl = Mock()
        mock_cavl.delete_feed = Mock(return_value=None)
        get_service.return_value = mock_cavl

        organisation = OrganisationFactory()
        user = OrgStaffFactory(organisations=(organisation,))
        dataset = AVLDatasetRevisionFactory(
            published_by=user, dataset__organisation=organisation
        )

        client.force_login(user=user)
        url = reverse(
            "avl:feed-archive", args=[organisation.id, dataset.id], host=self.host
        )
        success_url = reverse(
            "avl:feed-archive-success",
            args=[organisation.id, dataset.id],
            host=self.host,
        )

        response = client.post(url, data={"submit": "submit"})
        dataset.refresh_from_db()

        mock_cavl.delete_feed.assert_called_once_with(feed_id=dataset.id)
        assert dataset.status == "inactive"
        assert response.status_code == 302
        assert response.url == success_url


@freeze_time("2022-12-04")  # Sunday
class TestPPCArchiveView:
    host = config.hosts.PUBLISH_HOST

    def test_archive_successful(self, client_factory):
        client = client_factory(host=self.host)

        organisation = OrganisationFactory()
        user = OrgStaffFactory(organisations=(organisation,))
        datasets = DatasetFactory.create_batch(
            4, organisation=organisation, dataset_type=AVLType, contact=user
        )
        all_scores = [(1, 10), (2, 10), (3, 10), (4, 10)]
        percent_scores = [round(s[0] * 100 / s[1]) for s in all_scores]
        today = datetime.date.today()
        report_dates = [today - datetime.timedelta(weeks=n) for n in range(3, -1, -1)]
        report_file = TEST_DATA / "report.zip"
        for i, report_date in enumerate(report_dates):
            # Create a single report the first week, then add one report each week
            scores_for_this_week = all_scores[: i + 1]
            for j, score in enumerate(scores_for_this_week):
                matching = score[0]
                analysed = score[1]
                score = round(matching * 100 / analysed)
                filename = (
                    f"week_{report_date.strftime('%d_%m_%Y')}_"
                    f"feed_{datasets[j].id}_{score}.zip"
                )
                PostPublishingCheckReportFactory(
                    dataset=datasets[j],
                    granularity=PPCReportType.WEEKLY,
                    created=report_date,
                    file=factory.django.FileField(
                        from_path=report_file, filename=filename
                    ),
                    vehicle_activities_analysed=analysed,
                    vehicle_activities_completely_matching=matching,
                )

        url = reverse("ppc-archive", args=[organisation.id], host=self.host)
        response = client.get(url)
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"]
            == "attachment; filename=archived_avl_to_timetable_matching_all_feeds.zip"
        )
        stream = response.streaming_content
        response_buffer = io.BytesIO()
        for chunk in stream:
            response_buffer.write(chunk)
        with zipfile.ZipFile(response_buffer, mode="r") as zin:
            zipped_files = zin.namelist()
            assert len(zipped_files) == 4
            for n, report_date in enumerate(report_dates):
                weekly_percentages = percent_scores[: n + 1]
                expected_avg = round(statistics.mean(weekly_percentages))
                expected_zip_name = (
                    f"week_{report_date.strftime('%d_%m_%Y')}_"
                    f"all_feeds_{expected_avg}.zip"
                )
                assert expected_zip_name in zipped_files

                content = zin.read(expected_zip_name)
                inner_buffer = io.BytesIO()
                inner_buffer.write(content)
                with zipfile.ZipFile(inner_buffer, mode="r") as inner_zin:
                    inner_zipped_files = inner_zin.namelist()
                    assert len(inner_zipped_files) == len(weekly_percentages)
                    for m, expected_score in enumerate(weekly_percentages):
                        expected_inner_zip_name = (
                            f"week_{report_date.strftime('%d_%m_%Y')}_"
                            f"feed_{datasets[m].id}_{expected_score}.zip"
                        )
                        assert expected_inner_zip_name in inner_zipped_files

    def test_no_reports_for_org(self, client_factory):
        client = client_factory(host=self.host)

        # Create organisation with a dataset with no PPC reports.
        organisation = OrganisationFactory()
        user = OrgStaffFactory(organisations=(organisation,))
        DatasetFactory(organisation=organisation, dataset_type=AVLType, contact=user)

        # Create second organisation with a dataset with 1 PPC report.
        org2 = OrganisationFactory()
        user2 = OrgStaffFactory(organisations=(org2,))
        org2_dataset = DatasetFactory(
            organisation=org2, dataset_type=AVLType, contact=user2
        )
        today = datetime.date.today()
        report_file = TEST_DATA / "report.zip"
        analysed = 10
        matching = 9
        percent_score = round(matching * 100 / analysed)
        filename = (
            f"week_{today.strftime('%d_%m_%Y')}_"
            f"feed_{org2_dataset.id}_{percent_score}.zip"
        )
        PostPublishingCheckReportFactory(
            dataset=org2_dataset,
            granularity=PPCReportType.WEEKLY,
            created=today,
            file=factory.django.FileField(from_path=report_file, filename=filename),
            vehicle_activities_analysed=analysed,
            vehicle_activities_completely_matching=matching,
        )

        # Check archive for first organisation.
        url = reverse("ppc-archive", args=[organisation.id], host=self.host)
        response = client.get(url)
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"]
            == "attachment; filename=archived_avl_to_timetable_matching_all_feeds.zip"
        )
        stream = response.streaming_content
        response_buffer = io.BytesIO()
        for chunk in stream:
            response_buffer.write(chunk)
        with zipfile.ZipFile(response_buffer, mode="r") as zin:
            zipped_files = zin.namelist()
            assert len(zipped_files) == 4
            today = datetime.date.today()
            expected_dates = [today - datetime.timedelta(weeks=n) for n in range(4)]
            for expected_date in expected_dates:
                # If no reports in a given week, we set the score figure to 0%.
                expected_zip_name = (
                    f"week_{expected_date.strftime('%d_%m_%Y')}_all_feeds_0.zip"
                )
                assert expected_zip_name in zipped_files
                content = zin.read(expected_zip_name)
                inner_buffer = io.BytesIO()
                inner_buffer.write(content)

                with zipfile.ZipFile(inner_buffer, mode="r") as inner_zin:
                    inner_zipped_files = inner_zin.namelist()
                    assert len(inner_zipped_files) == 0

    def test_non_sunday_report(self, client_factory):
        client = client_factory(host=self.host)

        organisation = OrganisationFactory()
        user = OrgStaffFactory(organisations=(organisation,))
        dataset = DatasetFactory(
            organisation=organisation, dataset_type=AVLType, contact=user
        )
        score = (8, 10)
        percent_score = round(score[0] * 100 / score[1])
        today = datetime.date.today()
        # Create weekly report for a day earlier in the week. This should never happen
        # in reality but test we handle it.
        report_date = today - datetime.timedelta(days=3)
        report_file = TEST_DATA / "report.zip"
        filename = (
            f"week_{report_date.strftime('%d_%m_%Y')}_"
            f"feed_{dataset.id}_{percent_score}.zip"
        )
        PostPublishingCheckReportFactory(
            dataset=dataset,
            granularity=PPCReportType.WEEKLY,
            created=report_date,
            file=factory.django.FileField(from_path=report_file, filename=filename),
            vehicle_activities_analysed=score[1],
            vehicle_activities_completely_matching=score[0],
        )

        url = reverse("ppc-archive", args=[organisation.id], host=self.host)
        response = client.get(url)
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"]
            == "attachment; filename=archived_avl_to_timetable_matching_all_feeds.zip"
        )
        stream = response.streaming_content
        response_buffer = io.BytesIO()
        for chunk in stream:
            response_buffer.write(chunk)
        with zipfile.ZipFile(response_buffer, mode="r") as zin:
            zipped_files = zin.namelist()
            assert len(zipped_files) == 4
            expected_zip_name = (
                f"week_{today.strftime('%d_%m_%Y')}_all_feeds_{percent_score}.zip"
            )
            assert expected_zip_name in zipped_files
            content = zin.read(expected_zip_name)
            inner_buffer = io.BytesIO()
            inner_buffer.write(content)

            with zipfile.ZipFile(inner_buffer, mode="r") as inner_zin:
                inner_zipped_files = inner_zin.namelist()
                assert len(inner_zipped_files) == 1
                expected_inner_zip_name = (
                    f"week_{report_date.strftime('%d_%m_%Y')}_"
                    f"feed_{dataset.id}_{percent_score}.zip"
                )
                assert inner_zipped_files == [expected_inner_zip_name]

    def test_multiple_reports_same_week(self, client_factory):
        client = client_factory(host=self.host)

        organisation = OrganisationFactory()
        user = OrgStaffFactory(organisations=(organisation,))
        dataset = DatasetFactory(
            organisation=organisation, dataset_type=AVLType, contact=user
        )
        today = datetime.date.today()
        # Create two reports for the same dataset in the same week. This should never
        # happen in reality but test we handle it.
        report_dates = [today - datetime.timedelta(days=d) for d in [4, 1]]
        scores = [(4, 10), (6, 10)]
        percent_scores = [round(score[0] * 100 / score[1]) for score in scores]
        for i in range(len(report_dates)):
            report_file = TEST_DATA / "report.zip"
            filename = (
                f"week_{report_dates[i].strftime('%d_%m_%Y')}_"
                f"feed_{dataset.id}_{percent_scores[i]}.zip"
            )
            PostPublishingCheckReportFactory(
                dataset=dataset,
                granularity=PPCReportType.WEEKLY,
                created=report_dates[i],
                file=factory.django.FileField(from_path=report_file, filename=filename),
                vehicle_activities_analysed=scores[i][1],
                vehicle_activities_completely_matching=scores[i][0],
            )

        url = reverse("ppc-archive", args=[organisation.id], host=self.host)
        response = client.get(url)
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"]
            == "attachment; filename=archived_avl_to_timetable_matching_all_feeds.zip"
        )
        stream = response.streaming_content
        response_buffer = io.BytesIO()
        for chunk in stream:
            response_buffer.write(chunk)
        # Check that the later of the two reports is used and the other discarded.
        with zipfile.ZipFile(response_buffer, mode="r") as zin:
            zipped_files = zin.namelist()
            assert len(zipped_files) == 4
            expected_zip_name = (
                f"week_{today.strftime('%d_%m_%Y')}_all_feeds_{percent_scores[1]}.zip"
            )
            assert expected_zip_name in zipped_files
            content = zin.read(expected_zip_name)
            inner_buffer = io.BytesIO()
            inner_buffer.write(content)

            with zipfile.ZipFile(inner_buffer, mode="r") as inner_zin:
                inner_zipped_files = inner_zin.namelist()
                assert len(inner_zipped_files) == 1
                expected_inner_zip_name = (
                    f"week_{report_dates[1].strftime('%d_%m_%Y')}_"
                    f"feed_{dataset.id}_{percent_scores[1]}.zip"
                )
                assert inner_zipped_files == [expected_inner_zip_name]
