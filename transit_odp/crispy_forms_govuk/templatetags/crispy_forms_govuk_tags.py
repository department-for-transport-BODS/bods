from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def debug_context(context):
    pass


@register.simple_tag()
def concat_str(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)
