from django.views.generic import ListView, TemplateView
from django_filters.views import FilterView

from transit_odp.common.view_mixins import BODSBaseView


class BaseFilterView(BODSBaseView, FilterView):
    pass


class BaseTemplateView(BODSBaseView, TemplateView):
    pass


class BaseListView(BODSBaseView, ListView):
    pass


class BrowseHomeView(BaseTemplateView):
    template_name = "browse/home.html"


class SearchSelectView(BaseTemplateView):
    template_name = "browse/search_select.html"


class DownloadsView(BaseTemplateView):
    template_name = "browse/downloads.html"


class ApiSelectView(BaseTemplateView):
    template_name = "browse/api_select.html"


class DownloadDataCatalogueView(BaseTemplateView):
    template_name = "browse/download_catalogue.html"
