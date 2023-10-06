from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from django_hosts import reverse
import config.hosts
from collections import ChainMap

from transit_odp.browse.views.base_views import BaseTemplateView
from transit_odp.common.view_mixins import DownloadView, ResourceCounterMixin
from transit_odp.disruptions.models import DisruptionsDataArchive

import logging
import requests
from requests import RequestException
from rest_framework import status
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from transit_odp.browse.views.base_views import (
    BaseTemplateView,
)
from django.core.paginator import Paginator
from django.views.generic.list import ListView
from django.core.paginator import Paginator
from datetime import datetime

logger = logging.getLogger(__name__)


class DownloadDisruptionsView(LoginRequiredMixin, BaseTemplateView):
    template_name = "browse/disruptions/download_disruptions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["show_bulk_archive_url"] = DisruptionsDataArchive.objects.exists()
        return context


class DownloadDisruptionsDataArchiveView(ResourceCounterMixin, DownloadView):
    def get_object(self, queryset=None):
        archive = DisruptionsDataArchive.objects.last()

        if archive is None:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": DisruptionsDataArchive._meta.verbose_name}
            )
        return archive

    def get_download_file(self):
        return self.object.data


def _get_disruptions_organisation_data(url: str, headers: object):
    response_status = status.HTTP_400_BAD_REQUEST
    response = {}
    content = None
    try:
        response = requests.get(url, headers=headers, timeout=180)
        elapsed_time = response.elapsed.total_seconds()
        logger.info(
            f"Request to get organisation data took {elapsed_time}s "
            f"- status {response.status_code}"
        )

        if response.status_code == 200:
            content = response.json()
            response_status = status.HTTP_200_OK
    except RequestException:
        return {}, response_status

    return content, response_status


class DisruptionsDataView(ListView):
    template_name = "browse/disruptions/disruptions_data.html"
    paginate_by = 10
    # context_object_name = 'api_data'
    content = None

    def get_queryset(self):
        url = settings.DISRUPTIONS_ORG_API_URL
        headers = {"x-api-key": settings.DISRUPTIONS_API_KEY}
        if self.content is None:
            self.content, _ = _get_disruptions_organisation_data(url, headers)

        keywords = self.request.GET.get("q", "").strip()
        # ordering = self.request.GET.get('ordering', '-lastUpdated')
        ordering = self.request.GET.get("ordering", "operatorPublicName")
        # Validate the ordering value to prevent SQL injection
        if ordering not in ["name", "-name", "-lastUpdated"]:
            # ordering = '-lastUpdated'
            ordering = "name"

        reverse_order = ordering.startswith("-")

        filtered_list = [
            item
            for item in self.content
            if any(
                isinstance(value, str) and keywords in value for value in item.values()
            )
        ]

        # Sort the data based on the selected field
        if ordering == "last_updated":
            # Sort by last_updated date
            filtered_list = sorted(
                filtered_list,
                key=lambda item: datetime.strptime(
                    item[ordering.lstrip("-")], "%d/%m/%Y"
                ),
                reverse=reverse_order,
            )
        else:
            # Sort by other fields (e.g., publicName)
            filtered_list = sorted(
                filtered_list,
                key=lambda item: item[ordering.lstrip("-")].lower(),
                reverse=reverse_order,
            )

        return filtered_list

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs_data = self.get_queryset()
        paginator = Paginator(qs_data, self.paginate_by)
        page = self.request.GET.get("page")
        context["api_data"] = paginator.get_page(page)
        keywords = self.request.GET.get("q", "").strip()
        context["q"] = keywords
        return context


class DisruptionOrganisationDetailView(BaseTemplateView):
    template_name = "browse/disruptions/organisation/organisation_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        url = settings.DISRUPTIONS_ORG_API_URL + "/" + str(kwargs["pk"])
        headers = {"x-api-key": settings.DISRUPTIONS_API_KEY}
        content = None
        content, _ = _get_disruptions_organisation_data(url, headers)
        if content is None:
            context["error"] = "true"
        else:
            context["object"] = content
        context["api_root"] = reverse("api:app:api-root", host=config.hosts.DATA_HOST)
        context["org_id"] = str(kwargs["pk"])
        return context
