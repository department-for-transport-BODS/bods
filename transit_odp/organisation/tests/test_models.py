import hashlib
from datetime import datetime, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from django_hosts import reverse
from freezegun import freeze_time

from config.hosts import PUBLISH_HOST
from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    DatasetFactory,
    DatasetRevisionFactory,
    DraftDatasetFactory,
)
from transit_odp.pipelines.factories import RemoteDatasetHealthCheckCountFactory
from transit_odp.users.constants import AccountType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestDatasetModel:
    @pytest.mark.parametrize("defaults", [{}, {"description": "New revision"}])
    def test_start_revision_initial(self, defaults):
        """Tests a new revision is initialised with no data when no previous
        revision exists"""
        dataset = DatasetFactory(live_revision=None)
        revision = dataset.start_revision(**defaults)
        assert revision.dataset == dataset
        assert revision.id is None
        assert revision.published_by is None
        assert revision.status == FeedStatus.pending.value
        assert revision.name is None
        assert revision.description == defaults.get("description", "")
        assert revision.comment == "First publication"
        assert revision.upload_file.name is None
        assert revision.url_link == ""

    @pytest.mark.parametrize("defaults", [{}, {"description": "New revision"}])
    def test_start_revision_with_live_revision(self, defaults):
        """Tests a new revision is initialised with data from the previous
        published revision"""
        dataset = DatasetFactory()
        live_revision = dataset.live_revision
        revision = dataset.start_revision(**defaults)
        assert revision.dataset == dataset
        assert revision.id is None
        assert revision.published_by is None
        assert revision.status == FeedStatus.pending.value
        assert revision.name is None
        assert revision.description == defaults.get(
            "description", live_revision.description
        )
        assert revision.comment == ""
        assert revision.upload_file == live_revision.upload_file
        assert revision.url_link == live_revision.url_link


