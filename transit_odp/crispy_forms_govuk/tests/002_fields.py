import os

import pytest
from crispy_forms.layout import Layout
from crispy_forms_govuk.forms import GOVUKForm
from crispy_forms_govuk.layout.fields import HiddenField
from django import forms
from django.test.html import parse_html
from tests.forms import CheckboxForm
from tests.utils import write_output


@pytest.mark.skip
def test_checkboxfield(
    output_test_path, render_output, rendered_template, helper, client
):
    # Setup
    form = CheckboxForm()

    rendered = rendered_template(form, helper=helper)

    attempted = render_output(
        os.path.join(output_test_path, "fields/test_checkboxfield.html")
    )
    write_output(output_test_path, "test_checkboxfield_out.html", rendered)

    # Assert
    assert parse_html(attempted) == parse_html(rendered)


def test_hidden_field(output_test_path, render_output, rendered_template):
    # Setup
    class FormWithHiddenField(GOVUKForm):
        delete = forms.BooleanField()

        def get_layout(self):
            return Layout(HiddenField("delete"))

    form = FormWithHiddenField()

    expected = render_output(
        os.path.join(output_test_path, "fields/test_hiddenfield.html")
    )

    # Test
    actual = rendered_template(form)

    # Assert
    assert parse_html(actual) == parse_html(expected)
