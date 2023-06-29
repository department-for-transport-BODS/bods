import logging

from allauth.account.adapter import get_adapter
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.views.generic import DetailView, TemplateView, UpdateView
from django.views.generic.detail import BaseDetailView
from django_hosts import reverse

import config.hosts
from transit_odp.browse.filters import FaresSearchFilter
from transit_odp.browse.tables import DatasetPaginatorTable
from transit_odp.browse.views.base_views import (
    BaseSearchView,
    BaseTemplateView,
    ChangeLogView,
)
from transit_odp.browse.views.timetable_views import (
    DatasetSubscriptionBaseView,
    UserFeedbackView,
)
from transit_odp.common.forms import ConfirmationForm
from transit_odp.common.view_mixins import DownloadView, ResourceCounterMixin
from transit_odp.fares_validator.models import FaresValidationResult
from transit_odp.organisation.constants import (
    EXPIRED,
    INACTIVE,
    LIVE,
    DatasetType,
    FaresType,
    FeedStatus,
)
from transit_odp.organisation.models import (
    Dataset,
    DatasetRevision,
    DatasetSubscription,
)
from transit_odp.pipelines.models import BulkDataArchive
from transit_odp.publish.tables import DatasetRevisionTable

logger = logging.getLogger(__name__)


class DownloadFaresView(LoginRequiredMixin, BaseTemplateView):
    template_name = "browse/fares/download_fares.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add link to most recent bulk data archive
        context["show_bulk_archive_url"] = BulkDataArchive.objects.filter(
            dataset_type=DatasetType.FARES.value
        ).exists()

        return context


class DownloadFaresBulkDataArchiveView(ResourceCounterMixin, DownloadView):
    def get_object(self, queryset=None):
        try:
            return BulkDataArchive.objects.filter(
                dataset_type=DatasetType.FARES.value
            ).earliest()  # as objects are already ordered by '-created' in model Meta
        except BulkDataArchive.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": BulkDataArchive._meta.verbose_name}
            )

    def get_download_file(self):
        return self.object.data


class FaresSearchView(BaseSearchView):
    template_name = "browse/fares/search.html"
    model = Dataset
    paginate_by = 10
    filterset_class = FaresSearchFilter
    strict = False

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .get_dataset_type(dataset_type=FaresType)
            .get_published()
            .get_viewable_statuses()
            .get_active_org()
            .add_organisation_name()
            .add_live_data()
            .get_compliant_fares_validation()
            .order_by(*self.get_ordering())
        )

        keywords = self.request.GET.get("q", "").strip()
        if keywords:
            qs = qs.search(keywords)
        return qs


class FaresDatasetDetailView(DetailView):
    template_name = "browse/fares/feed_detail/index.html"
    model = Dataset

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .get_active_org()
            .get_dataset_type(dataset_type=DatasetType.FARES.value)
            .get_published()
            .add_live_data()
            .select_related("live_revision")
        )

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)

        dataset = self.object
        user = self.request.user
        last_modified_username = None
        if dataset.last_modified_user is not None:
            last_modified_username = dataset.live_revision.last_modified_user.username
        kwargs["api_root"] = reverse("api:app:api-root", host=config.hosts.DATA_HOST)
        kwargs["metadata"] = dataset.live_revision.metadata.faresmetadata
        kwargs["download_link"] = reverse(
            "fares-feed-download", args=[dataset.id], host=config.hosts.DATA_HOST
        )
        kwargs["last_modified_username"] = last_modified_username
        kwargs["show_map"] = dataset.status in (EXPIRED, INACTIVE, LIVE)

        kwargs["pk1"] = dataset.organisation_id
        kwargs["pk2"] = dataset.live_revision_id

        kwargs["is_compliant_error"] = True
        kwargs["show_report_link"] = False
        try:
            results = FaresValidationResult.objects.get(
                revision_id=dataset.live_revision_id
            )
        except FaresValidationResult.DoesNotExist:
            results = None
        if results:
            if results.is_compliant is True:
                kwargs["is_compliant_error"] = False
            kwargs["show_report_link"] = True
        is_subscribed = None
        feed_api = None

        if user.is_authenticated:
            is_subscribed = DatasetSubscription.objects.filter(
                dataset=dataset, user=user
            ).exists()
            feed_api = reverse(
                "api:fares-api-detail",
                args=[self.object.id],
                host=config.hosts.DATA_HOST,
            )
            feed_api = f"{feed_api}?api_key={user.auth_token}"

        kwargs.update({"notification": is_subscribed, "feed_api": feed_api})

        return kwargs


class FaresChangeLogView(ChangeLogView):
    template_name = "browse/fares/feed_change_log.html"
    table_class = DatasetRevisionTable
    dataset_type = DatasetType.FARES.value


