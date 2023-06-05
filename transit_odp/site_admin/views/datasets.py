from django.contrib.auth import get_user_model
from django.db.models import (
    Case,
    CharField,
    DateTimeField,
    F,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    When,
)
from django.http import Http404
from django.utils.translation import gettext as _
from django_filters.views import FilterView

from transit_odp.organisation.constants import AVLType, FaresType, TimetableType
from transit_odp.organisation.models import Dataset, DatasetRevision, Organisation
from transit_odp.site_admin.filters import AVLSearchFilter, TimetableSearchFilter
from transit_odp.users.views.mixins import SiteAdminViewMixin

User = get_user_model()

__all__ = [
    "BaseOrganisationListView",
    "OrganisationAVLListView",
    "OrganisationFaresListView",
    "OrganisationTimetableListView",
]


class BaseOrganisationListView(SiteAdminViewMixin, FilterView):
    model = Dataset
    paginate_by = 10
    filterset_class = TimetableSearchFilter
    strict = False
    _organisation = None
    headers = ()
    dataset_type = None

    @property
    def organisation(self) -> Organisation:
        if self._organisation is None:
            try:
                pk = self.kwargs["pk"]
                self._organisation = Organisation.objects.get(id=pk)
            except (Organisation.DoesNotExist, KeyError):
                raise Http404(
                    _("No %(verbose_name)s found matching the query")
                    % {"verbose_name": Organisation._meta.verbose_name}
                )
        return self._organisation

    def get_queryset(self):
        org_id = self.kwargs["pk"]
        queryset = self.model.objects.distinct()
        queryset = queryset.filter(
            Q(live_revision__isnull=False) | Q(revisions__status="success"),
            organisation_id=org_id,
            dataset_type=self.dataset_type,
        )

        status = self.request.GET.getlist("status", [])
        status_list = []
        if len(status) == 0:
            status_list = ["live"]
            queryset = queryset.filter(live_revision__status__in=status_list)

        latest_revision_subquery = DatasetRevision.objects.filter(
            dataset_id=OuterRef("id"), status="success"
        ).order_by("-modified")

        annotation_kwargs = {}
        for header in self.headers:
            accessor, output_field = header[-2:]
            annotation_kwargs[accessor if len(header) == 2 else header[0]] = Case(
                When(
                    live_revision__isnull=True,
                    then=Subquery(
                        latest_revision_subquery.values(accessor)[:1],
                        output_field=output_field(),
                    ),
                ),
                default=F(f"live_revision__{accessor}"),
                output_field=output_field(),
            )

        return queryset.annotate(**annotation_kwargs).order_by(self.get_ordering())

    def get_ordering(self):
        return self.request.GET.get("ordering", "-modified")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = self.filterset.form
        pill_box_items = {}
        pill_box_title = "Containing"
        choice_dict = dict(form.fields["status"].choices)
        if form.is_valid() and form.cleaned_data.get("status"):
            status = form.cleaned_data.get("status")
            pill_box_title = "Status"
            pill_box_items["status"] = choice_dict[status]

        context.update(
            {
                "organisation": self.organisation,
                "query_params": pill_box_items,
                "pill_box_title": pill_box_title,
                "ordering": self.get_ordering(),
            }
        )
        return context


class OrganisationAVLListView(BaseOrganisationListView):
    filterset_class = AVLSearchFilter
    template_name = "site_admin/organisation_dataset_list/avls.html"
    dataset_type = AVLType
    headers = (
        ("name", CharField),
        ("status", CharField),
        ("description", CharField),
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"title": _(f"{ self.organisation.name } location data feeds")})

        if not self.request.GET:
            context["query_params"] = {"status": "Published"}

        return context


class OrganisationFaresListView(BaseOrganisationListView):
    template_name = "site_admin/organisation_dataset_list/fares.html"
    dataset_type = FaresType
    headers = (
        ("name", CharField),
        ("status", CharField),
        ("description", CharField),
        ("last_updated", "modified", DateTimeField),
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"title": _(f"{ self.organisation.name } fares data sets")})

        if not self.request.GET:
            context["query_params"] = {"status": "Published"}

        return context


class OrganisationTimetableListView(BaseOrganisationListView):
    template_name = "site_admin/organisation_dataset_list/timetables.html"
    dataset_type = TimetableType
    # headers tuple helps build the queryset
    # (name of annotation, name of field on revision, field type)
    # if the name of annotation isnt defined then the name of field is used
    headers = (
        ("name", CharField),
        ("status", CharField),
        ("num_of_routes", "num_of_lines", IntegerField),
        ("num_of_bus_stops", IntegerField),
        ("last_updated", "modified", DateTimeField),
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"title": _(f"{ self.organisation.name } timetables data sets")})

        if not self.request.GET:
            context["query_params"] = {"status": "Published"}

        return context
