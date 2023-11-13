from typing import Any, Dict

from django.template import Library
from django.template.defaultfilters import floatformat

register = Library()


@register.filter("percentage")
def percentage(text, arg=-1):
    try:
        score = float(text)
    except (TypeError, ValueError):
        # Handle the case where the conversion to float fails (e.g., if value is not numeric)
        return text

    percentage_value = score * 100.0

    # If value is 0.1 then 1% should be returned
    # If value is 99.8 then 99% should be returned
    if 0 < percentage_value < 1:
        return "1%"
    elif 99 < percentage_value < 100:
        return "99%"
    return floatformat(percentage_value, arg=arg) + "%"


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
