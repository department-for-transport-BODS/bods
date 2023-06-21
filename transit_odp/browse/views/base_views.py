from datetime import datetime

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import ChoiceField
from django.http import Http404
from django.utils.translation import gettext as _
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import CreateView
from django_filters.constants import EMPTY_VALUES
from django_filters.views import FilterView
from django_hosts import reverse
from django_tables2 import SingleTableView

from transit_odp.common.view_mixins import BODSBaseView
from transit_odp.feedback.forms import GlobalFeedbackForm
from transit_odp.feedback.models import Feedback
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models.data import Dataset, DatasetRevision


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pti_pdf_url"] = settings.PTI_PDF_URL
        return context


class DownloadsView(BaseTemplateView):
    template_name = "browse/downloads.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pti_pdf_url"] = settings.PTI_PDF_URL
        return context


class ApiSelectView(LoginRequiredMixin, BaseTemplateView):
    template_name = "browse/api_select.html"


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
        kwargs["ordering"] = self.request.GET.get("ordering", "-published_at")
        return kwargs


class GlobalFeedbackView(CreateView):
    template_name = "pages/feedback.html"
    form_class = GlobalFeedbackForm
    model = Feedback

    def get_success_url(self):
        return reverse(
            "global-feedback-success",
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["url"] = self.request.GET.get("url", "")
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["hide_global_feedback"] = True
        return context


class GlobalFeedbackThankYouView(TemplateView):
    template_name = "pages/thank_you_page.html"


class ChangeLogView(BODSBaseView, SingleTableView):
    model = DatasetRevision
    paginate_by = 10

    dataset_type: DatasetType

    def get_dataset_queryset(self):
        return (
            Dataset.objects.get_active_org()
            .get_dataset_type(dataset_type=self.dataset_type)
            .add_live_data()
        )

    def get_dataset(self):
        try:
            related_pk = self.kwargs["pk"]
            self.dataset = self.get_dataset_queryset().get(id=related_pk)
            return self.dataset
        except Dataset.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": Dataset._meta.verbose_name}
            )

    def get_queryset(self):
        self.dataset = self.get_dataset()
        return (
            super()
            .get_queryset()
            .filter(dataset=self.dataset)
            .get_published()
            .add_publisher_email()
            .order_by("-created")
        )

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context["object"] = self.dataset
        context["feed"] = self.dataset
        context["dataset_type"] = self.dataset.dataset_type
        return context


class OrgChangeLogView(ChangeLogView):
    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        context["pk1"] = self.kwargs["pk1"]
        return context

    def get_dataset_queryset(self):
        return (
            super().get_dataset_queryset().filter(organisation_id=self.organisation.id)
        )
