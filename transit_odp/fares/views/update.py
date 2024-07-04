from typing import List, Tuple, Type

from django.db import transaction
from django.forms import Form
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views.generic.detail import SingleObjectMixin
from django_hosts import reverse
from waffle import flag_is_active

import config.hosts
from transit_odp.browse.views.base_views import BaseTemplateView
from transit_odp.fares.forms import FaresFeedCommentForm, FaresFeedUploadForm
from transit_odp.fares.tasks import task_run_fares_pipeline
from transit_odp.fares_validator.models import FaresValidationResult
from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.models import Dataset, DatasetRevision
from transit_odp.publish.forms import FeedPublishCancelForm
from transit_odp.publish.views.base import FeedWizardBaseView
from transit_odp.users.views.mixins import OrgUserViewMixin


class RevisionUpdateSuccessView(OrgUserViewMixin, BaseTemplateView):
    template_name = "fares/revision_publish_success.html"

    def get_count(self, dataset_id):
        live_revision_id = list(
            Dataset.objects.filter(id=dataset_id).values_list(
                "live_revision_id", flat=True
            )
        )
        count_list = list(
            FaresValidationResult.objects.filter(
                revision_id=live_revision_id[0]
            ).values_list("count", flat=True)
        )
        return count_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"update": True, "pk1": self.kwargs["pk1"]})
        is_fares_validator_active = flag_is_active(
            self.request, "is_fares_validator_active"
        )
        if is_fares_validator_active:
            count = self.get_count(self.kwargs["pk"])

            if count[0] != 0:
                context.update({"validator_error": True})
            else:
                context.update({"validator_error": False})
        return context


