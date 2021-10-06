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
    **kwargs,
):
    if host is None:
        host = settings.DEFAULT_HOST
    try:
        pattern = f"^{reverse(url, host=host, kwargs=kwargs)}"

    except NoReverseMatch:
        pattern = url

    if exact:
        pattern += "$"

    path = context["request"].build_absolute_uri()
    return css_class if re.search(pattern, path) else ""
