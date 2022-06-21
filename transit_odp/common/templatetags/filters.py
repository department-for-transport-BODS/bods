from typing import Any, Dict

from django.template import Library
from django.template.defaultfilters import floatformat

register = Library()


@register.filter("percentage")
def percentage(text, arg=-1):
    return floatformat(text * 100.0, arg=arg) + "%"


@register.filter("lookup")
def lookup(d: Dict[Any, Any], key: Any) -> Any:
    return d[key]
