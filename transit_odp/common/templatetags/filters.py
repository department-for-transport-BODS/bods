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


@register.filter("unique_by_property")
def unique_by_property(lta_objects, property_name):
    unique_values = []
    unique_items = []
    for lta_object in lta_objects:
        if getattr(lta_object, property_name) not in unique_values:
            unique_values.append(getattr(lta_object, property_name))
            unique_items.append(lta_object)
    return unique_items
