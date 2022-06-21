from django.db import models
from django.db.models import Count, Q, Sum, Value
from django.db.models.functions import Coalesce, TruncDay

from config.hosts import DATA_HOST
from transit_odp.common.utils import reverse_path


class ResourceRequestCounterQuerySet(models.QuerySet):
    def add_bulk_download_counts(self):
        return self.annotate(
            total_download_timetables=Coalesce(
                Sum(
                    "counter",
                    filter=Q(path_info=reverse_path("downloads-bulk", host=DATA_HOST)),
                ),
                Value(0),
            ),
            total_download_fares=Coalesce(
                Sum(
                    "counter",
                    filter=Q(
                        path_info=reverse_path("downloads-fares-bulk", host=DATA_HOST)
                    ),
                ),
                Value(0),
            ),
            total_download_avl=Coalesce(
                Sum(
                    "counter",
                    filter=Q(
                        path_info=reverse_path("downloads-avl-bulk", host=DATA_HOST)
                    ),
                ),
                Value(0),
            ),
        )

    def get_requests_per_day_per_user(self):
        return (
            self.select_related("requestor")
            .values("date", "requestor_id", "requestor__email")
            .order_by("date", "requestor_id")
            .add_bulk_download_counts()
            .filter(requestor_id__isnull=False)
        )


class APIRequestQuerySet(models.QuerySet):
    def add_day_from_created(self):
        return self.annotate(day=TruncDay("created"))

    def add_total_request_count(self):
        return self.annotate(total_requests=Count("id"))

    def get_requests_per_day_per_user(self):
        return (
            self.select_related("requestor")
            .add_day_from_created()
            .values("day", "requestor_id", "requestor__email")
            .add_total_request_count()
            .order_by("day", "requestor_id")
        )
