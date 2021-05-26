from typing import List

import attr
from django import template
from django.conf import settings

register = template.Library()


@attr.s(auto_attribs=True)
class PaginatorLabel(object):
    label: str
    clickable: bool
    url: str

    def __init__(self, _label: str, _clickable: bool, _url: str):
        self.label = _label
        self.clickable = _clickable
        self.url = _url


# TODO CM - Rename this to something better?
@register.filter(name="my_paginator_range")
def my_paginator_range(page, paginator) -> List[PaginatorLabel]:
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

    # page_range is the number of pages either side of the current page number
    # to be displayed
    page_range = getattr(settings, "DJANGO_TABLES2_PAGE_RANGE", 2)

    num_pages = paginator.num_pages

    # A list of PaginatorLabel
    ret: List[PaginatorLabel] = []

    if page.number > 1:
        ret.append(PaginatorLabel("Prev", True, str(page.number - 1)))

    if page.number > page_range + 1:
        ret.append(PaginatorLabel("...", False, None))

    for p in range(
        max(1, page.number - page_range), min(num_pages, page.number + page_range) + 1
    ):
        if p == page.number:
            ret.append(PaginatorLabel(str(p), False, None))
        else:
            ret.append(PaginatorLabel(str(p), True, str(p)))

    if page.number < num_pages - page_range:
        ret.append(PaginatorLabel("...", False, None))

    if page.number < num_pages:
        ret.append(PaginatorLabel("Next", True, str(page.number + 1)))

    return ret
