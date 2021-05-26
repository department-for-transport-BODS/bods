"""Sandbox URL Configuration."""
from django.conf.urls import include, url
from django.urls import path
from django.views.generic.base import TemplateView

urlpatterns = [
    # Dummy homepage just for simple ping view
    url(r"^$", TemplateView.as_view(template_name="home.html"), name="home"),
    path("components/", include("sandbox.components.urls", namespace="components")),
    path("examples/", include("sandbox.examples.urls", namespace="examples")),
]

try:
    import debug_toolbar

    urlpatterns += [url(r"^__debug__/", include(debug_toolbar.urls))]
except ImportError:
    pass
