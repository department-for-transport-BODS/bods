from typing import List, Optional, Set, Type, Union

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class HelperMixin(object):
    _helper: FormHelper = None
    helper_class: Type[FormHelper] = FormHelper

    # Helper properties
    form_tag: bool = True
    form_title: Optional[str] = None
    form_method: str = "post"
    form_error_title: Optional[str] = _("There is a problem")
    formset_error_title: Optional[str] = _("There is a problem")
    form_show_errors = True
    formset_show_errors = True
    page_heading_field: Optional[str] = None
    layout: Layout = None
    # TODO - this isn't right. The form shouldn't have to know if its
    # being used in a formset
    is_formset = False

    def get_helper_class(self):
        """Return the helper class to use."""
        return self.helper_class

    def get_helper_kwargs(self):
        """Return the keyword arguments for instantiating the helper.

        Note many of the helper's properties cannot be set through its constructor
        """
        return {}

    def get_helper_properties(self):
        """Return the properties to assign to the helper."""
        props = {
            "form_tag": self.form_tag,
            "page_heading_field": self.page_heading_field,
            "form_title": self.form_title,
            "form_method": self.form_method,
            "form_error_title": self.form_error_title,
            "formset_error_title": self.formset_error_title,
            "form_show_errors": self.form_show_errors,
            "formset_show_errors": self.formset_show_errors,
        }

        layout = self.get_layout()
        if layout is not None:
            # Don't override default layout if get_layout returns None
            props.update({"layout": layout})

        if self.is_formset:
            # we don't want any of these to be rendered in the child forms
            props.update(
                {
                    "form_tag": False,
                    "form_show_errors": False,
                    "formset_show_errors": False,
                    "disable_csrf": True,
                }
            )

        return props

    def get_helper(self, helper_class=None):
        """Return an instance of the helper to be used in this form."""
        if helper_class is None:
            helper_class = self.get_helper_class()

        # instantiate helper
        helper = helper_class(**self.get_helper_kwargs())

        # assign properties
        properties = self.get_helper_properties()
        for name, value in properties.items():
            setattr(helper, name, value)

        return helper

    @property
    def helper(self):
        if self._helper is None:
            self._helper = self.get_helper()
        return self._helper

    def get_layout(self):
        return self.layout

    def get_form_title(self):
        return self.form_title

    def get_form_error_title(self):
        return self.form_error_title


class GOVUKFormMixin(HelperMixin):
    WIDGET_ERROR_CLASSES = {
        "textinput": "govuk-input--error",
        "numberinput": "govuk-input--error",
        "emailinput": "govuk-input--error",
        "urlinput": "govuk-input--error",
        "passwordinput": "govuk-input--error",
        "textarea": "govuk-textarea--error",
        "fileinput": "govuk-file-upload--error",
        "clearablefileinput": "govuk-file-upload--error",
    }

    display_form_template: Optional[str] = None
    display_formset_template: Optional[str] = None
    errors_template: Optional[str] = None
    errors_formset_template: Optional[str] = None
    inputs_template: Optional[str] = None

    def is_valid(self):
        is_valid = super().is_valid()
        if not is_valid:
            # Initialisation of widget CSS error class depends on if the form's
            # fields have errors. Therefore, we must call set_error_classes which
            # does a full clean and then sets the classes.
            # TODO - rendering should ideally reflect changes to widget attributes
            # after initialisation
            self.set_error_classes()
        return is_valid

    def get_helper_properties(self):
        props = super().get_helper_properties()
        props.update(
            {
                "display_form_template": self.display_form_template,
                "display_formset_template": self.display_formset_template,
                "errors_template": self.errors_template,
                "errors_formset_template": self.errors_formset_template,
                "inputs_template": self.inputs_template,
            }
        )
        return props

    def set_error_classes(self):
        for f in self.errors:
            if f == "__all__":
                continue

            field = self[f].field
            self.set_field_errors(field)

    def set_field_errors(self, field):
        # Some fields have multiple widgets, e.g. DateInput.
        # TODO - I think this should be widgets.subwidgets
        widgets = getattr(
            field.widget, "widgets", [getattr(field.widget, "widget", field.widget)]
        )

        for widget in widgets:
            self.set_widget_classes(widget)

    @classmethod
    def set_widget_classes(cls, widget):
        # Note - this is duplicates some of the logic in crispy forms' CrispyFieldNode
        # to work around a bug.
        # The node checks to whether to apply the css class using
        # 'css_class.find(class_name) == -1'. Since we're using
        # BEM our error class will prevent the base class being applied, since
        # 'govuk-input' is a substring of 'govuk-input--error' so this method
        # applies both classes.

        # Get CSS classes for the type of widget
        css_classes = []
        widget_class = cls.get_widget_class(widget)
        if widget_class is not None:
            css_classes.append(widget_class)

        error_class = cls.get_widget_error_class(widget)
        if error_class is not None:
            css_classes.append(error_class)

        # Set css classes in widget's attributes
        cls.set_widget_class(widget, css_classes)

    @classmethod
    def set_widget_class(cls, widget, css_class: Union[str, List[str]]):

        if css_class is None:
            return

        css_classes: Set[str] = set()

        if isinstance(css_class, str):
            css_classes = set(css_class.split(" "))
        else:
            for c in css_class:
                css_classes = css_classes.union(set(c.split(" ")))

        # split class string to ensure we match on full class name
        widget_classes = widget.attrs.get("class", "")

        # split class to match class name exactly
        class_to_add = css_classes - set(widget_classes.split(" "))
        for c in list(class_to_add):
            widget_classes += " " + c

        widget.attrs["class"] = widget_classes

    @classmethod
    def get_widget_class(cls, widget):
        converters = settings.CRISPY_CLASS_CONVERTERS
        class_name = widget.__class__.__name__.lower()
        return converters.get(class_name, None)

    @classmethod
    def get_widget_error_class(cls, widget):
        class_name = widget.__class__.__name__.lower()
        return cls.WIDGET_ERROR_CLASSES.get(class_name, None)


class GOVUKForm(GOVUKFormMixin, forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class GOVUKModelForm(GOVUKFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
