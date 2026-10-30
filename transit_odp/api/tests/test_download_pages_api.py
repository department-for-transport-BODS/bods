from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.files.base import ContentFile
from django.test import override_settings
from django.utils import timezone
from django_hosts import reverse

from config.hosts import DATA_HOST
from transit_odp.avl.factories import CAVLDataArchiveFactory
from transit_odp.common.downloaders import GTFSFile
from transit_odp.disruptions.models import DisruptionsDataArchive
from transit_odp.organisation.constants import FaresType
from transit_odp.pipelines.factories import (
    BulkDataArchiveFactory,
    ChangeDataArchiveFactory,
)
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db

TIMETABLES_URL = "browser-download-timetables"
AVL_URL = "browser-download-avl"
FARES_URL = "browser-download-fares"
DISRUPTIONS_URL = "browser-download-disruptions"
COACH_URL = "browser-download-coach"
TIMETABLE_VIEWS = "transit_odp.browse.views.timetable_views"


def _url(name):
    return reverse(f"api:{name}", host=DATA_HOST)


@pytest.fixture
def logged_in_client(data_client):
    data_client.force_login(UserFactory())
    return data_client


@pytest.mark.parametrize("name", [TIMETABLES_URL, AVL_URL, FARES_URL, DISRUPTIONS_URL])
def test_login_required_endpoints_reject_anonymous_users(data_client, name):
    response = data_client.get(_url(name))

    assert response.status_code == 401
    assert response.json() == {"error": "Authentication required"}


@pytest.mark.parametrize(
    "name", [TIMETABLES_URL, AVL_URL, FARES_URL, DISRUPTIONS_URL, COACH_URL]
)
def test_endpoints_only_allow_get(logged_in_client, name):
    assert logged_in_client.post(_url(name)).status_code == 405


class TestTimetables:
    def test_empty_state(self, logged_in_client):
        with patch(f"{TIMETABLE_VIEWS}.flag_is_active", return_value=False), patch(
            f"{TIMETABLE_VIEWS}.GTFSFileDownloader"
        ) as downloader:
            downloader.return_value.get_files.return_value = []
            response = logged_in_client.get(_url(TIMETABLES_URL))

        assert response.status_code == 200
        payload = response.json()
        assert payload["showBulkArchiveUrl"] is False
        assert payload["changeArchives"] == []
        assert payload["isNewGtfsApiActive"] is False
        assert payload["gtfsFiles"] == []
        assert all(region["exists"] is False for region in payload["regions"])
        assert [region["regionCode"] for region in payload["regions"]][0] == "ALL"
        assert {"regionCode": "EA", "name": "East Anglia", "exists": False} in (
            payload["regions"]
        )

    def test_bulk_archives_and_change_archives(self, logged_in_client):
        BulkDataArchiveFactory()
        BulkDataArchiveFactory(traveline_regions="EA")
        BulkDataArchiveFactory(traveline_regions="SW", compliant_archive=True)
        today = timezone.now().date()
        ChangeDataArchiveFactory(published_at=today)
        ChangeDataArchiveFactory(published_at=today - timedelta(days=30))

        with patch(f"{TIMETABLE_VIEWS}.flag_is_active", return_value=False), patch(
            f"{TIMETABLE_VIEWS}.GTFSFileDownloader"
        ) as downloader:
            downloader.return_value.get_files.return_value = []
            payload = logged_in_client.get(_url(TIMETABLES_URL)).json()

        assert payload["showBulkArchiveUrl"] is True
        existing = {r["regionCode"] for r in payload["regions"] if r["exists"]}
        # Same as the Django page: any archive for a region counts, compliant or not
        assert existing == {"EA", "SW"}
        assert payload["changeArchives"] == [
            {
                "publishedAt": today.isoformat(),
                "label": today.strftime("%A %-d %B"),
            }
        ]

    def test_only_compliant_archive_hides_bulk_link(self, logged_in_client):
        BulkDataArchiveFactory(compliant_archive=True)

        with patch(f"{TIMETABLE_VIEWS}.flag_is_active", return_value=False), patch(
            f"{TIMETABLE_VIEWS}.GTFSFileDownloader"
        ) as downloader:
            downloader.return_value.get_files.return_value = []
            payload = logged_in_client.get(_url(TIMETABLES_URL)).json()

        assert payload["showBulkArchiveUrl"] is False

    def test_legacy_gtfs_files_when_new_gtfs_api_is_off(self, logged_in_client):
        files = [GTFSFile("itm_south_east_gtfs.zip"), GTFSFile("itm_all_gtfs.zip")]

        with patch(f"{TIMETABLE_VIEWS}.flag_is_active", return_value=False), patch(
            f"{TIMETABLE_VIEWS}.GTFSFileDownloader"
        ) as downloader:
            downloader.return_value.get_files.return_value = files
            payload = logged_in_client.get(_url(TIMETABLES_URL)).json()

        assert payload["isNewGtfsApiActive"] is False
        assert payload["gtfsFiles"] == [
            {"id": "south_east", "name": "South East"},
            {"id": "all", "name": "All"},
        ]

    def test_gtfs_regions_when_new_gtfs_api_is_on(self, logged_in_client):
        regions = [
            {"regionName": "all", "regionDisplayName": "All"},
            {"regionName": "south_east", "regionDisplayName": "South East"},
        ]

        with patch(f"{TIMETABLE_VIEWS}.flag_is_active", return_value=True), patch(
            f"{TIMETABLE_VIEWS}._get_gtfs_regions", return_value=regions
        ):
            payload = logged_in_client.get(_url(TIMETABLES_URL)).json()

        assert payload["isNewGtfsApiActive"] is True
        assert payload["gtfsFiles"] == [
            {"id": "all", "name": "All"},
            {"id": "south_east", "name": "South East"},
        ]

    def test_gtfs_api_failure_gives_empty_list(self, logged_in_client):
        with patch(f"{TIMETABLE_VIEWS}.flag_is_active", return_value=True), patch(
            f"{TIMETABLE_VIEWS}._get_gtfs_regions", return_value=None
        ):
            payload = logged_in_client.get(_url(TIMETABLES_URL)).json()

        assert payload["isNewGtfsApiActive"] is True
        assert payload["gtfsFiles"] == []


