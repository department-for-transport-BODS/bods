import uuid
from typing import List, Tuple, Type

from django.db import transaction
from django.db.models import Q
from django.forms import Form
from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _
from django_hosts import reverse

import config.hosts
from transit_odp.avl.forms import AvlFeedDescriptionForm, AvlFeedUploadForm
from transit_odp.avl.models import CAVLValidationTaskResult
from transit_odp.avl.tasks import task_validate_avl_feed
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models import Dataset, DatasetRevision
from transit_odp.publish.forms import FeedPublishCancelForm
from transit_odp.publish.views.timetable.create import FeedUploadWizard


class AVLUploadWizard(FeedUploadWizard):
    DESCRIPTION_STEP = "description"
    PUBLISH_CANCEL_STEP = "cancel"
    UPLOAD_STEP = "upload"

    step_context = {
        DESCRIPTION_STEP: {"step_title": _("Describe your data feed")},
        PUBLISH_CANCEL_STEP: {"step_title": _("Cancel step for publish")},
        UPLOAD_STEP: {"step_title": _("Provide your data using the link below")},
    }

    form_list: List[Tuple[str, Type[Form]]] = [
        (DESCRIPTION_STEP, AvlFeedDescriptionForm),
        (PUBLISH_CANCEL_STEP, FeedPublishCancelForm),
        (UPLOAD_STEP, AvlFeedUploadForm),
    ]

    def get_template_names(self):
        if self.request.POST.get("cancel", None) == self.PUBLISH_CANCEL_STEP:
            # TODO The buttons in cancel page do not work as expected, as there are few
            # AVL pages yet to be developed
            return "avl/feed_publish_cancel.html"
        return "publish/feed_form.html"

    def get_context_data(self, form, **kwargs):
        kwargs = super().get_context_data(form, **kwargs)
        kwargs.update(
            {"title_tag_text": f"Publish new data feed: {kwargs.get('current_step')}"}
        )

        if self.request.POST.get("cancel", None) == self.PUBLISH_CANCEL_STEP:
            kwargs["previous_step"] = self.request.POST.get(
                "avl_upload_wizard-current_step", None
            )
        return kwargs

    def get_dataset(self):
        return Dataset.objects.create(
            contact=self.request.user,
            organisation_id=self.organisation.id,
            dataset_type=DatasetType.AVL.value,
        )

    @transaction.atomic
    def done(self, form_list, **kwargs):
        all_data = self.get_all_cleaned_data()
        dataset = self.get_dataset()

        # TODO - refactor this into a service

        revision, _ = DatasetRevision.objects.filter(
            Q(dataset=dataset) & Q(is_published=False)
        ).update_or_create(
            dataset=dataset,
            is_published=False,
            defaults={
                "url_link": all_data["url_link"],
                "description": all_data["description"],
                "short_description": all_data["short_description"],
                "username": all_data["username"],
                "password": all_data["password"],
                "requestor_ref": all_data["requestor_ref"],
                "last_modified_user": self.request.user,
                "comment": "First publication",
                "status": "success",
            },
        )

        task_id = uuid.uuid4()
        CAVLValidationTaskResult.objects.create(
            revision=revision,
            task_id=task_id,
            status=CAVLValidationTaskResult.SUCCESS,
        )

        transaction.on_commit(lambda: task_validate_avl_feed.delay(task_id))
        #
        # print("transaction has happened")

        return HttpResponseRedirect(
            reverse(
                "avl:revision-publish",
                kwargs={"pk": dataset.id, "pk1": dataset.organisation_id},
                host=config.hosts.PUBLISH_HOST,
            )
        )
