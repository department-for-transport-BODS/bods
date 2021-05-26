from typing import Optional

from django.http import Http404
from django.utils.translation import gettext as _
from django.views.generic import TemplateView
from django_tables2 import SingleTableMixin

from transit_odp.bods.adapters.repositories import AVLRepository
from transit_odp.bods.domain.entities import AVLPublication
from transit_odp.bods.domain.entities.identity import PublicationId
from transit_odp.publish.tables import DatasetRevisionTable
from transit_odp.users.views.mixins import OrgUserViewMixin


class ChangeLogView(OrgUserViewMixin, SingleTableMixin, TemplateView):
    template_name = "avl/dataset_changelog.html"
    table_class = DatasetRevisionTable
    publication: Optional[AVLPublication] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repo = AVLRepository()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pk1"] = self.kwargs["pk1"]
        return context

    def get_object(self):
        if self.publication is None:
            self.publication = self.repo.find(
                publication_id=PublicationId(id=self.kwargs["pk"])
            )
            if self.publication is None:
                raise Http404(
                    _("No %(verbose_name)s found matching the query")
                    % {"verbose_name": "Publication"}
                )
        return self.publication

    @property
    def extra_context(self):
        publication = self.get_object()
        return {
            "publication_id": publication.get_id(),
            "publication_name": publication.live.dataset.name,
        }

    def get_table_data(self):
        revisions = self.repo.get_revision_history(publication_id=self.publication.id)
        return [
            {
                "comment": revision.dataset.comment,
                "published_at": revision.published_at,
                "status": "error" if revision.has_error else "live",
                "dataset_type": self.publication.type,
            }
            for revision in revisions
        ]
