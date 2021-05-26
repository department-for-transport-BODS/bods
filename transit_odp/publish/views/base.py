from collections import OrderedDict
from typing import List, Tuple, Type

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.db.models.query_utils import Q
from django.forms import Form
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import DetailView, TemplateView, UpdateView
from django.views.generic.detail import SingleObjectMixin
from django_hosts import reverse
from formtools.wizard.views import SessionWizardView

import config.hosts
from transit_odp.bods.interfaces.plugins import get_notifications
from transit_odp.common.forms import ConfirmationForm
from transit_odp.common.view_mixins import BODSBaseView
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models import Dataset, DatasetRevision
from transit_odp.publish.forms import (
    FeedDescriptionForm,
    FeedPublishCancelForm,
    FeedUploadForm,
    RevisionPublishForm,
)
from transit_odp.users.models import AgentUserInvite
from transit_odp.users.views.mixins import OrgUserViewMixin


class BaseTemplateView(BODSBaseView, TemplateView):
    pass


class BaseDetailView(BODSBaseView, DetailView):
    pass


class BaseUpdateView(BODSBaseView, UpdateView):
    pass


class PublishFeedDetailViewBase(BaseDetailView):
    """Baseclass to use for all child routes of the /feed/<int:pk>/

    Filters Feed queryset to those 'owned by organisation' to lookup feed pk.
    """

    model = Dataset

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                organisation_id=self.organisation.id,
            )
            .add_live_data()
            .select_related("live_revision")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"pk1": self.kwargs["pk"]})
        return context


class FeedWizardBaseView(BODSBaseView, OrgUserViewMixin, SessionWizardView):
    DESCRIPTION_STEP = "description"
    PUBLISH_CANCEL_STEP = "cancel"
    UPLOAD_STEP = "upload"

    form_list: List[Tuple[str, Type[Form]]] = [
        (DESCRIPTION_STEP, FeedDescriptionForm),
        (PUBLISH_CANCEL_STEP, FeedPublishCancelForm),
        (UPLOAD_STEP, FeedUploadForm),
    ]

    step_context = {
        DESCRIPTION_STEP: {"step_title": _("Describe your data set")},
        PUBLISH_CANCEL_STEP: {"step_title": _("Cancel step for publish")},
        UPLOAD_STEP: {"step_title": _("Choose how you want to publish your data")},
    }

    file_storage = FileSystemStorage(location=settings.MEDIA_ROOT + "/tmp")

    def get_context_data(self, form, **kwargs):
        kwargs = super().get_context_data(form, **kwargs)
        kwargs.update(self.step_context[self.steps.current])
        kwargs.update({"form_list": list(self.form_list.items())[0:3]})
        kwargs.update({"current_step": self.steps.current, "pk1": self.kwargs["pk1"]})
        return kwargs

    def get_form_initial(self, step):
        kwargs = super().get_form_initial(step)
        # Initialise form with stored step data
        stored = self.storage.get_step_data(step) or {}
        kwargs.update(**stored)
        return kwargs

    def render_done(self, form, **kwargs):
        final_forms = OrderedDict()
        # walk through the form list and try to validate the data again.
        for form_key in self.get_form_list():
            form_obj = self.get_form(
                step=form_key,
                data=self.storage.get_step_data(form_key),
                files=self.storage.get_step_files(form_key),
            )
            if not form_obj.is_valid() and form_key != self.PUBLISH_CANCEL_STEP:
                return self.render_revalidation_failure(form_key, form_obj, **kwargs)
            final_forms[form_key] = form_obj

        done_response = self.done(final_forms.values(), form_dict=final_forms, **kwargs)
        self.storage.reset()
        return done_response


