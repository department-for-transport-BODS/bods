import pytest
from django.conf import settings

import config.hosts

pytestmark = pytest.mark.django_db

settings.IS_AVL_FEATURE_FLAG_ENABLED = True


def test_upload_step__empty_comment(unpublished_update_url):
    """
    Test form complains on empty comment
    """
    settings.DEFAULT_HOST = config.hosts.PUBLISH_HOST
    url, client, _ = unpublished_update_url
    response = client.post(
        url,
        {
            "avl_update_wizard-current_step": "comment",
            "comment-comment": "",
            "submit": "submit",
        },
    )
    assert response.status_code == 200
    assert (
        response.context["form"].errors["comment"][0]
        == "Enter a comment in the box below"
    )


def test_upload_step__duplicate_comment(unpublished_update_url):
    """
    Test form complains on duplicate comment
    """
    settings.DEFAULT_HOST = config.hosts.PUBLISH_HOST
    url, client, dataset = unpublished_update_url
    revision = dataset.revisions.first()
    comment = "another_test"
    revision.comment = comment
    revision.save()

    response = client.post(
        url,
        {
            "avl_update_wizard-current_step": "comment",
            "comment-comment": comment,
            "submit": "submit",
        },
    )
    assert response.status_code == 200
    assert (
        response.context["form"].errors["comment"][0]
        == "You have provided the same comment earlier "
        "for the dataset. Please provide a new comment"
    )
