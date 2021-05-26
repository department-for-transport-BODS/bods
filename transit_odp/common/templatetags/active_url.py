import re

from django import template
from django.conf import settings
from django.urls import NoReverseMatch
from django_hosts.resolvers import reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def active_url(
    context,
    url,
    host=None,
    css_class="govuk-header__navigation-item--active",
    exact=False,
):
    if host is None:
        host = settings.DEFAULT_HOST
    try:
        pattern = "^%s" % reverse(url, host=host)
        if exact:
            pattern += "$"
    except NoReverseMatch:
        pattern = url

    path = context["request"].path
    # return "govuk-header__navigation-item--active" if re.search(pattern, path) else ''
    return css_class if re.search(pattern, path) else ""
