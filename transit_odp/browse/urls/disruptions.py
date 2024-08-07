from django.urls import include, path

from transit_odp.browse.views.disruptions_views import (
    DisruptionDetailView,
    DisruptionOrganisationDetailView,
    DisruptionsDataView,
    DownloadDisruptionsDataArchiveView,
    DownloadDisruptionsView,
)

urlpatterns = [
    path(
        "download/",
        include(
            [
                path(
                    "",
                    view=DownloadDisruptionsView.as_view(),
                    name="download-disruptions",
                ),
                path(
                    "bulk_archive",
                    view=DownloadDisruptionsDataArchiveView.as_view(),
                    name="downloads-disruptions-bulk",
                ),
            ]
        ),
    ),
    path(
        "organisations/",
        include(
            [
                path(
                    "",
                    view=DisruptionsDataView.as_view(),
                    name="disruptions-data",
                ),
                path(
                    "<uuid:orgId>/",
                    include(
                        [
                            path(
                                "",
                                view=DisruptionOrganisationDetailView.as_view(),
                                name="org-detail",
                            ),
                            path(
                                "disruption-detail/<uuid:disruptionId>/",
                                view=DisruptionDetailView.as_view(),
                                name="disruption-detail",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
]
