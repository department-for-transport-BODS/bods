from django.contrib import admin
from django.urls import path
from fares_validator import views


urlpatterns = [
    path('validate/', views.FaresXmlValidator, name='fares_validator'),
]