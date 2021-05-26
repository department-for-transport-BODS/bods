"""Urls for "crispy forms govuk" demo."""
from django.urls import path
from sandbox.examples import views

app_name = "examples"

urlpatterns = [
    path("", view=views.ExamplesHomeView.as_view(), name="home"),
    path("signup/", view=views.SignupView.as_view(), name="signup"),
    path(
        "question-page-with-label/",
        view=views.QuestionPageWithLabelView.as_view(),
        name="question-page-with-label",
    ),
    path(
        "question-page-with-legend/",
        view=views.QuestionPageWithLegendView.as_view(),
        name="question-page-with-legend",
    ),
    path("formset/", view=views.FormsetExampleView.as_view(), name="formset",),
]
