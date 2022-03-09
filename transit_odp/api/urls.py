from django.conf import settings
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_swagger.views import get_swagger_view

from transit_odp.api.views import (
    AVLApiView,
    AVLDetailApiView,
    AVLGTFSRTApiView,
    AVLOpenApiView,
    FaresDatasetViewset,
    FaresOpenApiView,
    TimetablesApiView,
    TimetablesViewSet,
    v2,
)

app_name = "api"

# TODO - refactor into api_v1,
router_v1 = DefaultRouter()
router_v1.register(r"dataset", TimetablesViewSet, "feed")
router_v1.register(r"fares/dataset", FaresDatasetViewset, "fares-api")

router_v2 = DefaultRouter()
router_v2.register(r"operators", viewset=v2.OperatorViewSet, basename="operators")
router_v2.register(r"timetables", viewset=v2.TimetableViewSet, basename="timetables")
router_v2.register(r"txcfiles", viewset=v2.TimetableFilesViewSet, basename="txcfiles")
router_v2.register(r"avlfeeds", viewset=v2.DatafeedViewSet, basename="avlfeeds")

schema_view = get_swagger_view(title="Timetables Data API")
avl_views = get_swagger_view(title="Bus Location Data API")
fares_views = get_swagger_view(title="Fares Data API")

urlpatterns = []

if settings.IS_AVL_FEATURE_FLAG_ENABLED:
    urlpatterns += [
        path("buslocation-openapi/", AVLOpenApiView.as_view(), name="avlopenapi"),
        path("v1/datafeed/", AVLApiView.as_view(), name="avldatafeedapi"),
        path(
            "v1/datafeed/<int:pk>/",
            AVLDetailApiView.as_view(),
            name="avldetaildatafeedapi",
        ),
        path(
            "v1/gtfsrtdatafeed/", AVLGTFSRTApiView.as_view(), name="gtfsrtdatafeedapi"
        ),
    ]

if settings.IS_FARES_FEATURE_FLAG_ENABLED:
    urlpatterns.append(
        path("fares-openapi/", FaresOpenApiView.as_view(), name="faresopenapi")
    )

if urlpatterns:
    # At least one flag is enabled
    urlpatterns = [
        path("timetable-openapi/", TimetablesApiView.as_view(), name="timetableopenapi")
    ] + urlpatterns

else:
    urlpatterns = [
        path(
            "openapi/",
            TimetablesApiView.as_view(),
            name="openapi",
        )
    ]

urlpatterns += [
    path("app/", include("transit_odp.api.app.urls")),
    path("v1/", include(router_v1.urls)),
    path("v2/", include((router_v2.urls, app_name), namespace="v2")),
]
