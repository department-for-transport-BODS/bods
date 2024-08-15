from django.urls import include, path

from transit_odp.data_quality import views
from transit_odp.dqs import views as DQSviews

app_name = "dq"

urlpatterns = [
    path("", view=views.ReportOverviewView.as_view(), name="overview"),
    path("glossary/", view=views.DataQualityGlossaryView.as_view(), name="glossary"),
    path("csv/", view=views.ReportCSVDownloadView.as_view(), name="report-csv"),
    path(
        "fast-timings/",
        include(
            [
                path(
                    "",
                    view=views.FastTimingListView.as_view(),
                    name="fast-timings-list",
                ),
                path(
                    "<uuid:warning_pk>/",
                    view=views.FastTimingDetailView.as_view(),
                    name="fast-timings-detail",
                ),
            ]
        ),
    ),
    path(
        "slow-timings/",
        include(
            [
                path(
                    "",
                    view=views.SlowTimingsListView.as_view(),
                    name="slow-timings-list",
                ),
                path(
                    "<uuid:warning_pk>/",
                    view=views.SlowTimingsDetailView.as_view(),
                    name="slow-timings-detail",
                ),
            ]
        ),
    ),
    path(
        "fast-links/",
        include(
            [
                path(
                    "",
                    view=views.FastLinkListView.as_view(),
                    name="fast-link-list",
                ),
                path(
                    "<uuid:warning_pk>/",
                    view=views.FastLinkDetailView.as_view(),
                    name="fast-link-detail",
                ),
            ]
        ),
    ),
    path(
        "slow-links/",
        include(
            [
                path("", view=views.SlowLinkListView.as_view(), name="slow-link-list"),
                path(
                    "<uuid:warning_pk>/",
                    view=views.SlowLinkDetailView.as_view(),
                    name="slow-link-detail",
                ),
            ]
        ),
    ),
    path(
        "duplicate-journeys/",
        include(
            [
                path(
                    "",
                    view=views.DuplicateJourneyListView.as_view(),
                    name="duplicate-journey-list",
                ),
                path(
                    "<uuid:warning_pk>/",
                    view=views.DuplicateJourneyDetailView.as_view(),
                    name="duplicate-journey-detail",
                ),
            ]
        ),
    ),
    path(
        "backward-timing/",
        include(
            [
                path(
                    "",
                    view=views.BackwardTimingListView.as_view(),
                    name="backward-timing-list",
                ),
                path(
                    "<uuid:warning_pk>/",
                    view=views.BackwardTimingDetailView.as_view(),
                    name="backward-timing-detail",
                ),
            ]
        ),
    ),
    path(
        "incorrect-noc/",
        include(
            [
                path(
                    "",
                    view=views.IncorrectNOCListView.as_view(),
                    name="incorrect-noc-list",
                ),
            ]
        ),
    ),
    path(
        "pick-up-only/",
        include(
            [
                path(
                    "",
                    view=views.LastStopPickUpListView.as_view(),
                    name="last-stop-pick-up-only-list",
                ),
                path(
                    "<uuid:warning_pk>/",
                    view=views.LastStopPickUpDetailView.as_view(),
                    name="last-stop-pick-up-only-detail",
                ),
                path(
                    "detail/",
                    view=DQSviews.LastStopPickUpDetailView.as_view(),
                    name="dqs-last-stop-pick-up-only-detail",
                ),
            ]
        ),
    ),
    path(
        "drop-off-only/",
        include(
            [
                path(
                    "",
                    view=views.FirstStopDropOffListView.as_view(),
                    name="first-stop-set-down-only-list",
                ),
                path(
                    "<uuid:warning_pk>/",
                    view=views.FirstStopDropOffDetailView.as_view(),
                    name="first-stop-set-down-only-detail",
                ),
                path(
                    "detail/",
                    view=DQSviews.FirstStopSetDownDetailView.as_view(),
                    name="dqs-first-stop-set-down-only-detail",
                ),
            ]
        ),
    ),
    path(
        "last-stop-not-timing-point/",
        include(
            [
                path(
                    "",
                    view=views.LastStopNotTimingListView.as_view(),
                    name="last-stop-not-timing-point-list",
                ),
                path(
                    "<uuid:warning_pk>/",
                    view=views.LastStopNotTimingDetailView.as_view(),
                    name="last-stop-not-timing-point-detail",
                ),
                path(
                    "detail/",
                    view=DQSviews.LastStopNotTimingPointDetailView.as_view(),
                    name="dqs-last-stop-not-timing-point-detail",
                ),
            ]
        ),
    ),
    path(
        "first-stop-not-timing-point/",
        include(
            [
                path(
                    "",
                    view=views.FirstStopNotTimingListView.as_view(),
                    name="first-stop-not-timing-point-list",
                ),
                path(
                    "<uuid:warning_pk>/",
                    view=views.FirstStopNotTimingDetailView.as_view(),
                    name="first-stop-not-timing-point-detail",
                ),
                path(
                    "detail/",
                    view=DQSviews.FirstStopNotTimingPointDetailView.as_view(),
                    name="dqs-first-stop-not-timing-point-detail",
                ),
            ]
        ),
    ),
    path(
        "stop-not-in-naptan/",
        include(
            [
                path(
                    "",
                    view=views.StopMissingNaptanListView.as_view(),
                    name="stop-missing-naptan-list",
                ),
                path(
                    "<uuid:warning_pk>/",
                    view=views.StopMissingNaptanDetailView.as_view(),
                    name="stop-missing-naptan-detail",
                ),
                path(
                    "detail/",
                    view=DQSviews.StopMissingNaptanDetailView.as_view(),
                    name="dqs-stop-missing-naptan-detail",
                ),
            ]
        ),
    ),
    path(
        "service-link-missing-stops/",
        include(
            [
                path(
                    "",
                    view=views.ServiceLinkMissingStopListView.as_view(),
                    name="service-link-missing-stops-list",
                ),
                path(
                    "<uuid:warning_pk>/",
                    view=views.ServiceLinkMissingStopDetailView.as_view(),
                    name="service-link-missing-stops-detail",
                ),
            ]
        ),
    ),
    path(
        "multiple-stops/",
        include(
            [
                path(
                    "",
                    view=views.StopRepeatedListView.as_view(),
                    name="stop-repeated-list",
                ),
                path(
                    "<uuid:warning_pk>/",
                    view=views.StopRepeatedDetailView.as_view(),
                    name="stop-repeated-detail",
                ),
            ]
        ),
    ),
    path(
        "missing-stops/",
        include(
            [
                path(
                    "",
                    view=views.MissingStopListView.as_view(),
                    name="missing-stops-list",
                ),
                path(
                    "<uuid:warning_pk>/",
                    view=views.MissingStopDetailView.as_view(),
                    name="missing-stops-detail",
                ),
            ]
        ),
    ),
    path(
        "journey-overlap/",
        include(
            [
                path(
                    "",
                    view=views.JourneyOverlapListView.as_view(),
                    name="journey-overlap-list",
                ),
                path(
                    "<uuid:warning_pk>/",
                    view=views.JourneyOverlapDetailView.as_view(),
                    name="journey-overlap-detail",
                ),
            ]
        ),
    ),
    path(
        "backward-date-range/",
        include(
            [
                path(
                    "",
                    view=views.BackwardDateRangeListView.as_view(),
                    name="backward-date-range-list",
                ),
                path(
                    "<uuid:warning_pk>/",
                    view=views.BackwardDateRangeDetailView.as_view(),
                    name="backward-date-range-detail",
                ),
            ]
        ),
    ),
    path(
        "incorrect-stop-type/",
        include(
            [
                path(
                    "",
                    view=views.IncorrectStopTypeListView.as_view(),
                    name="incorrect-stop-type-list",
                ),
                path(
                    "<uuid:warning_pk>/",
                    view=views.IncorrectStopTypeDetailView.as_view(),
                    name="incorrect-stop-type-detail",
                ),
                path(
                    "detail/",
                    view=DQSviews.IncorrectStopTypeDetailView.as_view(),
                    name="dqs-incorrect-stop-type-detail",
                ),
            ]
        ),
    ),
    path(
        "line-expired/",
        include(
            [
                path(
                    "",
                    view=views.LineExpiredListView.as_view(),
                    name="line-expired-list",
                )
            ]
        ),
    ),
    path(
        "line-missing-block-id/",
        include(
            [
                path(
                    "",
                    view=views.LineMissingBlockIDListView.as_view(),
                    name="line-missing-block-id-list",
                ),
                path(
                    "<uuid:warning_pk>/",
                    view=views.LineMissingBlockIDDetailView.as_view(),
                    name="line-missing-block-id-detail",
                ),
            ]
        ),
    ),
    path(
        "missing-journey-code/",
        include(
            [
                path(
                    "",
                    view=DQSviews.MissingJourneyCodeListView.as_view(),
                    name="missing-journey-code-list",
                ),
                path(
                    "detail/",
                    view=DQSviews.MissingJourneyCodeDetailView.as_view(),
                    name="missing-journey-code-detail",
                ),
            ]
        ),
    ),
    path(
        "duplicate-journey-code/",
        include(
            [
                path(
                    "",
                    view=DQSviews.DuplicateJourneyCodeListView.as_view(),
                    name="duplicate-journey-code-list",
                ),
                path(
                    "detail/",
                    view=DQSviews.DuplicateJourneyCodeDetailView.as_view(),
                    name="duplicate-journey-code-detail",
                ),
            ]
        ),
    ),
    path(
        "incorrect-licence-number/",
        include(
            [
                path(
                    "",
                    view=DQSviews.IncorrectLicenceNumberListView.as_view(),
                    name="incorrect-licence-number-list",
                )
            ]
        ),
    ),
    path(
        "no-timing-point-more-than-15-mins/",
        include(
            [
                path(
                    "",
                    view=DQSviews.NoTimingPointMoreThan15MinsListView.as_view(),
                    name="no-timing-point-more-than-15-mins-list",
                ),
                path(
                    "detail/",
                    view=DQSviews.NoTimingPointMoreThan15MinsDetailView.as_view(),
                    name="no-timing-point-more-than-15-mins-detail",
                ),
            ]
        ),
    ),
    path(
        "missing-bus-working-number/",
        include(
            [
                path(
                    "",
                    view=DQSviews.MissingBusWorkingNumberListView.as_view(),
                    name="missing-bus-working-number-list",
                ),
                path(
                    "detail/",
                    view=DQSviews.MissingBusWorkingNumberDetailView.as_view(),
                    name="missing-bus-working-number-detail",
                ),
            ]
        ),
    ),
    path("django_axe/", include("django_axe.urls")),
]
