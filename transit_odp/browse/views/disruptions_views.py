from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin
from django_hosts import reverse
from django.core.paginator import Paginator
from django.views.generic.list import ListView
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from waffle import flag_is_active

from transit_odp.common.view_mixins import DownloadView, ResourceCounterMixin
from transit_odp.disruptions.models import DisruptionsDataArchive
from transit_odp.organisation.constants import DatasetType
from transit_odp.browse.views.base_views import (
    BaseTemplateView,
)

import config.hosts
import logging
import requests
from requests import RequestException
from rest_framework import status
from datetime import datetime


logger = logging.getLogger(__name__)


class DownloadDisruptionsView(LoginRequiredMixin, BaseTemplateView):
    template_name = "browse/disruptions/download_disruptions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["show_bulk_archive_url"] = DisruptionsDataArchive.objects.exists()
        context["is_gtfs_service_alerts_live"] = flag_is_active(
            "", "is_gtfs_service_alerts_live"
        )
        return context


class DownloadDisruptionsDataArchiveView(DownloadView):
    data_format = None

    def get_object(self, queryset=None):
        archive = DisruptionsDataArchive.objects.filter(
            data_format=self.data_format,
        ).last()

        if archive is None:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": DisruptionsDataArchive._meta.verbose_name}
            )
        return archive

    def get_download_file(self):
        return self.object.data


class DownloadDisruptionsSIRIVMDataArchiveView(
    ResourceCounterMixin, DownloadDisruptionsDataArchiveView
):
    data_format = DisruptionsDataArchive.SIRISX


class DownloadDisruptionsGTFSRTDataArchiveView(
    ResourceCounterMixin, DownloadDisruptionsDataArchiveView
):
    data_format = DisruptionsDataArchive.GTFSRT


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
    content = None

    def get_queryset(self):
        url = f"{settings.DISRUPTIONS_API_BASE_URL}/organisations"
        headers = {"x-api-key": settings.DISRUPTIONS_API_KEY}
        if self.content is None:
            self.content, _ = _get_disruptions_organisation_data(url, headers)

        if self.content is None:
            return []

        search = self.request.GET.get("q", "").strip()
        ordering = self.request.GET.get("ordering", "-modified")

        if ordering not in ["-modified", "name", "-name"]:
            ordering = "-modified"

        reverse_order = ordering.startswith("-")

        orgs_to_show = list(
            filter(
                lambda d: (
                    d["stats"]["lastUpdated"] or d["stats"]["totalDisruptionsCount"]
                )
                and (not search or search.lower() in d["name"].lower()),
                self.content,
            )
        )

        if ordering == "-modified":
            sorted_orgs = sorted(
                orgs_to_show,
                key=lambda item: datetime.strptime(
                    item["stats"]["lastUpdated"], "%Y-%m-%dT%H:%M:%S.%fZ"
                )
                if item["stats"]["lastUpdated"]
                else datetime.min,
                reverse=reverse_order,
            )
        else:
            sorted_orgs = sorted(
                orgs_to_show,
                key=lambda item: item[ordering.lstrip("-")].lower(),
                reverse=reverse_order,
            )

        mapped_orgs = [
            dict(
                item,
                **{
                    "dataset_type": DatasetType.DISRUPTIONS.value,
                    "stats": dict(
                        item["stats"],
                        **{
                            "lastUpdated": datetime.strptime(
                                item["stats"]["lastUpdated"], "%Y-%m-%dT%H:%M:%S.%fZ"
                            )
                            if item["stats"]["lastUpdated"]
                            else ""
                        },
                    ),
                },
            )
            for item in sorted_orgs
        ]

        return mapped_orgs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs_data = self.get_queryset()
        paginator = Paginator(qs_data, self.paginate_by)
        page = self.request.GET.get("page")
        context["api_data"] = paginator.get_page(page)
        keywords = self.request.GET.get("q", "").strip()
        context["q"] = keywords
        context["ordering"] = self.request.GET.get("ordering", "-modified")
        context["org_names"] = {"names": [org["name"] for org in qs_data]}

        return context


class DisruptionOrganisationDetailView(BaseTemplateView):
    template_name = "browse/disruptions/organisation/organisation_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        url = (
            f"{settings.DISRUPTIONS_API_BASE_URL}/organisations/{str(kwargs['orgId'])}"
        )

        headers = {"x-api-key": settings.DISRUPTIONS_API_KEY}
        content = None
        content, _ = _get_disruptions_organisation_data(url, headers)
        if content is None:
            context["error"] = "true"
        else:
            content["stats"]["lastUpdated"] = (
                datetime.strptime(
                    content["stats"]["lastUpdated"], "%Y-%m-%dT%H:%M:%S.%fZ"
                )
                if content["stats"]["lastUpdated"]
                else ""
            )
            context["object"] = content
        context["api_root"] = reverse("api:app:api-root", host=config.hosts.DATA_HOST)
        context["org_id"] = str(kwargs["orgId"])
        return context


class DisruptionDetailView(BaseTemplateView):
    template_name = "browse/disruptions/organisation/disruption_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        url = f"{settings.DISRUPTIONS_API_BASE_URL}/organisations/{str(kwargs['orgId'])}/disruptions/{str(kwargs['disruptionId'])}"

        headers = {"x-api-key": settings.DISRUPTIONS_API_KEY}
        content = None
        content, _ = _get_disruptions_organisation_data(url, headers)
        if content is None:
            context["error"] = "true"
        else:
            type_of_consequence_dict = {
                "networkWide": "Network wide",
                "stops": "Stops",
                "services": "Services",
                "operatorWide": "Operator wide",
            }
            vehicle_mode_dict = {
                "bus": "Bus",
                "tram": "Tram",
                "ferryService": "Ferry service",
                "rail": "Train",
            }
            consequences = content["consequences"]
            formatted_consequences = [
                {
                    **consequence,
                    "consequenceType": type_of_consequence_dict[
                        consequence["consequenceType"]
                    ],
                    "vehicleMode": vehicle_mode_dict[consequence["vehicleMode"]]
                    if consequence["vehicleMode"] in vehicle_mode_dict
                    else consequence["vehicleMode"],
                }
                for consequence in consequences
            ]

            content["consequences"] = formatted_consequences
            context["object"] = content
        context["api_root"] = reverse("api:app:api-root", host=config.hosts.DATA_HOST)
        context["org_id"] = str(kwargs["orgId"])
        context["disruption_id"] = str(kwargs["disruptionId"])
        return context
