import re
from datetime import datetime
from typing import Any, List

from django.core.exceptions import ImproperlyConfigured
from django.db.models import F, QuerySet
from django.http import FileResponse
from django.views import View
from django.views.generic import ListView
from django.views.generic.detail import SingleObjectMixin
from django_hosts.resolvers import reverse

from config import hosts
from transit_odp.common.dataclasses import AnchorTag
from transit_odp.common.view_models import RangeFilter
from transit_odp.site_admin.models import ResourceRequestCounter


class RangeFilterContentMixin(object):
    # The lookup to filter with, e.g. 'name__iregex'
    lookup: str = None
    ranges: List[str] = None
    query_param = "range"

    def get_lookup(self):
        """
        Returns the lookup to use to filter the queryset, e.g. name__iregex
        :return:
        """
        if not self.lookup:
            raise ImproperlyConfigured(
                "%(cls)s is missing a lookup. Define "
                "%(cls)s.lookup or override "
                "%(cls)s.get_lookup()." % {"cls": self.__class__.__name__}
            )
        return self.lookup

    def get_filter_context(self, queryset: QuerySet):
        """
        Generates context for the view:
         - gets the query param and validates its
         - uses query param and lookup to filter the queryset
         - creates filter_ranges list
        """
        param = self.get_filter_param()

        # TODO - the apply_range_filter().exist makes N queries
        # (where N is the number of ranges)
        #  This could be improved by doing a single aggregation
        ranges = [
            RangeFilter(
                filter=filter_range,
                display=" ".join(list(filter_range)).upper(),
                disabled=not self.apply_range_filter(queryset, filter_range).exists(),
            )
            for filter_range in self.ranges
        ]

        return {"current_range": param, "range_filters": ranges}

    def apply_range_filter(self, queryset: QuerySet, filter_range: str):
        """
        Filters the queryset using the lookup and the filter_range
        """
        lookup = self.get_lookup()
        return queryset.filter(**{lookup: rf"^[{filter_range}]+"})

    def get_default_range(self) -> str:
        """
        Returns the range to use as a default,
        e.g. when query param is missing or invalid
        """
        return self.ranges[0]

    def get_filter_param(self) -> str:
        """
        Extracts and validates the query param from GET
        :return: validated filter_range
        """
        default_range = self.get_default_range()
        param = self.request.GET.get(self.query_param, default_range)
        ranges_joined = "|".join(self.ranges)
        if not re.match(rf"({ranges_joined})$", param):
            param = default_range
        return param


class RangeFilterListView(RangeFilterContentMixin, ListView):
    """
    A view which combines a RangeFilter with a list of objects displayed
    in columns
    """

    num_cols: int = 3

    def get_context_data(self, object_list=None, *args, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)

        qs = self.object_list

        # Generate range filters
        filter_context = self.get_filter_context(qs)
        context.update(**filter_context)

        # Apply range filter
        range_filter_value = self.get_filter_param()
        qs = self.apply_range_filter(qs, range_filter_value)

        # Calculate number of items per column
        total_items = qs.count()
        items_per_col = self.get_items_per_col(total_items, self.num_cols)

        context.update({"items_per_col": self.get_qs_slices(qs, items_per_col)})

        return context

    @classmethod
    def get_qs_slices(cls, qs: List[Any], items_per_col: List[int]):
        """Slices the qs iterable into a list of N slices,
        where N=len(items_per_col), e.g. number of cols, where
        the size of slice, s(i), is given by items_per_col(i)"""
        slices = []
        end = 0

        # force the queryset to commit before we slice it to avoid multiple queries
        len(qs)
        for n in items_per_col:
            start = end
            end = start + n
            slices.append(qs[start:end])
        return slices

    @classmethod
    def get_items_per_col(cls, total_items: int, num_cols: int) -> List[int]:
        """Calculates the number of items to populate in each column so
        that the items are spread across
        `num_cols` columns with as few rows as possible."""
        items_in_col = []
        items_per_col = total_items // num_cols
        remainder = total_items % num_cols

        for i in range(num_cols):
            n = items_per_col
            if remainder > i:
                n += 1
            items_in_col.append(n)

        return items_in_col


class BaseDownloadFileView(View):
    def get_download_file(self):
        raise NotImplementedError("DownloadView must implement get_download_file")

    def render_to_response(self, **response_kwargs):
        download_file = self.get_download_file()
        return FileResponse(
            download_file.open("rb"), filename=download_file.name, as_attachment=True
        )


class DownloadView(SingleObjectMixin, BaseDownloadFileView):
    """A base view for displaying a single object."""

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render_to_response()


class BODSBaseView:
    """Mixin for adding feature flags to the context"""

    def get_navigation_anchor(self):
        """Get an anchor tag for the navlinks."""
        if self.request.path == "/":
            return None

        if not hasattr(self.request, "user"):
            return None

        user = self.request.user
        if not user.is_authenticated:
            return None

        if user.is_site_admin or user.is_developer:
            return None

        if user.is_agent_user:
            tag = AnchorTag(
                href=reverse("select-org", host=hosts.PUBLISH_HOST),
                content="Operator Dashboard",
            )
        else:
            tag = AnchorTag(
                href=reverse(
                    "select-data",
                    kwargs={"pk1": user.organisation_id},
                    host=hosts.PUBLISH_HOST,
                ),
                content="Choose data type",
            )

        return tag

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        tag = self.get_navigation_anchor()
        if tag is not None:
            context["middle_nav_tag"] = tag

        return context


class ResourceCounterMixin:
    """Mixin to count the number times a user requests a resource in a day"""

    def get(self, request, *args, **kwargs):
        user = request.user if not request.user.is_anonymous else None
        today = datetime.now().date()
        resource_counter, _ = ResourceRequestCounter.objects.get_or_create(
            requestor=user,
            path_info=request.path,
            date=today,
            defaults={"counter": 0},
        )
        resource_counter.counter = F("counter") + 1
        resource_counter.save()
        return super().get(request, *args, **kwargs)
