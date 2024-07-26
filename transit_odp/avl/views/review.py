import logging
from typing import TypedDict

from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django_hosts import reverse

import config.hosts
from transit_odp.avl.models import CAVLValidationTaskResult
from transit_odp.avl.views.utils import (
    get_avl_failure_url,
    get_avl_success_url,
    get_validation_task_result_from_revision_id,
)
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models import Dataset
from transit_odp.publish.views.base import ReviewBaseView
from transit_odp.users.views.mixins import OrgUserViewMixin

logger = logging.getLogger(__name__)

SYSTEM_ERROR = (
    "Something went wrong and we could not "
    "process your data feed. Please try again later."
)
TIMEOUT_ERROR = "Timeout - please try again later or contact support"
INVALID = "We could not process your data. </br> SIRI-VM check status request failed."

ERROR_DESCRIPTIONS = {
    CAVLValidationTaskResult.TIMEOUT_ERROR: TIMEOUT_ERROR,
    CAVLValidationTaskResult.SYSTEM_ERROR: SYSTEM_ERROR,
    CAVLValidationTaskResult.INVALID: INVALID,
}


class ReviewView(ReviewBaseView):
    template_name = "avl/review/index.html"

    class Properties(TypedDict):
        dataset_id: int
        name: str
        description: str
        short_description: str
        status: str
        owner_name: str
        siri_version: str
        url_link: str
        last_modified: str
        last_modified_user: str
        last_server_update: str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(
            {"consent_label": "I have reviewed the data and wish to publish my data"}
        )
        return kwargs

    def get_dataset_queryset(self):
        """Returns a DatasetQuerySet for AVL datasets owned by the user's
        organisation"""
        queryset = super().get_dataset_queryset()
        return queryset.filter(dataset_type=DatasetType.AVL)

    def is_loading(self):
        """Gets the state of the AVL validation process"""
        task = get_validation_task_result_from_revision_id(self.object.id)
        return not (task and task.result)

    def get_error(self):
        """If an error exists get the error description."""
        task = get_validation_task_result_from_revision_id(self.object.id)

        if task is None:
            return None

        description = ERROR_DESCRIPTIONS.get(task.result, None)
        if description is None:
            return None

        return {"description": description}

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        revision = self.object

        # Get the status of the AVL validation process
        is_loading = self.is_loading()
        context["loading"] = is_loading

        context["current_step"] = "upload" if is_loading else "review"
        context["title_tag_text"] = f"Provide data: {kwargs.get('current_step')}"
        # Get the error info
        context["error"] = self.get_error()

        context["pk1"] = self.kwargs["pk1"]

        last_modified_username = None
        if revision.last_modified_user is not None:
            last_modified_username = revision.last_modified_user.username

        if hasattr(revision, "metadata"):
            siri_version = revision.metadata.schema_version
        else:
            siri_version = "_"

        context["properties"] = ReviewView.Properties(
            dataset_id=revision.dataset.id,
            name=revision.name,
            description=revision.description,
            short_description=revision.short_description,
            status=revision.status,
            owner_name=revision.dataset.organisation.name,
            siri_version=siri_version,
            url_link=revision.url_link,
            last_modified=revision.modified,
            last_modified_user=last_modified_username,
            last_server_update="",
        )

        return context

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except Exception:
            # If publication fails redirect user to error page
            return HttpResponseRedirect(self.get_failure_url())

    def get_success_url(self):
        return get_avl_success_url(self.object.dataset_id, self.kwargs["pk1"])

    def get_failure_url(self):
        return get_avl_failure_url(self.object.dataset_id, self.kwargs["pk1"])


class RevisionPublishSuccessView(OrgUserViewMixin, DetailView):
    template_name = "avl/revision_publish_success.html"
    model = Dataset
    pk_url_kwarg = "pk"

    def get_context_data(self, **kwargs):
        if self.get_object().revisions.count() > 1:
            update = True
        else:
            update = False
        context = super().get_context_data(**kwargs)
        context.update({"update": update, "pk1": self.kwargs["pk1"]})
        return context


class PublishErrorView(OrgUserViewMixin, TemplateView):
    """
    This is a generic error page to show something went wrong while publishing
    a revision

    Note: This is necessary for AVL datasets which require an interaction with the
    CAVL service which may fail upon publishing the changes.
    """

    template_name = "avl/revision_publish_error.html"

    class Properties(TypedDict):
        backlink: str

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        dataset_id = self.kwargs["pk"]

        context.update(
            self.Properties(
                backlink=reverse(
                    "avl:revision-publish",
                    kwargs={"pk": dataset_id, "pk1": self.kwargs["pk1"]},
                    host=config.hosts.PUBLISH_HOST,
                )
            )
        )

        return context


class RevisionUpdateSuccessView(RevisionPublishSuccessView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"update": True, "pk1": self.kwargs["pk1"]})
        return context


class UpdateRevisionPublishView(ReviewView):
    template_name = "avl/review/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"is_update": True, "pk1": self.kwargs["pk1"]})
        return context

    def get_success_url(self):
        return reverse(
            "avl:revision-update-success",
            kwargs={"pk": self.kwargs["pk"], "pk1": self.kwargs["pk1"]},
            host=config.hosts.PUBLISH_HOST,
        )
