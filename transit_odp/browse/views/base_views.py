from datetime import datetime

from django.forms import ChoiceField
from django.views.generic import ListView, TemplateView
from django_filters.constants import EMPTY_VALUES
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


class BaseSearchView(BaseFilterView):
    def translate_query_params(self):
        """
        Translates query params into something more human
        readable for use in the frontend
        :return: dict[str, str] of query params
        """
        form = self.filterset.form
        translated_query_params = {}
        for key, value in form.cleaned_data.items():
            if value in EMPTY_VALUES:
                continue

            if isinstance(value, datetime):
                value = value.strftime("%d/%m/%y")

            name_func = getattr(form.fields[key], "label_from_instance", str)
            value = name_func(value)

            if isinstance(form.fields[key], ChoiceField):
                choice_dict = {}
                for model, choice in form.fields[key].choices:
                    if hasattr(model, "value"):
                        choice_dict[model.value] = choice
                    elif isinstance(model, str):
                        choice_dict[model] = choice
                if value in choice_dict:
                    value = choice_dict[value]

            translated_query_params[key] = value
        return translated_query_params

    def get_queryset(self):
        return self.model.objects.all()

    def get_ordering(self):
        ordering = self.request.GET.get("ordering", "-published_at")
        if isinstance(ordering, str):
            ordering = (ordering,)
        return ordering

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        if not self.request.GET:
            return kwargs

        kwargs["query_params"] = self.translate_query_params()
        kwargs["q"] = self.request.GET.get("q", "")
        kwargs["ordering"] = self.request.GET.get("ordering", "name")
        return kwargs
