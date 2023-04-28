from math import ceil

from django.db.models import Count, F
from django_hosts.resolvers import reverse
from waffle import flag_is_active

from config.hosts import DATA_HOST, PUBLISH_HOST
from transit_odp.avl.proxies import AVLDataset
from transit_odp.browse.views.base_views import BaseListView
from transit_odp.common.views import BaseDetailView
from transit_odp.fares_validator.models import FaresValidationResult
from transit_odp.organisation.constants import EXPIRED, INACTIVE, AVLType, FaresType
from transit_odp.organisation.models import Dataset, DatasetRevision, Organisation
from transit_odp.otc.models import Service as OTCService
from transit_odp.publish.requires_attention import get_requires_attention_data


class OperatorsView(BaseListView):
    template_name = "browse/operators.html"
    model = Organisation
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        context["ordering"] = self.request.GET.get("ordering", "name")
        active_orgs = self.model.objects.filter(is_active=True)
        operators = {
            "names": [name for name in active_orgs.values_list("name", flat=True)]
        }
        context["operators"] = operators
        return context

    def get_queryset(self):
        qs = self.model.objects.filter(is_active=True)

        search_term = self.request.GET.get("q", "").strip()
        if search_term:
            qs = qs.filter(name__icontains=search_term)

        qs = qs.order_by(*self.get_ordering())
        return qs

    def get_ordering(self):
        ordering = self.request.GET.get("ordering", "name")
        if isinstance(ordering, str):
            ordering = (ordering,)
        return ordering


class OperatorDetailView(BaseDetailView):
    template_name = "browse/operators/operator_detail.html"
    model = Organisation

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True).add_nocs_string()

    def get_context_data(self, **kwargs):
        is_fares_validator_active = flag_is_active("", "is_fares_validator_active")
        context = super().get_context_data(**kwargs)
        organisation = self.object

        context["total_services_requiring_attention"] = len(
            get_requires_attention_data(organisation.id)
        )
        context[
            "total_in_scope_in_season_services"
        ] = OTCService.objects.get_in_scope_in_season_services(organisation.id).count()
        try:
            context["services_require_attention_percentage"] = ceil(
                100
                * (
                    context["total_services_requiring_attention"]
                    / context["total_in_scope_in_season_services"]
                )
            )
        except ZeroDivisionError:
            context["services_require_attention_percentage"] = 0

        avl_dataset_revisions = (
            DatasetRevision.objects.filter(dataset__organisation_id=organisation.id)
            .filter(dataset__dataset_type=AVLType)
            .aggregate(dataset_count=Count("dataset_id", distinct=True))
        )
        avl_datasets = (
            AVLDataset.objects.filter(organisation=organisation)
            .annotate(status=F("live_revision__status"))
            .exclude(status__in=[EXPIRED, INACTIVE])
            .add_draft_revisions()
        )
        avl_non_compliant_count = avl_datasets.get_needs_attention_count()
        context["avl_total_datasets"] = avl_dataset_revisions["dataset_count"]
        context["avl_non_compliant"] = avl_non_compliant_count

        fares_datasets = (
            Dataset.objects.filter(
                organisation=organisation,
                dataset_type=FaresType,
            )
            .select_related("organisation")
            .select_related("live_revision")
        )
        context["fares_stats"] = fares_datasets.agg_global_feed_stats(
            dataset_type=FaresType, organisation_id=organisation.id
        )
        if is_fares_validator_active:
            try:
                results = (
                    FaresValidationResult.objects.filter(
                        organisation_id=organisation.id,
                        revision_id=F("revision__dataset__live_revision_id"),
                        revision__dataset__dataset_type=FaresType,
                    )
                    .annotate(status=F("revision__status"))
                    .exclude(status__in=[EXPIRED, INACTIVE])
                    .values("count")
                )
            except FaresValidationResult.DoesNotExist:
                results = []
            fares_non_compliant_count = len(
                [count for count in results if count.get("count") > 0]
            )
            context["fares_non_compliant"] = fares_non_compliant_count
        else:
            # Compliance is n/a for Fares datasets
            context["fares_non_compliant"] = 0

        if self.request.user.is_authenticated:
            context["timetable_feed_url"] = (
                f"{reverse('api:feed-list', host=DATA_HOST)}"
                f"?noc={organisation.nocs_string}"
                f"&api_key={self.request.user.auth_token.key}"
            )
            context["avl_feed_url"] = (
                f"{reverse('api:avldatafeedapi', host=DATA_HOST)}"
                f"?operatorRef={organisation.nocs_string}"
                f"&api_key={self.request.user.auth_token.key}"
            )
            context["fares_feed_url"] = (
                f"{reverse('api:fares-api-list', host=DATA_HOST)}"
                f"?noc={organisation.nocs_string}"
                f"&api_key={self.request.user.auth_token.key}"
            )

        context["data_activity_url"] = (
            reverse("data-activity", kwargs={"pk1": organisation.id}, host=PUBLISH_HOST)
            + "?prev=operator-detail"
        )
        return context
