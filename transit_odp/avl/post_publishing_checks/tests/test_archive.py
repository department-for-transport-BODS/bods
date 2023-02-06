import datetime

import pytest
from freezegun import freeze_time

from transit_odp.avl.post_publishing_checks.archive import PPCArchiveCreator
from transit_odp.organisation.constants import INACTIVE, AVLType
from transit_odp.organisation.factories import (
    DatasetFactory,
    DraftDatasetFactory,
    OrganisationFactory,
)

pytestmark = pytest.mark.django_db


class TestPPCArchiveCreator:
    def test_getdatasets(self):
        organisation = OrganisationFactory()
        DraftDatasetFactory(organisation=organisation, dataset_type=AVLType)
        dataset2 = DatasetFactory(organisation=organisation, dataset_type=AVLType)
        DatasetFactory(
            organisation=organisation,
            dataset_type=AVLType,
            live_revision__status=INACTIVE,
        )

        archiver = PPCArchiveCreator()
        archiver._get_datasets_for_org(organisation.id)
        assert archiver._avl_datasets.count() == 1
        assert archiver._avl_datasets.first().id == dataset2.id

    @freeze_time("2022-01-01 12:00:00")
    def test_weekly_archive_dates(self):
        archiver = PPCArchiveCreator()
        archiver._set_weekly_archive_dates()
        assert len(archiver._archive_dates) == 4
        assert len(set(archiver._archive_dates)) == 4
        today = datetime.date.today()
        for d in archiver._archive_dates:
            assert d.weekday() == 6
            assert today >= d > today - datetime.timedelta(weeks=4)

    @freeze_time("2022-01-02 12:00:00")  # Sunday
    def test_weekly_zips(self):
        organisation = OrganisationFactory()
        archiver = PPCArchiveCreator()
        archiver._get_datasets_for_org(organisation.id)
        archiver._set_weekly_archive_dates()
        archiver._create_weekly_zips()

        assert len(archiver._weekly_zips) == 4
        today = datetime.date.today()
        expected_dates = [today - datetime.timedelta(weeks=n) for n in range(4)]
        expected_filenames = [
            f"week_{d.strftime('%d_%m_%Y')}_all_feeds_0.zip" for d in expected_dates
        ]
        for zip in archiver._weekly_zips:
            assert isinstance(zip, tuple)
            assert zip[1] in expected_filenames