class TestDatasetRevision:
    mut = "transit_odp.organisation.models.data"

    def test_dataset_created_must_be_unique(self):
        """Tests that IntegrityError is raised if dataset-created fields are
        not unique"""
        dataset = DatasetFactory(live_revision=None)
        now = timezone.now()
        DatasetRevisionFactory(dataset=dataset, is_published=True, created=now)
        with pytest.raises(IntegrityError):
            DatasetRevisionFactory(dataset=dataset, is_published=True, created=now)

    def test_dataset_revision_draft_must_be_unique(self):
        """Tests that IntegrityError is raised if dataset has more than
        one unpublished revision"""
        dataset = DatasetFactory(live_revision=None)
        now = timezone.now()
        DatasetRevisionFactory(
            dataset=dataset, is_published=False, created=now - timedelta(days=1)
        )

        with pytest.raises(IntegrityError):
            DatasetRevisionFactory(dataset=dataset, is_published=False, created=now)

    def test_dataset_live_revision_on_publish(self):
        """Tests the denormalised FK, live_revision, on the Dataset is updated to
        the newly published DatasetRevision"""
        dataset = DatasetFactory(live_revision=None)
        assert dataset.live_revision is None
        rev = DatasetRevisionFactory(dataset=dataset, is_published=False)
        dataset.refresh_from_db()
        assert dataset.live_revision is None
        rev.is_published = True
        rev.save()
        dataset.refresh_from_db()
        assert dataset.live_revision == rev

    def test_get_hash(self, mocker):
        """Tests feeds get_hash method"""
        revision = DatasetRevisionFactory()
        mocker.patch.object(revision, "get_file_content", return_value=b"abcd")
        result = revision.get_hash()
        assert result == hashlib.sha1(b"abcd").hexdigest()

    def test_is_remote(self):
        """Tests is_remote property returns turn if url_link is set"""
        revision = DatasetRevisionFactory(
            upload_file=None, url_link="www.example.com/dataset"
        )
        result = revision.is_remote
        assert result

    def test_is_local(self):
        """Tests is_local property returns turn if url_link is not set"""
        revision = DatasetRevisionFactory()
        result = revision.is_local
        assert result

    def test_get_availability_retry_count(self):
        """Tests DatasetAvailabilityRetryCount is initialised if it doesn't exist"""
        revision = DatasetRevisionFactory(
            upload_file=None, url_link="www.example.com/dataset", is_published=True
        )
        availability_retry_count = revision.get_availability_retry_count()
        assert availability_retry_count is not None
        assert availability_retry_count.count == 0
        assert availability_retry_count.revision == revision

    # TODO - need to clarify this requirement as the revision only goes 'live'
    # once when published
    @pytest.mark.skip
    def test_availability_retry_count_reset_when_feed_goes_live(self):
        """Tests the DatasetAvailabilityRetryCount model count is reset to zero
        when status set to live"""
        revision = DatasetRevisionFactory(
            upload_file=None,
            url_link="www.example.com/dataset",
            is_published=False,
            status=FeedStatus.indexing.value,
        )
        reset_counter = RemoteDatasetHealthCheckCountFactory(revision=revision, count=1)
        revision.to_live()
        assert reset_counter.count == 0

    @pytest.mark.parametrize("field_with_profanity", ["name", "description", "comment"])
    def test_model_validates_profanity(self, field_with_profanity):
        with pytest.raises(ValidationError) as e:
            # create feed and set field to contain profanity
            revision = DatasetRevisionFactory.build()
            setattr(revision, field_with_profanity, "shit")
            # Note validators only run when specifically called, not on save.
            revision.full_clean()

        # test field errors contain profanity error
        errors = e.value.error_dict[field_with_profanity]
        assert any(
            err.code == "profanity" for err in errors if getattr(err, "code", False)
        )

    def test_publish_revision(self):
        now = timezone.now()
        user = UserFactory(account_type=AccountType.org_admin.value)
        revision = DatasetRevisionFactory(
            is_published=False, status=FeedStatus.success.value
        )

        with freeze_time(now):
            revision.publish(user)
        assert revision.is_published is True
        assert revision.published_by == user
        assert revision.published_at == now
        assert revision.status == FeedStatus.live.value  # TODO change

    def test_start_etl(self, mocker):
        """Tests the start_etl method triggers the dataset_etl signal"""
        revision = DatasetRevisionFactory()
        mocked_signal = mocker.patch(f"{self.mut}.dataset_etl")
        revision.start_etl()
        mocked_signal.send.assert_called_once_with(revision, revision=revision)

    def test_temporary_name_is_assigned_on_save(self):
        """Tests the revision is created with a temporary name"""
        dt = datetime(2020, 12, 25, 18)
        with freeze_time(dt):
            revision = DatasetRevisionFactory(name=None)
        organisation = revision.dataset.organisation
        expected = f"{organisation.name}_{revision.dataset.id}_{dt:%Y%m%d %H:%M:%S}"
        assert revision.name == expected

    def test_temporary_name_is_assigned_on_save_in_bst(self):
        """Tests the revision is created with a temporary name"""
        dt = datetime(2021, 4, 30, 18)
        with freeze_time(dt):
            revision = DatasetRevisionFactory(name=None)
        organisation = revision.dataset.organisation
        expected = f"{organisation.name}_{revision.dataset.id}_20210430 19:00:00"
        assert revision.name == expected

    def test_avl_dataset_publish_register_cavl(self, mocker):
        revision = AVLDatasetRevisionFactory(
            is_published=False,
            url_link="https://www.test-feed.com",
            username="test-account",
            password="password123",
        )
        cavl_service = mocker.patch(f"{self.mut}.get_cavl_service").return_value
        revision.publish()
        cavl_service.register_feed.assert_called_once_with(
            feed_id=revision.dataset.id,
            publisher_id=revision.dataset.organisation_id,
            url="https://www.test-feed.com",
            username="test-account",
            password="password123",
        )

    def test_avl_dataset_publish_update_cavl(self, mocker):
        """Tests the feed is updated in CAVL when the dataset is edited"""
        dt = timezone.now() - timedelta(minutes=5)
        with freeze_time(dt):
            revision = AVLDatasetRevisionFactory(
                is_published=True,
                url_link="https://www.test-feed.com",
                username="test-account",
                password="password123",
            )

        new_revision = AVLDatasetRevisionFactory(
            dataset=revision.dataset,
            is_published=False,
            url_link="https://www.test-feed.v2.com",
            username="test-account.v2",
            password="password123.v2",
        )

        cavl_service = mocker.patch(f"{self.mut}.get_cavl_service").return_value
        new_revision.publish()
        cavl_service.update_feed.assert_called_once_with(
            feed_id=revision.dataset.id,
            url="https://www.test-feed.v2.com",
            username="test-account.v2",
            password="password123.v2",
        )

    def test_revision_draft_url_for_new_dataset(self):
        dataset = DraftDatasetFactory()
        assert dataset.revisions.latest().draft_url == reverse(
            "revision-publish",
            kwargs={"pk": dataset.id, "pk1": dataset.organisation.id},
            host=PUBLISH_HOST,
        )

    def test_revision_draft_url_for_existing_datasets(self):
        dataset = DatasetFactory(live_revision=None)
        live = DatasetRevisionFactory(
            created=datetime(2021, 4, 10, 16, 0, 4),
            modified=datetime(2021, 4, 10, 16, 0, 4),
            status=FeedStatus.live.value,
            is_published=True,
            dataset=dataset,
        )
        DatasetRevisionFactory(
            status=FeedStatus.draft.value,
            is_published=False,
            dataset=dataset,
        )
        assert dataset.live_revision == live
        assert dataset.revisions.latest().draft_url == reverse(
            "revision-update-publish",
            kwargs={"pk": dataset.id, "pk1": dataset.organisation.id},
            host=PUBLISH_HOST,
        )

    def test_revision_draft_url_for_live_datasets(self):
        dataset = DatasetFactory(live_revision=None)
        DatasetRevisionFactory(
            created=datetime(2021, 4, 10, 16, 0, 4),
            modified=datetime(2021, 4, 10, 16, 0, 4),
            status=FeedStatus.live.value,
            dataset=dataset,
            is_published=True,
        )
        live = DatasetRevisionFactory(
            is_published=True, status=FeedStatus.live.value, dataset=dataset
        )
        assert dataset.live_revision == live
        assert dataset.revisions.latest().draft_url == reverse(
            "feed-detail",
            kwargs={"pk": dataset.id, "pk1": dataset.organisation.id},
            host=PUBLISH_HOST,
        )