class FaresSubscriptionView(DatasetSubscriptionBaseView, UpdateView):
    template_name = "browse/timetables/feed_subscription.html"
    form_class = ConfirmationForm

    def get_queryset(self):
        # Only allow users to subscribe to Datasets which are published
        return (
            super()
            .get_queryset()
            .get_active_org()
            .get_dataset_type(dataset_type=DatasetType.FARES.value)
            .get_published()
            .add_live_data()
        )

    def get_cancel_url(self):
        # Send user to feed-detail if can't get HTTP_REFERER (more likely to
        # have come from feed-detail because users can only subscribe from that page)
        return self.request.META.get(
            "HTTP_REFERER",
            reverse(
                "fares-feed-detail", args=[self.object.id], host=self.request.host.name
            ),
        )

    def stash_data(self):
        adapter = get_adapter(self.request)
        adapter.stash_back_url(self.request, self.get_cancel_url())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # pop model instance as form is not a ModelForm
        kwargs.pop("instance", None)
        kwargs.update({"cancel_url": self.get_cancel_url()})
        return kwargs

    def get_form_url(self):
        return reverse(
            "fares-feed-subscription",
            args=[self.object.id],
            host=config.hosts.DATA_HOST,
        )

    def get_context_data(self, **kwargs):
        # the success page needs access to the user's origin url. Can't stash in
        # form_valid because at that point the HTTP_REFERER is the current page
        self.stash_data()
        # set is_subscribed before calling super().get_context_data
        # so that it is available in subsequent call to get_form_kwargs
        self.is_subscribed = self.get_is_subscribed()

        context = super().get_context_data(**kwargs)
        context["is_subscribed"] = self.is_subscribed
        context["backlink_url"] = self.get_cancel_url()
        context["form_url"] = self.get_form_url()
        return context

    def form_valid(self, form):
        user = self.request.user
        is_subscribed = self.get_is_subscribed()

        # Toggle subscription
        if is_subscribed:
            DatasetSubscription.objects.filter(dataset=self.object, user=user).delete()
        else:
            DatasetSubscription.objects.create(user=user, dataset=self.object)

        success_url = reverse(
            "fares-feed-subscription-success",
            args=[self.object.id],
            host=config.hosts.DATA_HOST,
        )
        return redirect(success_url)


class FaresSubscriptionSuccessView(
    DatasetPaginatorTable, DatasetSubscriptionBaseView, DetailView
):
    template_name = "browse/timetables/feed_subscription_success.html"

    def get_queryset(self):
        # Only allow users to subscribe to Datasets which are published
        return (
            super()
            .get_queryset()
            .get_active_org()
            .get_dataset_type(dataset_type=DatasetType.FARES.value)
            .get_published()
            .add_live_data()
        )

    def get_back_url(self):
        adapter = get_adapter(self.request)
        if adapter.stash_contains_back_url(self.request):
            return adapter.unstash_back_url(self.request)
        else:
            # Send user to feed-detail if can't retrieve URL (more likely to have come
            # from feed-detail because users can only subscribe from that page)
            return reverse(
                "fares-feed-detail", args=[self.object.id], host=self.request.host.name
            )

    def get_back_button_text(self, previous_url):
        sub_manage_url = reverse("users:feeds-manage", host=config.hosts.DATA_HOST)
        if sub_manage_url in previous_url:
            return _("Go back to manage subscriptions")
        else:
            return _("Go back to data set")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        back_url = self._get_or_update_url(self.request.user, self.get_back_url())
        context.update(
            {
                "subscribe": self.get_is_subscribed(),
                "back_url": back_url,
                "back_button_text": self.get_back_button_text(back_url),
            }
        )
        return context


class FaresDatasetDownloadView(ResourceCounterMixin, BaseDetailView):
    dataset_type = DatasetType.FARES.value

    def get_queryset(self):
        if self.request.GET.get("is_review", None) == "true":
            return Dataset.objects.get_active_org()
        else:
            return (
                Dataset.objects.get_active_org()
                .get_dataset_type(dataset_type=self.dataset_type)
                .get_published()
                .select_related("live_revision")
            )

    def render_to_response(self, context, **response_kwargs):
        dataset = self.object
        if dataset:
            if self.request.GET.get("is_review", None) == "true":
                revision = dataset.revisions.latest()
            else:
                revision = dataset.live_revision

            if (
                self.request.GET.get("get_working", None) == "true"
                and revision.status == FeedStatus.error.value
            ):
                # get previous working revision
                revision = dataset.revisions.filter(
                    status=FeedStatus.live.value
                ).latest()

            if revision:
                return FileResponse(revision.upload_file.open("rb"), as_attachment=True)
            else:
                raise Http404(
                    _("No %(verbose_name)s found matching the query")
                    % {"verbose_name": DatasetRevision._meta.verbose_name}
                )


class FaresUserFeedbackView(UserFeedbackView):
    dataset_type = DatasetType.FARES.value

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_url"] = reverse(
            "fares-feed-detail",
            args=[self.dataset.id],
            host=config.hosts.DATA_HOST,
        )
        return context

    def get_success_url(self):
        return reverse(
            "fares-feed-feedback-success",
            args=[self.dataset.id],
            host=config.hosts.DATA_HOST,
        )


class FaresUserFeedbackSuccessView(LoginRequiredMixin, TemplateView):
    template_name = "browse/timetables/user_feedback_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        object_id = self.kwargs["pk"]
        url = reverse(
            "fares-feed-detail", args=[object_id], host=config.hosts.DATA_HOST
        )
        context["back_link"] = url
        return context
