import os

from crispy_forms.layout import ButtonHolder, Layout
from crispy_forms_govuk.layout import ButtonElement, ButtonSubmit, LinkButton
from tests.forms import BasicForm, EmptyForm
from tests.utils import write_output  # noqa: F401


def test_buttonelement(
    output_test_path, render_output, rendered_template, helper, client
):
    # Setup
    form = BasicForm()
    helper.layout = Layout("event", ButtonElement("copy", "copy", content="Copy"))

    expected = render_output(os.path.join(output_test_path, "test_buttonelement.html"))

    # Test
    actual = rendered_template(form, helper=helper)
    # write_output(output_test_path, "test_buttongroup_act.html", actual)
    # write_output(output_test_path, "test_buttongroup_out.html", expected)

    # Assert
    assert expected == actual


def test_buttonsubmit(
    output_test_path, render_output, rendered_template, helper, client
):
    # Setup
    form = BasicForm()
    helper.layout = Layout(
        "event", ButtonSubmit("save", "save", content="Save and continue")
    )

    expected = render_output(os.path.join(output_test_path, "test_buttonsubmit.html"))

    # Test
    actual = rendered_template(form, helper=helper)

    # Assert
    assert expected == actual


def test_cancellinkbutton(
    output_test_path, render_output, rendered_template, helper, client
):
    # Setup
    form = EmptyForm()
    helper.layout = Layout(
        ButtonHolder(
            ButtonSubmit("submit", "submit", content="Confirm"), LinkButton(url="/"),
        )
    )

    expected = render_output(
        os.path.join(output_test_path, "test_cancellinkbutton.html")
    )

    # Test
    actual = rendered_template(form, helper=helper)

    # Assert
    assert expected == actual
