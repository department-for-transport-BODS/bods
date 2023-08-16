from django.urls import path
from transit_odp.browse.views.disruptions_views import DownloadDisruptionsView

urlpatterns = [
    path(
        "download/", view=DownloadDisruptionsView.as_view(), name="download-disruptions"
    )
]
