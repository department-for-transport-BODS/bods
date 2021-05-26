import uuid
from typing import List, Tuple, Type

from django.db import transaction
from django.forms import Form
from django.http import Http404, HttpResponseRedirect
from django.utils.translation import gettext as _
from django.views.generic import TemplateView
from django_hosts import reverse

import config.hosts
from transit_odp.avl.forms import AVLFeedCommentForm, AvlFeedUploadForm
from transit_odp.avl.models import CAVLValidationTaskResult
from transit_odp.avl.tasks import task_validate_avl_feed
from transit_odp.organisation.models import Dataset, DatasetRevision
from transit_odp.publish.forms import FeedPublishCancelForm
from transit_odp.publish.views.timetable.update import FeedUpdateWizard
from transit_odp.users.views.mixins import OrgUserViewMixin


class AVLUpdateWizard(FeedUpdateWizard):
    COMMENT_STEP = "comment"
    UPLOAD_STEP = "upload"
    PUBLISH_CANCEL_STEP = "cancel"

    # Note the form_list needs to be available statically within the as_view() method,
    # so cannot add extra step cleanly within init
    form_list: List[Tuple[str, Type[Form]]] = [
        (COMMENT_STEP, AVLFeedCommentForm),
        (PUBLISH_CANCEL_STEP, FeedPublishCancelForm),
        (UPLOAD_STEP, AvlFeedUploadForm),
    ]

    step_context = {
        COMMENT_STEP: {"step_title": _("Add comment to your feed (optional)")},
        PUBLISH_CANCEL_STEP: {"step_title": _("Cancel step for publish")},
        UPLOAD_STEP: {"step_title": _("3. Choose how you want to publish your data")},
    }

    def get_object(self, queryset=None):
        queryset = Dataset.objects.filter(organisation_id=self.organisation.id)

        # Filter by dataset
        pk = self.kwargs.get(self.pk_url_kwarg)

        try:
            # Get the single item from the filtered queryset
            dataset = queryset.get(id=pk)
        except queryset.model.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": queryset.model._meta.verbose_name}
            )

        try:
            return dataset.revisions.get(is_published=False)
        except DatasetRevision.DoesNotExist:
            new_revision = dataset.start_revision()
            # clear out url_link from the
            new_revision.url_link = ""
            return new_revision

    def get_template_names(self):
        if self.request.POST.get("cancel", None) == self.PUBLISH_CANCEL_STEP:
            return "avl/feed_publish_cancel.html"
        return "avl/feed_form.html"

    def get_context_data(self, form, **kwargs):

        kwargs = super().get_context_data(form=form, **kwargs)
        kwargs.update(
            {
                "is_update": True,
                "title_tag_text": f"Update data feed: {kwargs.get('current_step')}",
            }
        )
        if self.request.POST.get("cancel", None) == self.PUBLISH_CANCEL_STEP:
            kwargs["previous_step"] = self.request.POST.get(
                "avl_update_wizard-current_step", None
            )

        return kwargs

    def get(self, request, *args, **kwargs):
        # Get feed object to update
        self.object = self.get_object()
        self.object.comment = None

        # Ensure GET returns the preview step
        self.storage.reset()
        return self.render(self.get_form())

    @transaction.atomic
    def done(self, form_list, **kwargs):
        all_data = self.get_all_cleaned_data()
        all_data.update({"last_modified_user": self.request.user})

        # assign data to revision
        revision = self.object
        for key, value in all_data.items():
            setattr(revision, key, value)

        # no longer use the status field to determine if the workflow is 'pending'
        revision.status = "success"
        revision.save()

        task_id = uuid.uuid4()
        CAVLValidationTaskResult.objects.create(
            revision=revision, task_id=task_id, status=CAVLValidationTaskResult.STARTED
        )
        transaction.on_commit(lambda: task_validate_avl_feed.delay(task_id))

        return HttpResponseRedirect(
            reverse(
                "avl:revision-update-publish",
                kwargs={"pk": self.kwargs["pk"], "pk1": self.kwargs["pk1"]},
                host=config.hosts.PUBLISH_HOST,
            )
        )


class DraftExistsView(OrgUserViewMixin, TemplateView):
    template_name = "avl/feed_existing_draft.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pk1"] = self.kwargs["pk1"]
        return context