class ReviewBaseView(OrgUserViewMixin, BaseUpdateView):
    """The base view of all review pages"""

    model = DatasetRevision
    form_class = RevisionPublishForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pk1"] = self.kwargs["pk1"]
        return context

    def get_dataset_queryset(self):
        """Returns a DatasetQuerySet for Datasets owned by the user's organisation"""
        return Dataset.objects.filter(organisation_id=self.organisation.id)

    def get_dataset(self):
        """Get Dataset using URL parameter"""
        try:
            pk = self.kwargs.get(self.pk_url_kwarg)
            queryset = self.get_dataset_queryset()
            return queryset.get(id=pk)
        except Dataset.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": Dataset._meta.verbose_name}
            )

    def get_queryset(self):
        """Returns a QuerySet of DatasetRevisions"""
        dataset = self.get_dataset()
        queryset = dataset.revisions.select_related("dataset__organisation")
        return queryset

    def get_object(self, queryset=None):
        queryset = self.get_queryset()
        try:
            self.object = queryset.get(is_published=False)
            return self.object
        except DatasetRevision.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": DatasetRevision._meta.verbose_name}
            )

    def form_valid(self, form):
        revision = self.get_object()
        if not revision.is_published:
            revision.publish(self.request.user)
        return HttpResponseRedirect(self.get_success_url())

    def is_loading(self):
        revision = self.object
        status = revision.status
        return status == "indexing" or status == "processing" or status == "pending"


class DeleteRevisionBaseView(OrgUserViewMixin, BaseUpdateView):
    model = Dataset
    form_class = ConfirmationForm
    revision_name = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        revision = self.object.revisions.latest()
        if not revision.is_published:
            self.revision_name = revision.name

        context.update({"revision_name": self.revision_name, "pk1": self.kwargs["pk1"]})
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        feed_id = self.object.id
        kwargs.update({"label": "Delete", "cancel_url": self.get_cancel_url(feed_id)})
        kwargs.pop("instance", None)
        return kwargs

    def get_cancel_url(self, feed_id):
        pass

    def form_valid(self, form):
        client = get_notifications()
        dataset = self.get_object()
        revision = dataset.revisions.latest()

        # Delete revision
        if not revision.is_published:

            try:
                DatasetRevision.objects.get(id=revision.id).delete()

            except DatasetRevision.DoesNotExist:
                # This shouldnt happen but we dont want to break the site if it does
                pass

            else:
                client.send_data_endpoint_deleted_deleter_notification(
                    dataset_id=dataset.id,
                    dataset_name=revision.name,
                    contact_email=self.request.user.email,
                )
                client.send_data_endpoint_deleted_updater_notification(
                    dataset_id=dataset.id,
                    contact_email=dataset.contact.email,
                    dataset_name=revision.name,
                    last_updated=revision.modified,
                )

        return HttpResponseRedirect(self.get_success_url())


