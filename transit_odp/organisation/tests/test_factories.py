from datetime import datetime, timedelta

import pytest
import pytz
from django.utils import timezone
from freezegun import freeze_time

from transit_odp.organisation.constants import DatasetType, FeedStatus
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    DatasetFactory,
    DatasetRevisionFactory,
    DraftDatasetFactory,
    OrganisationFactory,
)
from transit_odp.organisation.models import DatasetRevision
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestOrganisationFactory:
    def test_operator_code_created_on_create(self):
        """Tests an OperatorCode is created when an Organisation is added
        Also ensures the OperatorCode's FK points back to the parent Organisation
        """
        # Test
        organisation = (
            OrganisationFactory()
        )  # by default, creates 1 OperatorCode instance for an Organisation

        # Assert
        assert organisation.nocs is not None

        operator_code = organisation.nocs.first().noc

        assert operator_code is not None
        assert organisation.nocs.first().organisation == organisation


class TestDatasetFactory:
    def test_live_revision_is_created_by_default(self):
        """Tests a DatasetRevision is instantiated as the live_revision

        Also ensures the DatasetRevision's dataset FK points back to the parent Dataset
        """
        # Test
        dataset = DatasetFactory()

        # Setup
        assert dataset.live_revision is not None
        assert dataset.live_revision.is_published is True
        assert dataset.live_revision.status == FeedStatus.live.value
        assert dataset.live_revision.dataset == dataset


class TestDraftDatasetFactory:
    def test_creates_a_draft_revision(self):
        """Tests dataset is created with a related, unpublished DatasetRevision"""
        # Test
        dataset = DraftDatasetFactory()

        # Setup
        assert dataset.id is not None
        assert dataset.live_revision is None
        revisions = dataset.revisions.all()

        assert len(revisions) == 1
        revision = revisions[0]
        assert revision.is_published is False
        assert revision.status == FeedStatus.draft.value
        assert revision.dataset == dataset


class TestDatasetRevisionFactory:
    def test_creates_dataset_subfactory_with_live_revision_as_null(self):
        """Tests the factory creates the parent Dataset with live_revision set to None

        This is useful when creating DatasetRevisions without explicitly passing
        in a Dataset.

        Note this behaviour by which live_revision is set on the Dataset is due
        to a post_save signal not factoryboy
        """
        revision = DatasetRevisionFactory(is_published=True)
        assert DatasetRevision.objects.count() == 1
        assert revision.dataset.live_revision == revision

    def test_creates_dataset_subfactory_with_live_revision_as_revision(self):
        """Tests the factory creates the parent Dataset with live_revision set
        to the published dataset

        This is useful when creating DatasetRevisions without explicitly passing in
        a Dataset
        """
        # Setup
        revision = DatasetRevisionFactory(is_published=False)

        # Assert
        assert DatasetRevision.objects.count() == 1
        assert revision.dataset.live_revision is None

    def test_set_created_with_freezegun(self):
        """Tests the factory uses the value provided for created to freeze time
        while creating objects"""
        # Setup
        dataset = DatasetFactory()
        now = datetime.utcnow().replace(tzinfo=pytz.utc)

        # Test
        rev1 = DatasetRevisionFactory(
            dataset=dataset, is_published=True, created=now - timedelta(hours=2)
        )
        rev2 = DatasetRevisionFactory(
            dataset=dataset, is_published=True, created=now - timedelta(hours=1)
        )
        rev3 = DatasetRevisionFactory(dataset=dataset, is_published=True, created=now)

        # Assert
        assert rev1.created == now - timedelta(hours=2)
        assert rev2.created == now - timedelta(hours=1)
        assert rev3.created == now

    def test_published_by_is_set_to_null(self):
        """Tests factory sets published_by to null. Note it might be useful to
        conditionally create published_by when is_published=True.
        """
        # Setup
        revision = DatasetRevisionFactory(is_published=True)

        # Assert
        assert revision.published_by is None

    def test_initialises_published_at_when_is_published_is_true(self):
        """Tests published_at is initialised when is_published=True"""
        now = timezone.now()

        with freeze_time(now):
            published = DatasetRevisionFactory(is_published=True)
            unpublished = DatasetRevisionFactory(is_published=False)

        # Assert
        assert published.published_at == now
        assert unpublished.published_at is None

    def test_initialises_published_at_when_is_published_by_is_set(self):
        """Tests published_at is initialised when published_at=User"""
        now = timezone.now()

        org = OrganisationFactory()
        publisher = UserFactory(
            account_type=AccountType.org_admin.value, organisations=(org,)
        )

        with freeze_time(now):
            published = DatasetRevisionFactory(
                published_by=publisher, dataset__organisation=org
            )

        # Assert
        assert published.published_at == now


class TestAVLDatasetRevisionFactory:
    def test_creates_avl_dataset(self):

        # Test
        revision = AVLDatasetRevisionFactory()

        # Assert
        assert revision.dataset.dataset_type == DatasetType.AVL
        assert len(revision.url_link) > 0
        assert bool(revision.upload_file) is False
        assert revision.first_service_start is None
