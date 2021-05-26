from django.http import Http404
from django.utils.translation import gettext as _

from transit_odp.organisation.models import Dataset


class WithPublishedRevision:
    """Mixing to provide:
    get_revision_id"""

    def get_revision_id(self) -> int:
        """Returns Revision ID going through dateset.live_revision"""
        dataset_id: int = self.kwargs.get("pk")
        dataset: Dataset = Dataset.objects.get(id=dataset_id)
        return dataset.live_revision_id


class WithDraftRevision:
    """Mixing to provide:
    get_revision_id"""

    def get_revision_id(self) -> int:
        """Returns Revision ID going through dateset.revisions.latest"""
        try:
            dataset_id: int = self.kwargs.get("pk")
            org_id: int = self.kwargs.get("pk1")
            dataset: Dataset = Dataset.objects.filter(organisation_id=org_id).get(
                id=dataset_id
            )
            return dataset.revisions.latest().id
        except Dataset.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": Dataset._meta.verbose_name}
            )
