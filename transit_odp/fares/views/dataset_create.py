from typing import List, Tuple, Type

import config.hosts
from django.db import transaction
from django.db.models import Q
from django.forms import Form
from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _
from django_hosts import reverse

from transit_odp.fares.forms import FaresFeedDescriptionForm, FaresFeedUploadForm
from transit_odp.fares.tasks import task_run_fares_pipeline
from transit_odp.organisation.constants import DatasetType, FeedStatus
from transit_odp.organisation.models import Dataset, DatasetRevision
from transit_odp.publish.forms import FeedPublishCancelForm
from transit_odp.publish.views.base import FeedWizardBaseView


class FaresUploadWizard(FeedWizardBaseView):
    DESCRIPTION_STEP = "description"
    PUBLISH_CANCEL_STEP = "cancel"
    UPLOAD_STEP = "upload"

    step_context = {
        DESCRIPTION_STEP: {"step_title": _("Describe your data feed")},
        PUBLISH_CANCEL_STEP: {"step_title": _("Cancel step for publish")},
        UPLOAD_STEP: {"step_title": _("Provide your data using the link below")},
    }

    form_list: List[Tuple[str, Type[Form]]] = [
        (DESCRIPTION_STEP, FaresFeedDescriptionForm),
        (PUBLISH_CANCEL_STEP, FeedPublishCancelForm),
        (UPLOAD_STEP, FaresFeedUploadForm),
    ]

    def get_template_names(self):
        if self.request.POST.get("cancel", None) == self.PUBLISH_CANCEL_STEP:
            return "fares/feed_publish_cancel.html"
        return "fares/feed_form.html"

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
            {"title_tag_text": f"Publish new data set: {kwargs.get('current_step')}"}
        )

        if self.request.POST.get("cancel", None) == self.PUBLISH_CANCEL_STEP:
            kwargs["previous_step"] = self.request.POST.get(
                "fares_upload_wizard-current_step", None
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
            contact=self.request.user,
            organisation_id=self.organisation.id,
            dataset_type=DatasetType.FARES.value,
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

        if not revision.status == FeedStatus.pending.value:
            revision.to_pending()
            revision.save()

        transaction.on_commit(lambda: task_run_fares_pipeline.delay(revision.id))

        return HttpResponseRedirect(
            reverse(
                "fares:revision-publish",
                kwargs={"pk": dataset.id, "pk1": dataset.organisation_id},
                host=config.hosts.PUBLISH_HOST,
            )
        )
