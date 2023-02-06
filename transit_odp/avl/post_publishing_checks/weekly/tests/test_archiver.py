from unittest.mock import Mock
from zipfile import ZipFile

import pandas as pd
import pytest

from transit_odp.avl.post_publishing_checks.weekly.archiver import (
    WeeklyPPCReportArchiver,
)
from transit_odp.avl.post_publishing_checks.weekly.constants import (
    WeeklyPPCSummaryFiles,
)


@pytest.fixture()
def summary_data() -> Mock:
    summary_data_mock = Mock()
    summary_data_mock.get_summary_report.return_value = pd.DataFrame()
    summary_data_mock.get_block_ref.return_value = pd.DataFrame()
    summary_data_mock.get_destination_ref.return_value = pd.DataFrame()
    summary_data_mock.get_direction_ref.return_value = pd.DataFrame()
    summary_data_mock.get_origin_ref.return_value = pd.DataFrame()
    summary_data_mock.get_siri_message_analysed.return_value = pd.DataFrame()
    summary_data_mock.get_uncounted_vehicle_activities.return_value = pd.DataFrame()

    return summary_data_mock


def test_create_archive_with_correct_files(summary_data: Mock) -> None:
    """
    Weekly Report Archive should contain files defined in WeeklyPPCSummaryFiles Enum
    """
    archiver = WeeklyPPCReportArchiver()

    archive = archiver.to_zip(summary_data)
    with ZipFile(archive, "r") as archive_r:
        filenames = {zipinfo.filename for zipinfo in archive_r.filelist}

    expected_files = set(WeeklyPPCSummaryFiles.to_list())

    assert filenames == expected_files
