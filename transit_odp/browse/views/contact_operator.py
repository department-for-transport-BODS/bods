import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView
from django_hosts import reverse

import config.hosts
from transit_odp.browse.forms import ConsumerFeedbackForm
from transit_odp.notifications import get_notifications
from transit_odp.organisation.models import ConsumerFeedback, Organisation
from transit_odp.users.constants import OrgAdminType, SiteAdminType

logger = logging.getLogger(__name__)
User = get_user_model()


class ContactOperatorView(LoginRequiredMixin, CreateView):
    template_name = "browse/operators/contact_operator.html"
    form_class = ConsumerFeedbackForm
    model = ConsumerFeedback
    organisation = None

    def get(self, request, *args, **kwargs):
        self.organisation = get_object_or_404(Organisation, id=self.kwargs.get("pk"))
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.organisation = get_object_or_404(Organisation, id=self.kwargs.get("pk"))
        return super().post(request, *args, **kwargs)

    def get_initial(self):
        return {
            "dataset_id": None,
            "organisation_id": self.organisation.id,
            "consumer_id": self.request.user.id,
        }

    @transaction.atomic
    def form_valid(self, form):
        client = get_notifications()
        response = super().form_valid(form)
        org_users = self.organisation.users.filter(
            account_type=OrgAdminType, is_active=True
        )
        org_users_emails = [org_user["email"] for org_user in org_users.values()]
        developer_email = None if not self.object.consumer else self.request.user.email
        admins = User.objects.filter(account_type=SiteAdminType)
        emails = [email["email"] for email in admins.values()]
        emails.append(self.request.user.email)

        for email in emails:
            client.send_operator_feedback_consumer_copy(
                contact_email=email,
                publisher_name=self.organisation.name,
                feedback=self.object.feedback,
                time_now=None,
            )

        for email in org_users_emails:
            client.send_operator_feedback_notification(
                contact_email=email,
                publisher_name=self.organisation.name,
                feedback=self.object.feedback,
                time_now=None,
                developer_email=developer_email,
            )
        return response

    def get_success_url(self):
        return reverse(
            "feedback-operator-success",
            kwargs={"pk": self.organisation.id},
            host=config.hosts.DATA_HOST,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["organisation_name"] = self.organisation.name
        context["back_url"] = reverse(
            "operator-detail",
            kwargs={"pk": self.organisation.id},
            host=config.hosts.DATA_HOST,
        )
        return context


class ContactOperatorFeedbackSuccessView(LoginRequiredMixin, TemplateView):
    template_name = "browse/operators/contact_operator_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        url = reverse("operators", host=config.hosts.DATA_HOST)
        context["back_url"] = url
        return context
