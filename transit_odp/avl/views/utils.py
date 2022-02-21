import logging

from django_hosts import reverse

import config.hosts
from transit_odp.avl.models import CAVLValidationTaskResult

logger = logging.getLogger(__name__)


def get_validation_task_result_from_revision_id(revision_id):
    try:
        task = CAVLValidationTaskResult.objects.filter(revision_id=revision_id).latest(
            "created"
        )
    except CAVLValidationTaskResult.DoesNotExist:
        logger.warning(
            f"Could not find CAVLValidationTaskResult for revision: {revision_id}",
            exc_info=True,
        )
        return None

    return task


def get_avl_success_url(dataset_id, org_id):
    return reverse(
        "avl:revision-publish-success",
        kwargs={"pk": dataset_id, "pk1": org_id},
        host=config.hosts.PUBLISH_HOST,
    )


def get_avl_failure_url(dataset_id, org_id):
    return reverse(
        "avl:revision-publish-error",
        kwargs={"pk": dataset_id, "pk1": org_id},
        host=config.hosts.PUBLISH_HOST,
    )
