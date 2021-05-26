from django.urls import path

from transit_odp.site_admin.views import AgentDetailView, AgentListView

paths = [
    path(
        "",
        view=AgentListView.as_view(),
        name="agent-list",
    ),
    path(
        "<int:pk>/",
        view=AgentDetailView.as_view(),
        name="agent-detail",
    ),
]
