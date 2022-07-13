from datetime import timedelta

from django.db import models
from django.db.models import Count, DateField, IntegerField, Q, Sum, Value
from django.db.models.functions import Coalesce, TruncDay
from django.utils.timezone import now

from config.hosts import DATA_HOST
from transit_odp.common.utils import reverse_path


class ResourceRequestCounterQuerySet(models.QuerySet):
    def add_bulk_download_counts(self):
        # Probably should use unique counts here
        return self.annotate(
            total_download_timetables=Coalesce(
                Sum(
                    "counter",
                    filter=Q(path_info=reverse_path("downloads-bulk", host=DATA_HOST)),
                ),
                Value(0, output_field=IntegerField()),
            ),
            total_download_fares=Coalesce(
                Sum(
                    "counter",
                    filter=Q(
                        path_info=reverse_path("downloads-fares-bulk", host=DATA_HOST)
                    ),
                ),
                Value(0, output_field=IntegerField()),
            ),
            total_download_avl=Coalesce(
                Sum(
                    "counter",
                    filter=Q(
                        path_info=reverse_path("downloads-avl-bulk", host=DATA_HOST)
                    ),
                ),
                Value(0, output_field=IntegerField()),
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

    def get_requests_per_day(self):
        return self.values("date", "path_info").annotate(total_requests=Sum("counter"))

    def get_requests_from_last_7_days(self):
        seven_days_ago = now() - timedelta(days=7)
        return self.filter(date__gte=seven_days_ago)

    def get_requests_from_last_30_days(self):
        thirty_days_ago = now() - timedelta(days=30)
        return self.filter(date__gte=thirty_days_ago.date())


class APIRequestQuerySet(models.QuerySet):
    def add_day_from_created(self, as_date=False):
        if as_date:
            annotation = TruncDay("created", output_field=DateField())
        else:
            annotation = TruncDay("created")

        return self.annotate(day=annotation)

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

    def get_requests_from_last_7_days(self):
        seven_days_ago = now() - timedelta(days=7)
        return self.filter(created__gte=seven_days_ago)

    def get_requests_from_last_30_days(self):
        thirty_days_ago = now() - timedelta(days=30)
        return self.filter(created__gte=thirty_days_ago)

    def exclude_query_string(self):
        return self.filter(query_string="")

    def get_user_path_info_requests_from_last_7_days(self):
        return (
            self.get_requests_from_last_7_days()
            .exclude_query_string()
            .values("path_info", "requestor_id")
            .add_total_request_count()
        )
