import pytest

from transit_odp.publish.templatetags.publish_stepper import stepper


def gen_expected_text_publish(order_list):
    step1, step2, step3 = order_list
    return f"""<ol class="publish-stepper govuk-breadcrumbs__list">
<li class="publish-stepper__item publish-stepper__item--{step1}">1. Describe data</li>
<li class="publish-stepper__item publish-stepper__item--{step2}">2. Provide data</li>
<li class="publish-stepper__item publish-stepper__item--{step3}">3. Review and publish</li>
</ol>"""  # noqa


def gen_expected_text_update(order_list):
    step1, step2, step3 = order_list
    return f"""<ol class="publish-stepper govuk-breadcrumbs__list">
<li class="publish-stepper__item publish-stepper__item--{step1}">1. Comment</li>
<li class="publish-stepper__item publish-stepper__item--{step2}">2. Update</li>
<li class="publish-stepper__item publish-stepper__item--{step3}">3. Review and publish</li>
</ol>"""  # noqa


def test_stepper_errors_on_no_current_step():
    context = {}
    with pytest.raises(KeyError) as e:
        stepper(context)
    assert str(e.value) == "'current_step needs to be in the context for this to work'"


def test_stepper_errors_on_wrong_current_step():
    context = {"current_step": "I LIKE TRAINS"}
    with pytest.raises(ValueError) as e:
        stepper(context)
    assert str(e.value) == "current_step needs to be one of description, upload, review"


def test_stepper_errors_on_wrong_current_step_update():
    context = {"current_step": "I LIKE TRAINS", "is_update": True}
    with pytest.raises(ValueError) as e:
        stepper(context)
    assert str(e.value) == "current_step needs to be one of comment, upload, review"


@pytest.mark.parametrize(
    "context, steps",
    (
        ({"current_step": "description"}, ("selected", "next", "next")),
        ({"current_step": "upload"}, ("previous", "selected", "next")),
    ),
    ids=["test current step is description", "test current step is upload"],
)
def test_stepper_works_for_publish(context, steps):
    output_html = stepper(context)
    assert str(output_html) == gen_expected_text_publish(steps)


@pytest.mark.parametrize(
    "context, steps",
    (
        ({"current_step": "comment"}, ("selected", "next", "next")),
        ({"current_step": "upload"}, ("previous", "selected", "next")),
    ),
    ids=["test current step is comment", "test current step is update"],
)
def test_stepper_works_for_update(context, steps):
    context.update({"is_update": True})
    output_html = stepper(context)
    assert str(output_html) == gen_expected_text_update(steps)
