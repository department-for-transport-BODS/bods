from django import template

register = template.Library()


@register.filter("get_value_from_dict")
def get_value_from_dict(dict_data, key):
    """
    usage example {{ your_dict|get_value_from_dict:your_key }}
    """
    if key and key in dict_data:
        return True
    else:
        return False