class FeedArchiveBaseView(OrgUserViewMixin, BaseUpdateView):
    form_class = ConfirmationForm
    model = Dataset
    app_name = None
    dataset_type = None

    def get_back_url(self):
        return reverse(
            f"{self.viewname_prefix}feed-detail",
            host=self.request.host.name,
            kwargs={"pk": self.object.id, "pk1": self.object.organisation_id},
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"pk1": self.kwargs["pk1"], "backlink": self.get_back_url()})
        return context

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                organisation_id=self.organisation.id,
                dataset_type=self.dataset_type,
            )
            .get_active()
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        feed_id = self.object.id

        kwargs.update(
            {
                "cancel_url": reverse(
                    f"{self.viewname_prefix}feed-detail",
                    host=self.request.host.name,
                    kwargs={"pk": feed_id, "pk1": self.object.organisation_id},
                )
            }
        )
        kwargs.pop("instance", None)
        return kwargs

    def get_success_url(self):
        feed_id = self.object.id

        return reverse(
            f"{self.viewname_prefix}feed-archive-success",
            kwargs={"pk": feed_id, "pk1": self.kwargs["pk1"]},
            host=config.hosts.PUBLISH_HOST,
        )

    def form_valid(self, form):
        client = get_notifications()
        dataset = self.get_object()
        dataset_revision = dataset.live_revision
        user = self.request.user

        # set published revision to 'inactive'
        dataset_revision.to_inactive()
        dataset_revision.last_modified_user = user
        dataset_revision.save()
        now = timezone.now()

        # delete draft revisions of the dataset
        draft_revisions = dataset.revisions.exclude(id=dataset_revision.id).filter(
            is_published=False
        )
        draft_revisions.delete()

        if not dataset.contact.is_agent_user:
            # If the normal user flow is respected (ie adding through invites)
            # then we can assume that if an organisations user is an agent
            # then they must be an agent for that organisation. Mixed accounts
            # are not supported.
            client.send_data_endpoint_deactivated_notification(
                dataset_id=dataset.id,
                dataset_name=dataset.live_revision.name,
                short_description=dataset.live_revision.short_description,
                contact_email=dataset.contact.email,
                published_at=dataset.live_revision.published_at,
                expired_at=now,
            )

        for agent in dataset.organisation.agentuserinvite_set.filter(
            status=AgentUserInvite.ACCEPTED
        ):
            client.send_agent_data_endpoint_deactivated_notification(
                dataset_id=dataset.id,
                dataset_name=dataset.live_revision.name,
                contact_email=agent.email,
                operator_name=dataset.organisation.name,
                short_description=dataset.live_revision.short_description,
                published_at=dataset.live_revision.published_at,
                expired_at=now,
            )

        for developer in dataset.subscribers.exclude(
            settings__mute_all_dataset_notifications=True
        ).order_by("id"):
            client.send_developer_data_endpoint_expired_notification(
                dataset_id=dataset.id,
                dataset_name=dataset.live_revision.name,
                short_description=dataset.live_revision.short_description,
                contact_email=developer.email,
                published_at=dataset.live_revision.published_at,
                expired_at=now,
            )

        return HttpResponseRedirect(self.get_success_url())

    @property
    def viewname_prefix(self):
        return "" if self.app_name is None else f"{self.app_name}:"


class FeedArchiveSuccessBaseView(OrgUserViewMixin, PublishFeedDetailViewBase):
    template_name = "publish/feed_archive_success.html"

    def back_to_data_sets_url(self):
        viewname_prefix = "" if self.app_name is None else f"{self.app_name}:"
        return reverse(
            f"{viewname_prefix}feed-list",
            kwargs={"pk1": self.kwargs["pk1"]},
            host=config.hosts.PUBLISH_HOST,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_to_data_sets"] = self.back_to_data_sets_url()
        return context


class EditDescriptionBaseView(OrgUserViewMixin, BaseUpdateView):
    model = Dataset
    dataset_type: DatasetType
    object: DatasetRevision

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                organisation_id=self.organisation.id,
                dataset_type=self.dataset_type,
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        revision_name = self.object.name
        if len(revision_name) > 20:
            revision_name = revision_name[:19] + "..."
        context.update({"pk1": self.kwargs["pk1"], "revision_name": revision_name})
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"instance": self.object})
        return kwargs

    def post(self, request, *args, **kwargs):
        if self.request.POST.get("cancel", None) == "cancel":
            return redirect(self.get_cancel_url())
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        self.object.description = form.cleaned_data["description"]
        self.object.short_description = form.cleaned_data["short_description"]
        self.object.save()
        return redirect(self.get_success_url())

    def get_dataset_url(self):
        pass

    def get_success_url(self):
        return self.get_dataset_url()

    def get_cancel_url(self):
        return self.get_dataset_url()


