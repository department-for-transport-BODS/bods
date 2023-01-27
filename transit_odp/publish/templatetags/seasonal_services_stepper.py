from django import template
from django.utils.html import format_html

register = template.Library()


@register.simple_tag(takes_context=True)
def stepper(context):
    """
    Simple template tag to generate a stepper for the seasonal services

    :param context: must include the current step.
    :return:
    """
    # What is the current step?
    current_step = context.get("current_step")
    if current_step is None:
        raise KeyError("current_step needs to be in the context for this to work")

    steps = ("select_psv_licence_number", "provide_operating_dates")
    step_labels = ("Select PSV licence number", "Provide operating dates")

    try:
        # Where are we the current process?
        current_index = steps.index(current_step)
    except ValueError as e:
        # current step not in steps, check that its all lowercase.
        # maybe you are adding a step so it will need to be added here
        choices = ", ".join(steps)
        msg = f"current_step needs to be one of {choices}"
        raise ValueError(msg) from e

    html = """<ol class="publish-stepper govuk-breadcrumbs__list">\n"""
    for index, step in enumerate(step_labels):
        element = """<li class="publish-stepper__item"""
        if index < current_index:
            # Past steps
            element += " publish-stepper__item--previous"
        elif index > current_index:
            # Future steps
            element += " publish-stepper__item--next"
        else:
            # current step
            element += " publish-stepper__item--selected"

        element += f"""">{index + 1}. {step}</li>"""
        html += element + "\n"
    html += "</ol>"
    return format_html(html)
