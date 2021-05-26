# -*- coding: utf-8 -*-
"""Views."""
from django.views.generic import FormView, TemplateView
from sandbox.components import forms

try:
    # Default 'reverse' path since Django1.10
    from django.urls import reverse, reverse_lazy
except ImportError:
    # 'reverse' path for Django<1.10
    from django.core.urlresolvers import reverse


# COMPONENTS


class ComponentSidebarMixin(object):
    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context.update(
            {
                "links": [
                    {"label": "Character count", "viewname": "#"},
                    {"label": "Checkbox", "viewname": "components:checkbox"},
                    {"label": "Checkboxes", "viewname": "components:checkboxes"},
                    {"label": "Date input", "viewname": "#"},
                    {"label": "Error message", "viewname": "#"},
                    {"label": "Error summary", "viewname": "components:error-summary"},
                    {"label": "Fieldset", "viewname": "#"},
                    {"label": "File upload", "viewname": "components:file-upload"},
                    {"label": "Radios", "viewname": "#"},
                    {"label": "Select", "viewname": "#"},
                    {"label": "Text input", "viewname": "components:text-input"},
                    {"label": "Textarea", "viewname": "components:text-area"},
                ]
            }
        )
        return context


class ComponentsHomeView(ComponentSidebarMixin, TemplateView):
    template_name = "components/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context.update(
            {
                "page_heading": "Components",
                "intro": """List of crispy forms components for the
                        <a class="govuk-link" href="https://design-system.service.gov.uk/">GovUK Design System</a>""",
            }
        )
        return context


class CheckboxInputView(ComponentsHomeView, FormView):
    template_name = "components/checkbox.html"
    form_class = forms.CheckboxInputForm
    success_url = reverse_lazy("components:checkbox")


class CheckboxesView(ComponentsHomeView, FormView):
    template_name = "components/checkboxes.html"
    form_class = forms.CheckboxesForm
    success_url = reverse_lazy("components:checkboxes")


class ErrorSummaryView(ComponentsHomeView, FormView):
    template_name = "components/error-summary.html"
    form_class = forms.ErrorSummaryForm
    success_url = reverse_lazy("components:error-summary")


class FileUploadView(ComponentsHomeView, FormView):
    template_name = "components/fileupload.html"
    form_class = forms.FileUploadForm
    success_url = reverse_lazy("components:file-upload")


class TextInputView(ComponentsHomeView, FormView):
    template_name = "components/textinput.html"
    form_class = forms.TextInputForm
    success_url = reverse_lazy("components:text-input")


class TextAreaView(ComponentsHomeView, FormView):
    template_name = "components/textarea.html"
    form_class = forms.TextAreaForm
    success_url = reverse_lazy("components:text-area")
