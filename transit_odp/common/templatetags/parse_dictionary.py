from django import template

register = template.Library()


@register.filter("is_value_in_dict")
def is_value_in_dict(dict_data, key):
    """
    usage example {{ your_dict|is_value_in_dict:your_key }}
    """
    if key and key in dict_data:
        return True
    else:
        return False

@register.filter
def concatenate(o1, o2):
    """ It returns variable type as a pure string name """
    return str(o1) + str(o2)


@register.filter("get_value_from_dict")
def get_value_from_dict(dict_data, key):
    """
    Return the 
    usage example {{ your_dict|get_value_from_dict:your_key }}
    """
    if key and key in dict_data:
        return dict_data[key]
    

    return ""
