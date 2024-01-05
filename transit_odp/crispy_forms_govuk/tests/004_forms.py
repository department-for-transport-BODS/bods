import os

import pytest
from crispy_forms.layout import Layout
from crispy_forms_govuk.forms import GOVUKForm
from django import forms
from django.test.html import parse_html
from sandbox.components.forms import (
    CheckboxesForm,
    CheckboxInputForm,
    FileUploadForm,
    TextAreaForm,
    TextInputForm,
)
from sandbox.examples.forms import PostCodeQuestionPageForm, RadiosQuestionPage
from tests.forms import FormWithErrorFrom


class TestGOVUKForm:
    @pytest.mark.parametrize(
        "widget,expected_class",
        [
            (forms.TextInput(), "govuk-input govuk-input--error"),
            (forms.NumberInput(), "govuk-input govuk-input--error"),
            (forms.EmailInput(), "govuk-input govuk-input--error"),
            (forms.URLInput(), "govuk-input govuk-input--error"),
            (forms.PasswordInput(), "govuk-input govuk-input--error"),
            (forms.Textarea(), "govuk-textarea govuk-textarea--error"),
            (forms.FileInput(), "govuk-file-upload govuk-file-upload--error"),
            (forms.ClearableFileInput(), "govuk-file-upload govuk-file-upload--error"),
        ],
    )
    def test_set_widget_error_class(self, widget, expected_class):
        """Tests the appropriate css classes are applied to the widgets class attribute"""
        # Test
        GOVUKForm.set_widget_classes(widget)

        # Assert
        widget_classes = widget.attrs.get("class", "").split(" ")
        for css_class in expected_class.split(" "):
            assert css_class in widget_classes

    @pytest.mark.parametrize(
        "class_string,expected_class",
        [("a", "a"), ("a b", "a b"), (["a", "b"], "a b"), (["a", "b c"], "a b c")],
    )
    def test_set_widget_class(self, class_string, expected_class):
        # Setup
        widget = forms.TextInput()

        # Test
        GOVUKForm.set_widget_class(widget, class_string)

        # Assert
        widget_class = widget.attrs.get("class", "")
        for css_class in widget_class.split(" "):
            assert css_class in expected_class

    def test_form_sets_widget_error_classes(self):
        """Tests error class is set on the widget when is_valid is called"""
        # Setup
        # create an instance of a form with empty data
        form = FormWithErrorFrom(data={})

        # Test
        is_valid = form.is_valid()

        # Assert
        assert is_valid is False
        field = form.fields["event"]
        widget_class = field.widget.attrs.get("class", "")
        assert "govuk-input--error" in widget_class

    def test_helper_initialised_with_form_attributes(self):
        # Setup
        class TestForm(GOVUKForm):
            form_tag = False
            form_title = "Your details"
            form_method = "get"
            form_error_title = "There is a problem"
            page_heading_field = "somefield"

            somefield = forms.CharField()

            def get_layout(self):
                return "some layout"  # Note this should be of type Layout but cannot assert for equality

        form = TestForm()

        # Test
        helper = form.helper

        # Assert
        assert helper.form_tag is False
        assert helper.form_title == "Your details"
        assert helper.form_method == "get"
        assert helper.form_error_title == "There is a problem"
        assert helper.page_heading_field == "somefield"
        assert helper.layout == "some layout"


def test_checkbox_form(output_test_path, render_output, rendered_template, client):
    # Setup
    form = CheckboxInputForm()

    expected = render_output(os.path.join(output_test_path, "test_checkbox_form.html"))

    # Test
    actual = rendered_template(form)

    # Assert
    assert parse_html(actual) == parse_html(expected)


def test_checkboxes_form(output_test_path, render_output, rendered_template, client):
    # Setup
    form = CheckboxesForm()

    expected = render_output(
        os.path.join(output_test_path, "test_checkboxes_form.html")
    )

    # Test
    actual = rendered_template(form)

    # Assert
    assert parse_html(actual) == parse_html(expected)


def test_file_upload(output_test_path, render_output, rendered_template, client):
    # Setup
    form = FileUploadForm()

    expected = render_output(os.path.join(output_test_path, "test_file_upload.html"))

    # Test
    actual = rendered_template(form)

    # Assert
    assert parse_html(actual) == parse_html(expected)


def test_question_page_renders_label_as_page_heading(
    output_test_path, render_output, rendered_template, client
):
    # Setup
    form = PostCodeQuestionPageForm()

    expected = render_output(
        os.path.join(output_test_path, "test_question_page_with_label.html")
    )

    # Test
    actual = rendered_template(form)

    # Assert
    assert parse_html(actual) == parse_html(expected)


def test_question_page_renders_legend_as_page_heading(
    output_test_path, render_output, rendered_template, client
):
    # Setup
    form = RadiosQuestionPage()

    expected = render_output(
        os.path.join(output_test_path, "test_question_page_with_legend.html")
    )

    # Test
    actual = rendered_template(form)

    # Assert
    assert parse_html(actual) == parse_html(expected)


def test_text_input(output_test_path, render_output, rendered_template, client):
    # Setup
    form = TextInputForm()

    expected = render_output(os.path.join(output_test_path, "test_text_input.html"))

    # Test
    actual = rendered_template(form)

    # Assert
    assert parse_html(actual) == parse_html(expected)


def test_text_area(output_test_path, render_output, rendered_template, client):
    # Setup
    form = TextAreaForm()

    expected = render_output(os.path.join(output_test_path, "test_text_area.html"))

    # Test
    actual = rendered_template(form)

    # Assert
    assert parse_html(actual) == parse_html(expected)
