import logging
from uuid import uuid4

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse

from transit_odp.common.utils.aws_common import StepFunctionsClientWrapper
from transit_odp.organisation.constants import FeedStatus
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.publish.views.utils import create_state_machine_payload

logger = logging.getLogger(__name__)


def delete_tt_existing_revision_data(revision):
    """
    Delete any existing violations for the given revision id.
    This allows validation to occur multiple times for the same DatasetRevision
    Includes: SchemaViolation, PostSchemaViolation, PTIObservation, TXCFileAttributes and ServicePattern objects
    Cascade deletes so that other related objects ex-Service, dqstasks,etc. are also deleted
    """
    revision.schema_violations.all().delete()
    revision.post_schema_violations.all().delete()
    revision.txc_file_attributes.all().delete()
    revision.pti_observations.all().delete()
    revision.service_patterns.all().delete()
    revision.dqs_report.all().delete()


def delete_fares_existing_revision_data(revision):
    """
    Delete any existing violations for the given revision id.
    This allows validation to occur multiple times for the same DatasetRevision
    Includes: SchemaViolation, FaresValidation, FaresValidationResult
    ****DataCatalogueMetaData is also deleted but it does not have a foreign key constraint to revision***
    """
    revision.schema_violations.all().delete()
    revision.fares_validations.all().delete()
    revision.fares_validation_result.all().delete()
    revision.metadata.all().delete()
    # DataCatalogueMetaData is also deleted but it does not have a foreign key constraint to revision


def trigger_state_machine(revision, dataset_type, do_publish: bool = False):
    """
    Prepare payload and trigger the state machine
    """
    with transaction.atomic():
        if not revision.status == FeedStatus.pending.value:
            revision.to_pending()
            revision.save()
        task = DatasetETLTaskResult.objects.create(
            revision=revision,
            status=DatasetETLTaskResult.STARTED,
            task_id=str(uuid4()),
        )

    try:
        # trigger state machine
        step_fucntions_client = StepFunctionsClientWrapper()
        if dataset_type == "timetables":
            # 'Update data' flow allows validation to occur multiple times
            # Delete relevant dataset data
            if not do_publish:
                delete_tt_existing_revision_data(revision)
            input_payload = create_state_machine_payload(
                revision, task.id, do_publish, "timetables"
            )
            step_function_arn = settings.TIMETABLES_STATE_MACHINE_ARN
        elif dataset_type == "fares":
            if not do_publish:
                delete_fares_existing_revision_data(revision)
            input_payload = create_state_machine_payload(
                revision, task.id, do_publish, "fares"
            )
            step_function_arn = settings.FARES_STATE_MACHINE_ARN
        else:
            raise ValueError("Invalid dataset type provided.")

        if not step_function_arn:
            logger.error(
                f"{dataset_type.capitalize()} pipeline: AWS Step Function ARN is missing or invalid"
            )
            raise ValueError(
                f"{dataset_type.capitalize()} pipeline: AWS Step Function ARN is missing or invalid"
            )

        # Invoke the Step Function
        step_fucntions_client.start_step_function(input_payload, step_function_arn)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
