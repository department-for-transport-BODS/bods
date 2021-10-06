from django import template
from django.conf import settings
from django_tables2.paginators import LazyPaginator

register = template.Library()


@register.filter(name="paginator_range")
def paginator_range(page, paginator):
    """
    Returns a list of pagination labels.
    The list includes the current page, plus up to page_range pages
    either side of the current page.
    Any gaps are represented by ellipses.

    Example:
        {% for p in table.page|my_paginator_range:table.paginator %}
            {{ p }}
        {% endfor %}
    """
    num_pages = paginator.num_pages

    if page.number < 11:
        page_range = getattr(settings, "DJANGO_TABLES2_PAGE_RANGE", 10)
    else:
        page_range = getattr(settings, "DJANGO_TABLES2_PAGE_RANGE", 8)

    if num_pages <= page_range:
        return range(1, num_pages + 1)

    range_start = page.number - int(page_range / 2)
    if range_start < 1:
        range_start = 1
    range_end = range_start + page_range
    if range_end > num_pages:
        range_start = num_pages - page_range + 1
        range_end = num_pages + 1

    ret = range(range_start, range_end)
    if 1 not in ret:
        ret = [1, "..."] + list(ret)[2:]
    if num_pages not in ret:
        ret = list(ret)[:-2] + ["...", num_pages]
    if isinstance(paginator, LazyPaginator) and not paginator.is_last_page(page.number):
        list(ret).append("...")
    return ret
