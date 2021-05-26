from django.urls import include, path

from transit_odp.site_admin.views import (
    ConsumerDetailView,
    ConsumerListView,
    RevokeConsumerSuccessView,
    RevokeConsumerView,
    UpdateConsumerNotesView,
)

paths = [
    path("", ConsumerListView.as_view(), name="consumer-list"),
    path(
        "<int:pk>/",
        include(
            [
                path(
                    "",
                    ConsumerDetailView.as_view(),
                    name="consumer-detail",
                ),
                path(
                    "revoke/",
                    RevokeConsumerView.as_view(),
                    name="revoke-consumer",
                ),
                path(
                    "revoke/success/",
                    RevokeConsumerSuccessView.as_view(),
                    name="revoke-consumer-success",
                ),
                path(
                    "notes/edit/",
                    UpdateConsumerNotesView.as_view(),
                    name="edit-consumer-notes",
                ),
            ]
        ),
    ),
]
