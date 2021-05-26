from config.settings.base import APP_VERSION_NUMBER
from django import template

register = template.Library()


@register.simple_tag
def version():
    return APP_VERSION_NUMBER
