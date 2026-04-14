from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_swagger.views import get_swagger_view

from transit_odp.api.views import (
    AVLApiView,
    AVLApiServiceView,
    AVLDetailApiView,
    AVLGTFSRTApiView,
    AVLOpenApiView,
    DisruptionsOverview,
    DisruptionsOpenApiView,
    CancellationsOverview,
    CancellationsOpenApiView,
    FaresDatasetViewset,
    FaresOpenApiView,
    TimetablesApiView,
    TimetablesViewSet,
    v2,
)
from transit_odp.api.views.avl import (
    AVLManageSubscriptionsView,
    AVLManageSubscriptionDetailView,
    AVLManageSubscriptionDeactivateView,
    AVLManageSubscriptionDeactivateSuccessView,
    AVLConsumerSubscriptionsApiViewSet,
    AVLConsumerSubscriptionApiViewSet,
    AVLSubscriptionsSubscribeView,
    AVLSubscriptionsSubscribeSuccessView,
)
from transit_odp.api.views.disruptions import (
    DisruptionsApiView,
    DisruptionsGtfsRtServiceAlertsApiView,
)
from transit_odp.api.views.cancellations import CancellationsApiView

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
disruptions_views = get_swagger_view(title="Disruption Data API")

urlpatterns = [
    path("timetable-openapi/", TimetablesApiView.as_view(), name="timetableopenapi"),
    path("buslocation-api/", AVLApiServiceView.as_view(), name="buslocation-api"),
    path(
        "buslocation-api/openapi/",
        AVLOpenApiView.as_view(),
        name="buslocation-tryapi",
    ),
    path(
        "buslocation-api/subscribe/",
        AVLSubscriptionsSubscribeView.as_view(),
        name="buslocation-subscribe",
    ),
    path(
        "buslocation-api/manage-subscriptions/",
        AVLManageSubscriptionsView.as_view(),
        name="buslocation-manage-subscriptions",
    ),
    path(
        "buslocation-api/manage-subscriptions/<str:subscription_id>/",
        AVLManageSubscriptionDetailView.as_view(),
        name="buslocation-manage-subscription",
    ),
    path(
        "buslocation-api/manage-subscriptions/<str:subscription_id>/deactivate",
        AVLManageSubscriptionDeactivateView.as_view(),
        name="buslocation-manage-subscription-deactivate",
    ),
    path(
        "buslocation-api/manage-subscriptions/<str:subscription_id>/deactivate/success",
        AVLManageSubscriptionDeactivateSuccessView.as_view(),
        name="buslocation-manage-subscription-deactivate-success",
    ),
    path(
        "buslocation-api/subscribe/success/",
        AVLSubscriptionsSubscribeSuccessView.as_view(),
        name="buslocation-subscribe-success",
    ),
    path("fares-openapi/", FaresOpenApiView.as_view(), name="faresopenapi"),
    path(
        "disruptions-api-overview/",
        DisruptionsOverview.as_view(),
        name="disruptionsapioverview",
    ),
    path(
        "disruptions-openapi/",
        DisruptionsOpenApiView.as_view(),
        name="disruptionsopenapi",
    ),
    path(
        "cancellations-api-overview/",
        CancellationsOverview.as_view(),
        name="cancellationsapioverview",
    ),
    path(
        "cancellations-openapi/",
        CancellationsOpenApiView.as_view(),
        name="cancellationsopenapi",
    ),
    path("app/", include("transit_odp.api.app.urls")),
    path("v1/", include(router_v1.urls)),
    path("v1/datafeed/", AVLApiView.as_view(), name="avldatafeedapi"),
    path(
        "v1/siri-vm/subscriptions/",
        AVLConsumerSubscriptionsApiViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="avlconsumersubscriptionsapi",
    ),
    path(
        "v1/siri-vm/subscriptions/<str:subscription_id>/",
        AVLConsumerSubscriptionApiViewSet.as_view(
            {
                "get": "list",
                "delete": "destroy",
            }
        ),
        name="avlconsumersubscriptionapi",
    ),
    path("v1/siri-sx/", DisruptionsApiView.as_view(), name="disruptionsapi"),
    path(
        "v1/siri-sx/cancellations/",
        CancellationsApiView.as_view(),
        name="cancellationsapi",
    ),
    path(
        "v1/gtfs-rt/service-alerts",
        DisruptionsGtfsRtServiceAlertsApiView.as_view(),
        name="gtfsrtservicealertsapi",
    ),
    path(
        "v1/datafeed/<int:pk>/", AVLDetailApiView.as_view(), name="avldetaildatafeedapi"
    ),
    path("v1/gtfsrtdatafeed/", AVLGTFSRTApiView.as_view(), name="gtfsrtdatafeedapi"),
    path("v2/", include((router_v2.urls, app_name), namespace="v2")),
]
