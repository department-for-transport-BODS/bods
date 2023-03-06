import logging
from typing import List, Optional, Tuple, Type, TypedDict

from django.db import transaction
from django.db.models import Q
from django.forms import Form
from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _
from django.views.generic import TemplateView
from django_hosts import reverse
from waffle import flag_is_active

import config.hosts
from transit_odp.fares.constants import ERROR_CODE_MAP
from transit_odp.fares.forms import FaresFeedUploadForm
from transit_odp.fares.tasks import task_run_fares_pipeline
from transit_odp.fares_validator.views.validate import FaresXmlValidator
from transit_odp.organisation.constants import DatasetType, FeedStatus
from transit_odp.organisation.models import DatasetMetadata, DatasetRevision
from transit_odp.pipelines.models import DatasetETLTaskResult
from transit_odp.publish.forms import FeedPublishCancelForm
from transit_odp.publish.views.base import BaseDatasetUploadModify, ReviewBaseView
from transit_odp.users.views.mixins import OrgUserViewMixin
from transit_odp.validate.errors import XMLErrorMessageRenderer

logger = logging.getLogger(__name__)


class ReviewView(ReviewBaseView):
    template_name = "fares/review/index.html"

    class Properties(TypedDict):
        dataset_id: int
        name: str
        description: str
        short_description: str
        status: str
        owner_name: str
        url_link: str
        last_modified: str
        last_modified_user: str
        api_root: str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_dataset_queryset(self):
        """Returns a DatasetQuerySet for Fares datasets owned by the user's
        organisation.
        """
        queryset = super().get_dataset_queryset()
        return queryset.filter(dataset_type=DatasetType.FARES)

    # TODO: change this code when we have the progress bar in place
    def get_validation_task_result(self) -> Optional[DatasetETLTaskResult]:
        try:
            task = DatasetETLTaskResult.objects.filter(revision=self.object).latest(
                "created"
            )
        except DatasetETLTaskResult.DoesNotExist:
            logger.warning(
                f"Could not find DatasetETLTaskResult for revision: {self.object}",
                exc_info=True,
            )
            return None

        return task

    def get_error(self):
        error_message = None
        task = self.get_validation_task_result()

        if task is None:
            return None

        if task.additional_info is not None:
            renderer = XMLErrorMessageRenderer(
                task.additional_info, error_code=task.error_code
            )
            error_message = {"description": renderer.get_message()}

        if error_message is None:
            error_message = ERROR_CODE_MAP.get(task.error_code, None)

        return error_message

    def get_upload_file(self, revision_id):
        revision = DatasetRevision.objects.get(id=revision_id)
        upload_file = revision.upload_file
        return upload_file

    def set_validator_error(self, revision_id):
        upload_file = self.get_upload_file(revision_id)

        fares_validator_obj = FaresXmlValidator(
            upload_file, self.kwargs["pk1"], revision_id
        )
        fares_validator_response = fares_validator_obj.set_errors()

        if fares_validator_response.status_code == 201:
            return True
        return False

    def get_validator_error(self, revision_id):
        upload_file = self.get_upload_file(revision_id)

        fares_validator_obj = FaresXmlValidator(
            upload_file, self.kwargs["pk1"], revision_id
        )
        fares_validator_errors = fares_validator_obj.get_errors()
        fares_validator_errors_list = fares_validator_errors.content.decode(
            "utf8"
        ).replace("'", '"')

        if fares_validator_errors_list == "[]":
            return False
        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        revision = self.object

        # Get the status of the Fares validation process
        is_loading = self.is_loading()
        context["loading"] = is_loading

        context["current_step"] = "upload" if is_loading else "review"

        # Get the error info
        context["error"] = self.get_error()

        is_fares_validator_active = flag_is_active(
            self.request, "is_fares_validator_active"
        )
        if is_fares_validator_active:
            # Get the fares-validator error info
            if (
                not is_loading
                and context["error"] is None
                and not self.get_validator_error(revision.id)
            ):
                context["validator_error"] = self.set_validator_error(revision.id)
            else:
                context["validator_error"] = self.get_validator_error(revision.id)

            context["pk2"] = revision.id

        api_root = reverse("api:app:api-root", host=config.hosts.DATA_HOST)

        context["pk1"] = self.kwargs["pk1"]

        last_modified_username = None
        if revision.last_modified_user is not None:
            last_modified_username = revision.last_modified_user.username

        try:
            context["metadata"] = revision.metadata.faresmetadata
        except DatasetMetadata.DoesNotExist:
            # We'll end up here will the fares validation task is running
            pass

        context["properties"] = ReviewView.Properties(
            dataset_id=revision.dataset.id,
            name=revision.name,
            description=revision.description,
            short_description=revision.short_description,
            status=revision.status,
            owner_name=revision.dataset.organisation.name,
            url_link=revision.url_link,
            last_modified=revision.modified,
            last_modified_user=last_modified_username,
            api_root=api_root,
        )

        return context

    def get_success_url(self):
        dataset_id = self.object.dataset_id
        return reverse(
            "fares:revision-publish-success",
            kwargs={"pk": dataset_id, "pk1": self.kwargs["pk1"]},
            host=config.hosts.PUBLISH_HOST,
        )


