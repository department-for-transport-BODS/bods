import config.hosts
import pytest
from django.conf import settings
from django_hosts.resolvers import reverse

from transit_odp.fares.views import DatasetUpdateModify
from transit_odp.organisation.models import Dataset

pytestmark = pytest.mark.django_db

settings.IS_AVL_FEATURE_FLAG_ENABLED = True


def get_archive_feed_context(published_archive_url):
    url, client = published_archive_url
    response = client.get(url)
    return response.context


def test_archive_view_works(published_archive_url):
    # Setup
    url, client = published_archive_url

    # Test
    response = client.post(url, data={"submit": "submit"}, follow=True)
    fished_out_feed = Dataset.objects.first()

    # Assert
    assert response.status_code == 200
    assert fished_out_feed.live_revision.status == "inactive"
    assert response.context["back_to_data_sets"] == reverse(
        "fares:feed-list",
        host=config.hosts.PUBLISH_HOST,
        kwargs={"pk1": fished_out_feed.organisation_id},
    )


def test_archive_view_cancel_works(published_archive_url):
    # Setup
    _, client = published_archive_url
    context = get_archive_feed_context(published_archive_url)
    response = client.get(context["form"].cancel_url)
    assert response.status_code == 200


def test_archive_view_back_works(published_archive_url):
    # Setup
    _, client = published_archive_url
    context = get_archive_feed_context(published_archive_url)
    response = client.get(context["backlink"])
    assert response.status_code == 200


def test_upload_step__empty_comment(unpublished_update_url):
    """
    Test form complains on empty comment
    """
    # Set Up
    settings.DEFAULT_HOST = config.hosts.PUBLISH_HOST
    url, client = unpublished_update_url
    response = client.post(
        url,
        {
            "feed_update_wizard-current_step": DatasetUpdateModify.COMMENT_STEP,
            "wizard_goto_step": DatasetUpdateModify.COMMENT_STEP,
        },
    )
    assert response.status_code == 200
    assert (
        response.context["wizard"]["steps"].current == DatasetUpdateModify.COMMENT_STEP
    )

    # Test
    response = client.post(
        url,
        {
            "feed_update_wizard-current_step": DatasetUpdateModify.COMMENT_STEP,
            "comment": "",
            "submit": "submit",
        },
    )

    # Assert
    assert response.status_code == 200
    assert (
        response.context["form"].errors["comment"][0]
        == "Enter a comment in the box below"
    )
