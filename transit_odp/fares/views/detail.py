from typing import List, TypedDict

from django_hosts import reverse

import config.hosts
from transit_odp.common.enums import FeedErrorSeverity
from transit_odp.common.views import BaseDetailView
from transit_odp.fares_validator.models import FaresValidationResult
from transit_odp.organisation.constants import (
    EXPIRED,
    INACTIVE,
    LIVE,
    DatasetType,
    FeedStatus,
)
from transit_odp.organisation.models import Dataset, DatasetMetadata
from transit_odp.users.views.mixins import OrgUserViewMixin

URL_NAMESPACE = "fares"


class FaresFeedDetailView(OrgUserViewMixin, BaseDetailView):
    template_name = "fares/feed_detail/index.html"
    model = Dataset

    class Properties(TypedDict):
        dataset_id: int
        name: str
        description: str
        short_description: str
        status: str
        organisation_name: str
        organisation_id: int
        url_link: str
        last_modified: str
        last_modified_user: str
        published_by: str
        published_at: str
        api_root: str
        download_url: str
        show_map: bool
        severe_errors: List[FeedErrorSeverity]

    def get_feed_download_url(self):
        if download_url := self.object.live_revision.url_link:
            return download_url
        else:
            return reverse(
                f"{URL_NAMESPACE}:feed-download",
                kwargs={"pk1": self.kwargs["pk1"], "pk": self.object.pk},
                host=config.hosts.PUBLISH_HOST,
            )
        return download_url

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                organisation_id=self.organisation.id,
                dataset_type=DatasetType.FARES.value,
            )
            .get_published()
            .select_related("live_revision")
        )

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)

        dataset = self.object
        revision = dataset.live_revision

        last_modified_username = None
        if revision.last_modified_user is not None:
            last_modified_username = revision.last_modified_user.username

        published_by = None
        if revision.published_by is not None:
            published_by = revision.published_by.username

        api_root = reverse("api:app:api-root", host=config.hosts.DATA_HOST)

        kwargs["pk1"] = self.kwargs["pk1"]
        kwargs["pk2"] = revision.id

        severe_errors = revision.errors.filter(severity=FeedErrorSeverity.severe.value)
        status = revision.status
        # There shouldn't be severe errors without status == error, but just in case
        # there display error banner
        if severe_errors or (revision.status == FeedStatus.error.value):
            status = "error"

        kwargs["is_compliant_error"] = True
        kwargs["show_report_link"] = False
        try:
            results = FaresValidationResult.objects.get(
                revision_id=dataset.live_revision_id
            )
        except FaresValidationResult.DoesNotExist:
            results = None
        if results:
            if results.is_compliant is True:
                kwargs["is_compliant_error"] = False
            kwargs["show_report_link"] = True

        try:
            faresmetadata = revision.metadata.faresmetadata
        except DatasetMetadata.DoesNotExist:
            # TODO remove once old fares datasets have been migrated
            pass
        else:
            kwargs["metadata"] = faresmetadata

        show_map = status in (EXPIRED, INACTIVE, LIVE)
        kwargs["properties"] = self.Properties(
            dataset_id=dataset.id,
            name=revision.name,
            description=revision.description,
            short_description=revision.short_description,
            status=status,
            organisation_name=dataset.organisation.name,
            organisation_id=dataset.organisation_id,
            url_link=revision.url_link,
            last_modified=revision.modified,
            last_modified_user=last_modified_username,
            published_by=published_by,
            published_at=revision.published_at,
            api_root=api_root,
            download_url=self.get_feed_download_url(),
            severe_errors=severe_errors,
            show_map=show_map,
        )

        return kwargs