class RevisionPublishSuccessView(OrgUserViewMixin, TemplateView):
    template_name = "fares/revision_publish_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"update": False, "pk1": self.kwargs["pk1"]})
        return context


class RevisionUpdateSuccessView(RevisionPublishSuccessView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"update": True, "pk1": self.kwargs["pk1"]})
        return context


class UpdateRevisionPublishView(ReviewView):
    template_name = "fares/review/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"is_update": True})
        return context

    def get_success_url(self):
        dataset_id = self.object.dataset_id
        return reverse(
            "fares:revision-update-success",
            kwargs={"pk": dataset_id, "pk1": self.kwargs["pk1"]},
            host=config.hosts.PUBLISH_HOST,
        )


class FaresDatasetUploadModify(BaseDatasetUploadModify):
    dataset = None
    PUBLISH_CANCEL_STEP = "cancel"
    UPLOAD_STEP = "upload"

    form_list: List[Tuple[str, Type[Form]]] = [
        (PUBLISH_CANCEL_STEP, FeedPublishCancelForm),
        (UPLOAD_STEP, FaresFeedUploadForm),
    ]

    step_context = {
        PUBLISH_CANCEL_STEP: {"step_title": _("Cancel step for publish")},
        UPLOAD_STEP: {"step_title": _("Choose how you want to publish your data")},
    }

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs.update(
            {
                "title_tag_text": f"Provide data: {kwargs.get('current_step')}",
                "is_revision_modify": True,
            }
        )

        if self.request.POST.get("cancel", None) == self.PUBLISH_CANCEL_STEP:
            kwargs["previous_step"] = self.request.POST.get(
                "fares_dataset_upload_modify-current_step", None
            )

        return kwargs

    def get_template_names(self):
        if self.request.POST.get("cancel", None) == self.PUBLISH_CANCEL_STEP:
            return "fares/feed_publish_cancel.html"
        return "fares/feed_form.html"

    @transaction.atomic
    def done(self, form_list, **kwargs):
        all_data = self.get_all_cleaned_data()
        dataset = self.get_dataset()
        draft_revision = dataset.revisions.get_draft().first()
        if draft_revision is None:
            comment = "First publication"
        else:
            comment = draft_revision.comment
        all_data.update({"last_modified_user": self.request.user, "comment": comment})

        revision = DatasetRevision.objects.filter(
            Q(dataset=dataset) & Q(is_published=False)
        ).update_or_create(dataset=dataset, is_published=False, defaults=all_data)[0]

        if not revision.status == FeedStatus.pending.value:
            revision.to_pending()
            revision.save()

        transaction.on_commit(lambda: task_run_fares_pipeline.delay(revision.id))

        return HttpResponseRedirect(
            reverse(
                "fares:revision-update-publish",
                kwargs={"pk": dataset.id, "pk1": dataset.organisation_id},
                host=config.hosts.PUBLISH_HOST,
            )
        )
