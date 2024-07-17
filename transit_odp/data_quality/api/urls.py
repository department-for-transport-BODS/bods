from django.conf import settings
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from transit_odp.data_quality.api import views

app_name = "dq-api"

router = DefaultRouter()
router.register(r"service_link", views.ServiceLinkViewSet, "service_link")
router.register(r"service_pattern", views.ServicePatternViewSet, "service_pattern")
router.register(r"stop_point", views.StopPointViewSet, "stop_point")

urlpatterns = [
    path("", include(router.urls)),
]
if "django_axe" in settings.INSTALLED_APPS and settings.DJANGO_AXE_ENABLED:
    urlpatterns = [path("django_axe/", include("django_axe.urls"))] + urlpatterns