class BaseFeedUploadWizard(FeedWizardBaseView):
    def get_template_names(self):
        if self.request.POST.get("cancel", None) == self.PUBLISH_CANCEL_STEP:
            return "publish/feed_publish_cancel.html"
        return "publish/feed_form.html"

    def get_step_data(self, step):
        step_data = self.storage.get_step_data(step)
        if not step_data:
            return None
        if step == self.DESCRIPTION_STEP:
            return step_data.get("description-description", None)
        elif step == self.UPLOAD_STEP:
            return step_data.get("upload-upload", None)

        return None

    def get_context_data(self, form, **kwargs):
        kwargs = super().get_context_data(form, **kwargs)
        kwargs.update(
            {
                "title_tag_text": f"Publish new data set: {kwargs.get('current_step')}",
                "pk1": self.kwargs["pk1"],
            }
        )

        if self.request.POST.get("cancel", None) == self.PUBLISH_CANCEL_STEP:
            kwargs["previous_step"] = self.request.POST.get(
                "feed_upload_wizard-current_step", None
            )
        return kwargs

    def get_next_step(self, step=None):
        if self.steps.current == self.DESCRIPTION_STEP:
            return self.UPLOAD_STEP

        return None

    def step_was_modified(self, step):
        if step == self.UPLOAD_STEP:
            return True
        cleaned_data = self.storage.get_step_data(step)
        return cleaned_data is not None

    def post(self, *args, **kwargs):
        wizard_goto_step = self.request.POST.get("wizard_goto_step", None)

        if (
            self.request.POST.get("cancel", None) == self.PUBLISH_CANCEL_STEP
        ) and not wizard_goto_step:
            self.storage.current_step = self.PUBLISH_CANCEL_STEP
            return self.render_goto_step(self.storage.current_step)

        return super().post(*args, **kwargs)

    def get_dataset(self):
        return Dataset.objects.create(
            contact=self.request.user, organisation=self.organisation
        )

    @transaction.atomic
    def done(self, form_list, **kwargs):
        all_data = self.get_all_cleaned_data()
        dataset = self.get_dataset()
        all_data.update(
            {"last_modified_user": self.request.user, "comment": "First publication"}
        )

        revision = DatasetRevision.objects.filter(
            Q(dataset=dataset) & Q(is_published=False)
        ).update_or_create(dataset=dataset, is_published=False, defaults=all_data)[0]

        # trigger ETL job to run
        revision.start_etl()

        return HttpResponseRedirect(
            reverse(
                "revision-publish",
                kwargs={"pk": dataset.id, "pk1": dataset.organisation_id},
                host=config.hosts.PUBLISH_HOST,
            )
        )


class BaseDatasetUploadModify(SingleObjectMixin, BaseFeedUploadWizard):
    dataset = None
    PUBLISH_CANCEL_STEP = "cancel"
    UPLOAD_STEP = "upload"

    form_list: List[Tuple[str, Type[Form]]] = [
        (PUBLISH_CANCEL_STEP, FeedPublishCancelForm),
        (UPLOAD_STEP, FeedUploadForm),
    ]

    step_context = {
        PUBLISH_CANCEL_STEP: {"step_title": _("Cancel step for publish")},
        UPLOAD_STEP: {"step_title": _("Choose how you want to publish your data")},
    }

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        # self.dataset = self.get_dataset()
        # reset the current step to the first step.
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

    def get_form_instance(self, step):
        return self.object

    def get_queryset(self):
        return DatasetRevision.objects.filter(
            dataset__organisation_id=self.organisation.id
        )

    def get_object(self, queryset=None):
        revision = None
        queryset = Dataset.objects.filter(organisation_id=self.organisation.id)
        # Get the single item from the filtered queryset
        self.dataset = self.get_dataset()

        try:
            revision = self.dataset.revisions.get(is_published=False)
        except queryset.model.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": DatasetRevision._meta.verbose_name}
            )
        if revision is not None:
            return revision

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
                "dataset_upload_modify-current_step", None
            )

        return kwargs

    def post(self, *args, **kwargs):
        # Get feed object to update
        self.object = self.get_object()
        return super().post(*args, **kwargs)
