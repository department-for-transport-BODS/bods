# -*- coding: utf-8 -*-
"""Views."""
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from sandbox.demo import models
from sandbox.examples import forms

try:
    # Default 'reverse' path since Django1.10
    from django.urls import reverse, reverse_lazy
except ImportError:
    # 'reverse' path for Django<1.10
    from django.core.urlresolvers import reverse


# EXAMPLES


class ExampleSidebarMixin(object):
    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context.update(
            {
                "links": [
                    {"label": "Sign Up Page", "viewname": "examples:signup"},
                    {
                        "label": "Question Page with Label",
                        "viewname": "examples:question-page-with-label",
                    },
                    {
                        "label": "Question Page with Legend",
                        "viewname": "examples:question-page-with-legend",
                    },
                    {"label": "Formset Example", "viewname": "examples:formset",},
                ]
            }
        )
        return context


class ExamplesHomeView(ExampleSidebarMixin, TemplateView):
    template_name = "examples/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context.update(
            {
                "page_heading": "Examples",
                "intro": """List of examples using the
                        <a class="govuk-link" href="https://design-system.service.gov.uk/">GovUK Design System</a>""",
            }
        )
        return context


class SignupView(ExamplesHomeView, FormView):
    template_name = "examples/signup.html"
    form_class = forms.SignupForm
    success_url = reverse_lazy("examples:signup")


class QuestionPageWithLabelView(ExamplesHomeView, FormView):
    template_name = "examples/question_page_with_label.html"
    form_class = forms.PostCodeQuestionPageForm
    success_url = reverse_lazy("examples:question-page-with-label")


class QuestionPageWithLegendView(ExamplesHomeView, FormView):
    template_name = "examples/question_page_with_legend.html"
    form_class = forms.RadiosQuestionPage
    success_url = reverse_lazy("examples:question-page-with-legend")


class FormsetExampleView(ExamplesHomeView, FormView):
    template_name = "examples/formset_example.html"
    form_class = forms.NOCFormset
    success_url = reverse_lazy("examples:formset")

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        organisation = models.Organisation.objects.get_or_create(name="Demo Org")[0]
        kwargs.update({"instance": organisation})
        return kwargs
