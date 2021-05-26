"""Urls for "crispy forms govuk" components."""
from django.urls import path
from sandbox.components import views

app_name = "components"

urlpatterns = [
    path("", view=views.ComponentsHomeView.as_view(), name="home"),
    path("checkbox/", view=views.CheckboxInputView.as_view(), name="checkbox"),
    path("checkboxes/", view=views.CheckboxesView.as_view(), name="checkboxes"),
    path("error-summary/", view=views.ErrorSummaryView.as_view(), name="error-summary"),
    path("file-upload/", view=views.FileUploadView.as_view(), name="file-upload"),
    path("text-input/", view=views.TextInputView.as_view(), name="text-input"),
    path("text-area/", view=views.TextAreaView.as_view(), name="text-area"),
]
