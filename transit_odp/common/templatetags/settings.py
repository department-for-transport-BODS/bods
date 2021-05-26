from django import template
from django.conf import settings

register = template.Library()


@register.simple_tag
def session_cookie_age():
    """Exposes session cookie age in templates"""
    return str(settings.SESSION_COOKIE_AGE)
