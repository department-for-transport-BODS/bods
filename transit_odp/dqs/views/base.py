from typing import Any
from django.shortcuts import render
from django.views.generic import TemplateView
from django_tables2 import MultiTableMixin, SingleTableView
from django_hosts import reverse
import config.hosts

from transit_odp.dqs.models import Report, ObservationResults
from transit_odp.dqs.constants import Checks, Level
from transit_odp.dqs.tables.base import (
    DQSWarningListBaseTable,
    DQSWarningDetailsBaseTable,
)
from transit_odp.organisation.models import DatasetRevision
from transit_odp.users.models import User


from transit_odp.organisation.models import ConsumerFeedback


class DQSWarningListBaseView(SingleTableView):
    template_name = "data_quality/warning_list.html"
    table_class = DQSWarningListBaseTable
    model = ObservationResults
    paginate_by = 10
    check: Checks = Checks.DefaultCheck
    dqs_details: str = None
    _is_dqs_new_report = None
    is_details_link = True
    col_name = ""

    @property
    def is_dqs_new_report(self):
        if self._is_dqs_new_report is None:
            report_id = self.kwargs.get("report_id")
            qs = Report.objects.filter(id=report_id)
            self._is_dqs_new_report = True
            if not len(qs):
                self._is_dqs_new_report = False
        return self._is_dqs_new_report

    def dispatch(self, request, *args, **kwargs):
        session_data = request.session
        self.show_suppressed = False
        org_id = self.kwargs.get("pk1")

        if session_data and session_data.get("_auth_user_id") and org_id:
            auth_user_id = session_data.get("_auth_user_id")
            users = User.objects.filter(id=auth_user_id)
            if len(users):
                user = users[0]
                org_id = int(org_id)
                organisation_ids = set(user.organisations.values_list("id", flat=True))
                if org_id in organisation_ids:
                    self.show_suppressed = True

        # Call the parent class's dispatch method
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):

        self.model = ObservationResults
        self.table_class = DQSWarningListBaseTable

        report_id = self.kwargs.get("report_id")
        org_id = self.kwargs.get("pk1")

        qs = Report.objects.filter(id=report_id)
        if not len(qs):
            return qs
        revision_id = qs[0].revision_id
        qs_revision = (
            DatasetRevision.objects.filter(id=revision_id).get_published().first()
        )
        is_published = False
        if qs_revision:
            is_published = qs_revision.is_published

        show_suppressed_button = (
            True if self.data.level in (Level.advisory, Level.feedback) else False
        )

        return self.model.objects.get_observations(
            report_id,
            self.check,
            revision_id,
            is_published,
            self.dqs_details,
            self.is_details_link,
            self.col_name,
            org_id,
            self.show_suppressed,
            show_suppressed_button,
        )

    def get_table_kwargs(self):
        pass

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.data.title,
                "definition": self.data.text,
                "preamble": self.data.preamble,
                "resolve": self.data.resolve,
                "impacts": self.data.impacts,
            }
        )
        return context


class FeedbackListBaseView(DQSWarningListBaseView):
    def get_queryset(self):
        """
        Get the queryset for the summarised page of feedback
        """

        self.model = ConsumerFeedback

        report_id = self.kwargs.get("report_id")
        org_id = self.kwargs.get("pk1")

        qs = Report.objects.filter(id=report_id)
        if not len(qs):
            return qs
        revision_id = qs[0].revision_id
        qs_revision = (
            DatasetRevision.objects.filter(id=revision_id).get_published().first()
        )
        is_published = False
        if qs_revision:
            is_published = qs_revision.is_published

        self.show_suppressed = show_suppressed_button = False

        qs = ConsumerFeedback.objects.get_feedbacks(
            report_id,
            revision_id,
            is_published,
            self.dqs_details,
            self.is_details_link,
            org_id,
            self.show_suppressed,
            show_suppressed_button,
        )

        qs_filtered = []
        line_service_codes = []
        for obj in qs:
            service_code = obj.get("service_code", "")
            line_name = obj.get("line_name", "")
            if service_code and line_name:
                line_service_code = service_code + "-" + line_name
                if line_service_code not in line_service_codes:
                    qs_filtered.append(obj)
                    line_service_codes.append(line_service_code)
            else:
                print(f"ServiceCode: {service_code}, LineName: {line_name}")
                continue

        return qs_filtered


class DQSWarningDetailBaseView(MultiTableMixin, TemplateView):
    template_name = "dqs/observation_detail.html"
    model = None
    related_model = None
    related_object = None
    tables = []
    paginate_by = 10
    model = ObservationResults
    table_class = DQSWarningDetailsBaseTable

    @property
    def data(self):
        raise NotImplementedError("Warning detail views must have data attribute")

    def dispatch(self, request, *args, **kwargs):
        session_data = request.session
        self.show_suppressed = False
        org_id = self.kwargs.get("pk1")

        if session_data and session_data.get("_auth_user_id") and org_id:
            auth_user_id = session_data.get("_auth_user_id")
            users = User.objects.filter(id=auth_user_id)
            if len(users):
                user = users[0]
                org_id = int(org_id)
                organisation_ids = set(user.organisations.values_list("id", flat=True))
                if org_id in organisation_ids:
                    self.show_suppressed = True

        # Call the parent class's dispatch method
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Map variables defined largely as empty strings, with values overridden
        # in views as needed for that map
        revision_id = kwargs.get("pk")

        title = self.data.title
        page = self.request.GET.get("page", 1)
        qs = self.get_queryset()

        context.update(
            {
                "title": title,
                "num_of_journeys": len(qs),
                "table": self._table_name(qs, page),
                # for map -- empty strings passed if specific geometry not needed
                "service_pattern_id": "",
                "stop_ids": "",
                "effected_stop_ids": "",
                "service_link_ids": "",
                "api_root": reverse(
                    "dq-api:api-root",
                    host=config.hosts.PUBLISH_HOST,
                ),
                # for backlink -- inheriting views need data attribute set to
                # relevant constant
                "back_url": reverse(
                    self.data.list_url_name,
                    kwargs={
                        "pk": revision_id,
                        "pk1": kwargs.get("pk1"),
                        "report_id": kwargs.get("report_id"),
                    },
                    host=config.hosts.PUBLISH_HOST,
                ),
                "subtitle_description": "Which journeys have been affected?",
                "total_journey_description": "Total vehicle journeys",
                "list_text": "vehicle journeys for this service",
            }
        )
        return context

    def get_queryset(self):

        report_id = self.kwargs.get("report_id")
        service = self.request.GET.get("service")
        line = self.request.GET.get("line")
        qs = Report.objects.filter(id=report_id)
        if not len(qs):
            return qs
        revision_id = qs[0].revision_id

        qs = ObservationResults.objects.get_observations_details(
            report_id, self.check, revision_id, service, line
        )

        return qs


class FeedbackDetailBaseView(DQSWarningDetailBaseView):
    def get_queryset(self):
        """
        Get the queryset for the details page of feedback
        """

        report_id = self.kwargs.get("report_id")
        service = self.request.GET.get("service")
        line = self.request.GET.get("line")
        qs = Report.objects.filter(id=report_id)
        if not len(qs):
            return qs
        revision_id = qs[0].revision_id
        show_suppressed_button = self.show_suppressed
        qs = ConsumerFeedback.objects.get_feedback_details(
            revision_id,
            service,
            line,
            self.show_suppressed,
            show_suppressed_button,
        )

        return qs