class FeedUpdateWizard(SingleObjectMixin, FeedWizardBaseView):
    COMMENT_STEP = "comment"
    UPLOAD_STEP = "upload"
    PUBLISH_CANCEL_STEP = "cancel"

    # Note the form_list needs to be available statically within the as_view() method,
    # so cannot add extra step cleanly within init
    form_list: List[Tuple[str, Type[Form]]] = [
        (COMMENT_STEP, FaresFeedCommentForm),
        (PUBLISH_CANCEL_STEP, FeedPublishCancelForm),
        (UPLOAD_STEP, FaresFeedUploadForm),
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

        return dataset.start_revision()

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        wizard_goto_step = self.request.POST.get("wizard_goto_step", None)

        if (
            self.request.POST.get("cancel", None) == self.PUBLISH_CANCEL_STEP
        ) and not wizard_goto_step:
            self.storage.current_step = self.PUBLISH_CANCEL_STEP
            return self.render_goto_step(self.storage.current_step)

        return super().post(*args, **kwargs)

    def get_template_names(self):
        if self.request.POST.get("cancel", None) == self.PUBLISH_CANCEL_STEP:
            return "fares/feed_publish_cancel.html"
        return "fares/feed_form.html"

    def get_next_step(self, step=None):
        if self.steps.current == self.COMMENT_STEP:
            return self.UPLOAD_STEP

        return None

    def get_queryset(self):
        return DatasetRevision.objects.filter(
            dataset__organisation_id=self.organisation.id
        ).get_live_revisions()

    def get(self, request, *args, **kwargs):
        # Get feed object to update
        self.object = self.get_object()
        self.object.comment = None

        # prevent user from trying to update dataset with existing draft, regardless of
        # how they got to this page
        if self.object.dataset.revisions.filter(
            status__in=[FeedStatus.draft.value, FeedStatus.success.value]
        ).exists():
            return redirect(
                "fares:feed-draft-exists",
                pk=self.object.dataset_id,
                pk1=self.object.dataset.organisation_id,
            )
        else:
            # Ensure GET returns the preview step
            is_fares_validator_active = flag_is_active(
                self.request, "is_fares_validator_active"
            )
            if is_fares_validator_active:
                self.object.dataset.start_revision()
            self.storage.reset()
            return self.render(self.get_form())

    def get_form_kwargs(self, step=None):
        return {"is_update": True}

    def get_step_data(self, step):
        step_data = self.storage.get_step_data(step)

        if not step_data:
            return None

        if step == self.COMMENT_STEP:
            return step_data.get("comment-comment", None)

        elif step == self.UPLOAD_STEP:
            return step_data.get("upload-upload", None)

        return None

    def get_context_data(self, form, **kwargs):
        kwargs = super().get_context_data(form=form, **kwargs)
        kwargs.update(
            {
                "is_update": True,
                "title_tag_text": f"Update data set: {kwargs.get('current_step')}",
                "pk1": self.kwargs["pk1"],
            }
        )
        if self.request.POST.get("cancel", None) == self.PUBLISH_CANCEL_STEP:
            kwargs["previous_step"] = self.request.POST.get(
                "feed_update_wizard-current_step", None
            )

        return kwargs

    def get_form_instance(self, step):
        """Returns the Feed instance to bind to the step's form"""
        return self.object

    @transaction.atomic
    def done(self, form_list, **kwargs):
        all_data = self.get_all_cleaned_data()
        all_data.update({"last_modified_user": self.request.user})

        # assign data to revision
        revision = self.object
        for key, value in all_data.items():
            setattr(revision, key, value)
        revision.save()

        if not revision.status == FeedStatus.pending.value:
            revision.to_pending()
            revision.save()

        transaction.on_commit(lambda: task_run_fares_pipeline.delay(revision.id))

        return HttpResponseRedirect(
            reverse(
                "fares:revision-update-publish",
                kwargs={"pk": self.kwargs["pk"], "pk1": self.kwargs["pk1"]},
                host=config.hosts.PUBLISH_HOST,
            )
        )


class DatasetUpdateModify(FeedUpdateWizard):
    dataset = None
    PUBLISH_CANCEL_STEP = "cancel"
    UPLOAD_STEP = "upload"

    form_list: List[Tuple[str, Type[Form]]] = [
        (PUBLISH_CANCEL_STEP, FeedPublishCancelForm),
        (UPLOAD_STEP, FaresFeedUploadForm),
    ]

    step_context = {
        PUBLISH_CANCEL_STEP: {"step_title": _("Cancel step for update")},
        UPLOAD_STEP: {"step_title": _("Choose how you want to update your data")},
    }

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.storage.current_step = self.UPLOAD_STEP
        return self.render(self.get_form())

    def get_dataset(self):
        # Filter by dataset
        pk = self.kwargs.get(self.pk_url_kwarg)

        try:
            # Get the single item from the filtered queryset
            dataset = Dataset.objects.get(id=pk)
        except self.queryset.model.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": self.queryset.model._meta.verbose_name}
            )
        return dataset

    def get_form_kwargs(self, step=None):
        return {"is_revision_modify": True}

    def get_queryset(self):
        return DatasetRevision.objects.filter(
            dataset__organisation_id=self.organisation.id
        )

    def get_context_data(self, form, **kwargs):
        kwargs = super().get_context_data(form=form, **kwargs)
        kwargs.update(
            {
                "is_revision_modify": True,
                "title_tag_text": f"Update data set: {kwargs.get('current_step')}",
            }
        )
        if self.request.POST.get("cancel", None) == self.PUBLISH_CANCEL_STEP:
            kwargs["previous_step"] = self.request.POST.get(
                "dataset_update_modify-current_step", None
            )

        return kwargs

    def get_object(self, queryset=None):
        queryset = Dataset.objects.filter(organisation_id=self.organisation.id)

        try:
            # Get the single item from the filtered queryset
            self.dataset = self.get_dataset()
            revision = self.dataset.revisions.get(is_published=False)
        except queryset.model.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": DatasetRevision._meta.verbose_name}
            )
        if revision is not None:
            return revision


class DraftExistsView(OrgUserViewMixin, BaseTemplateView):
    template_name = "fares/feed_existing_draft.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pk1"] = self.kwargs["pk1"]
        return context
