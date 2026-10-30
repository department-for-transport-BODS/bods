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
from transit_odp.api.views.auth import CurrentUserAPIView
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
from transit_odp.api.views.browser import (
    BrowseAdminAreaListView,
    BrowseAVLListView,
    BrowseFaresListView,
    BrowseOrganisationListView,
    BrowseTimetableListView,
)
from transit_odp.avl.views.dataset_detail_api import get_browse_avl_detail_api
from transit_odp.browse.views.dataset_subpages_api import (
    dataset_feedback_api,
    dataset_subscription_api,
    get_dataset_changelog_api,
    get_dataset_feedback_success_api,
    get_dataset_subscription_success_api,
)
from transit_odp.browse.views.download_api import (
    get_download_avl_api,
    get_download_coach_api,
    get_download_disruptions_api,
    get_download_fares_api,
    get_download_timetables_api,
)
from transit_odp.browse.views.operators_api import (
    licence_detail_api,
    licence_line_detail_api,
    operator_contact_api,
    operator_detail_api,
    operators_list_api,
)
from transit_odp.fares.views.dataset_detail_api import get_browse_fares_detail_api
from transit_odp.publish.views.api import AVLRealTimeDataView
from transit_odp.timetables.views.dataset_detail_api import (
    get_browse_timetable_detail_api,
)
from transit_odp.timetables.views.line_detail_api import (
    get_browse_timetable_line_detail_api,
)

app_name = "api"

# Data host dataset sub-pages (changelog, subscription, feedback), one set per
# dataset type: browser/<timetables|avl|fares>/<pk>/<sub-page>/
DATASET_SUBPAGE_PATTERNS = [
    path(
        f"browser/{kind}/<int:pk>/{route}",
        view,
        {"kind": kind},
        name=f"browser-{kind}-{name}",
    )
    for kind in ("timetables", "avl", "fares")
    for route, view, name in (
        ("changelog/", get_dataset_changelog_api, "changelog"),
        ("subscription/", dataset_subscription_api, "subscription"),
        (
            "subscription/success/",
            get_dataset_subscription_success_api,
            "subscription-success",
        ),
        ("feedback/", dataset_feedback_api, "feedback"),
        ("feedback/success/", get_dataset_feedback_success_api, "feedback-success"),
    )
]

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
    path(
        "browser/timetables/",
        BrowseTimetableListView.as_view(),
        name="browser-timetables",
    ),
    path(
        "browser/timetables/<int:pk>/",
        get_browse_timetable_detail_api,
        name="browser-timetable-detail",
    ),
    path(
        "browser/timetables/<int:pk>/line-detail/",
        get_browse_timetable_line_detail_api,
        name="browser-timetable-line-detail",
    ),
    *DATASET_SUBPAGE_PATTERNS,
    path("browser/avl/", BrowseAVLListView.as_view(), name="browser-avl"),
    path(
        "browser/avl/<int:pk>/",
        get_browse_avl_detail_api,
        name="browser-avl-detail",
    ),
    path("browser/fares/", BrowseFaresListView.as_view(), name="browser-fares"),
    path(
        "browser/fares/<int:pk>/",
        get_browse_fares_detail_api,
        name="browser-fares-detail",
    ),
    path(
        "browser/admin-areas/",
        BrowseAdminAreaListView.as_view(),
        name="browser-admin-areas",
    ),
    path(
        "browser/organisations/",
        BrowseOrganisationListView.as_view(),
        name="browser-organisations",
    ),
    path(
        "browser/downloads/timetables/",
        get_download_timetables_api,
        name="browser-download-timetables",
    ),
    path(
        "browser/downloads/avl/",
        get_download_avl_api,
        name="browser-download-avl",
    ),
    path(
        "browser/downloads/fares/",
        get_download_fares_api,
        name="browser-download-fares",
    ),
    path(
        "browser/downloads/disruptions/",
        get_download_disruptions_api,
        name="browser-download-disruptions",
    ),
    path(
        "browser/downloads/coach/",
        get_download_coach_api,
        name="browser-download-coach",
    ),
    path("browser/operators/", operators_list_api, name="browser-operators"),
    path(
        "browser/operators/<int:pk>/",
        operator_detail_api,
        name="browser-operator-detail",
    ),
    path(
        "browser/operators/<int:pk>/contact/",
        operator_contact_api,
        name="browser-operator-contact",
    ),
    path(
        "browser/operators/licence/<slug:number>/",
        licence_detail_api,
        name="browser-operator-licence-detail",
    ),
    path(
        "browser/operators/licence/<slug:number>/line/details/",
        licence_line_detail_api,
        name="browser-operator-licence-line-detail",
    ),
    path(
        "browser/avl-feed/real-time-bus-location/",
        AVLRealTimeDataView.as_view(),
        name="browser-avl-real-time-bus-location",
    ),
    # Authentication endpoints for NextJS
    path("user/", CurrentUserAPIView.as_view(), name="current-user"),
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
