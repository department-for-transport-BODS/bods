from django import template

register = template.Library()

@register.filter
def round_percentage(value):
    try:
        value = float(value.rstrip('%'))
        return f'{int(value)}%'
    except ValueError:
        return value