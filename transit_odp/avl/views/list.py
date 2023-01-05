from django.conf import settings
from django.db.models import Avg, Case, ExpressionWrapper, F, OuterRef, Subquery, When
from django.db.models.fields import FloatField

from transit_odp.avl.constants import MORE_DATA_NEEDED
from transit_odp.avl.models import PostPublishingCheckReport
from transit_odp.avl.proxies import AVLDataset
from transit_odp.avl.tables import AVLDataFeedTable
from transit_odp.organisation.constants import AVLType
from transit_odp.publish.views.base import BasePublishListView


class ListView(BasePublishListView):
    template_name = "avl/feed_list.html"

    dataset_type = AVLType
    model = AVLDataset
    table = AVLDataFeedTable

    page_title_datatype = "bus location"
    publish_url_name = "avl:new-feed"
    nav_url_name = "avl:feed-list"

    def get_datasets(self):
        return (
            super()
            .get_datasets()
            .add_avl_compliance_status_cached()
            .order_by("avl_feed_status", "-modified")
        )

    def get_overall_ppc_score(self):
        created_at = (
            PostPublishingCheckReport.objects.filter(granularity="weekly")
            .filter(dataset=OuterRef("pk"))
            .order_by("-created")
        )
        avl_datasets = (
            self.get_datasets()
            .get_active()
            .exclude(avl_compliance_status_cached__in=[MORE_DATA_NEEDED])
        ).annotate(
            vehicle_completely_matching=Subquery(
                created_at.values("vehicle_activities_completely_matching")[:1]
            ),
            vehicle_analysed=Subquery(
                created_at.values("vehicle_activities_analysed")[:1]
            ),
        )
        return avl_datasets.annotate(
            score=Case(
                When(
                    vehicle_analysed__gt=0,
                    then=ExpressionWrapper(
                        F("vehicle_completely_matching")
                        * 100.0
                        / F("vehicle_analysed"),
                        output_field=FloatField(),
                    ),
                ),
                default=None,
            )
        ).aggregate(Avg("score"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "feature_ppc_enabled": settings.FEATURE_PPC_ENABLED,
                "overall_ppc_score": self.get_overall_ppc_score()["score__avg"],
            }
        )
        return context