class TestAvl:
    def test_no_archive(self, logged_in_client):
        response = logged_in_client.get(_url(AVL_URL))

        assert response.status_code == 200
        assert response.json() == {"showBulkArchiveUrl": False}

    def test_with_archive(self, logged_in_client):
        CAVLDataArchiveFactory()

        assert logged_in_client.get(_url(AVL_URL)).json() == {
            "showBulkArchiveUrl": True
        }


class TestFares:
    def test_no_archive(self, logged_in_client):
        response = logged_in_client.get(_url(FARES_URL))

        assert response.status_code == 200
        assert response.json() == {"showBulkArchiveUrl": False}

    def test_only_fares_archives_count(self, logged_in_client):
        BulkDataArchiveFactory()
        assert logged_in_client.get(_url(FARES_URL)).json() == {
            "showBulkArchiveUrl": False
        }

        BulkDataArchiveFactory(dataset_type=FaresType)
        assert logged_in_client.get(_url(FARES_URL)).json() == {
            "showBulkArchiveUrl": True
        }


class TestDisruptions:
    @pytest.mark.parametrize("flag", [True, False])
    def test_flag_is_reflected(self, logged_in_client, flag):
        with patch(
            "transit_odp.browse.views.disruptions_views.flag_is_active",
            return_value=flag,
        ):
            payload = logged_in_client.get(_url(DISRUPTIONS_URL)).json()

        assert payload == {
            "showBulkArchiveUrl": False,
            "isGtfsServiceAlertsLive": flag,
        }

    def test_with_archive(self, logged_in_client):
        DisruptionsDataArchive.objects.create(
            data_format=DisruptionsDataArchive.SIRISX,
            data=ContentFile(b"data", name="disruptions.zip"),
        )

        with patch(
            "transit_odp.browse.views.disruptions_views.flag_is_active",
            return_value=False,
        ):
            payload = logged_in_client.get(_url(DISRUPTIONS_URL)).json()

        assert payload["showBulkArchiveUrl"] is True


class TestCoach:
    @override_settings(
        COACH_TXC_FILE_S3_URL="https://example.test/txc.zip",
        COACH_ATCO_FILE_S3_URL="https://example.test/atco.zip",
    )
    def test_is_public_and_returns_file_urls(self, data_client):
        response = data_client.get(_url(COACH_URL))

        assert response.status_code == 200
        assert response.json() == {
            "txcFile": "https://example.test/txc.zip",
            "atcoFile": "https://example.test/atco.zip",
        }
