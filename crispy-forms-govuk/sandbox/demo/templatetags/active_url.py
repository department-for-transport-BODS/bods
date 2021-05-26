import re

from django import template
from django.urls import NoReverseMatch, reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def active_url(
    context, url, css_class="govuk-header__navigation-item--active", exact=False
):
    try:
        pattern = "^%s" % reverse(url)
        if exact:
            pattern += "$"
    except NoReverseMatch:
        pattern = url

    path = context["request"].path
    # return "govuk-header__navigation-item--active" if re.search(pattern, path) else ''
    return css_class if re.search(pattern, path) else ""
