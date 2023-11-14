from django.urls import path
from django.urls import include
from rest_framework.routers import DefaultRouter

from transit_odp.api.app import views

app_name = "app"


router = DefaultRouter()

# TODO - abstract specific revision id out of API e.g.
#  * /dataset/:id/live/...
#  * /dataset/:id/draft/...
router.register(r"revision", views.DatasetRevisionViewSet, "revision")

# APIs for rendering map data
router.register(r"stop_point", views.StopViewSet, "stop")
router.register(r"service_pattern", views.ServicePatternViewSet, "service_pattern")
router.register(r"fare_stops", views.FareStopsViewSet, "fare_stops")

urlpatterns = [
    path("", include(router.urls)),
]
