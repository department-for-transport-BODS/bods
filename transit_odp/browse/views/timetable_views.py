import logging
from collections import namedtuple
from datetime import datetime, timedelta

from allauth.account.adapter import get_adapter
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import DetailView, FormView, TemplateView, UpdateView
from django.views.generic.detail import BaseDetailView, SingleObjectMixin
from django_hosts import reverse
from django_tables2 import SingleTableView

import config.hosts
from transit_odp.bods.interfaces.plugins import get_notifications
from transit_odp.browse.filters import TimetableSearchFilter
from transit_odp.browse.forms import UserFeedbackForm
from transit_odp.browse.views.base_views import BaseSearchView, BaseTemplateView
from transit_odp.common.downloaders import GTFSFileDownloader
from transit_odp.common.forms import ConfirmationForm
from transit_odp.common.services import get_gtfs_bucket_service
from transit_odp.common.view_mixins import (
    BaseDownloadFileView,
    BODSBaseView,
    DownloadView,
)
from transit_odp.data_quality.scoring import get_data_quality_rag
from transit_odp.organisation.constants import (
    DatasetType,
    FeedStatus,
    TimetableType,
    TravelineRegions,
)
from transit_odp.organisation.models import (
    Dataset,
    DatasetRevision,
    DatasetSubscription,
)
from transit_odp.pipelines.models import BulkDataArchive, ChangeDataArchive
from transit_odp.timetables.tables import TimetableChangelogTable
from transit_odp.users.constants import SiteAdminType

logger = logging.getLogger(__name__)
User = get_user_model()
Regions = namedtuple("Regions", ("region_code", "pretty_name_region_code", "exists"))


class DatasetDetailView(DetailView):
    template_name = "browse/timetables/dataset_detail/index.html"
    model = Dataset

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .get_active_org()
            .get_dataset_type(dataset_type=DatasetType.TIMETABLE.value)
            .get_published()
            .add_admin_area_names()
            .add_live_data()
            .add_nocs()
            .select_related("live_revision")
            .add_is_live_pti_compliant()
        )

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)

        dataset = self.object
        live_revision = dataset.live_revision
        report = live_revision.report.order_by("-created").first()
        user = self.request.user

        kwargs["report_id"] = report.id if report else None
        kwargs["api_root"] = reverse("api:app:api-root", host=config.hosts.DATA_HOST)
        kwargs["admin_areas"] = self.object.admin_area_names
        # Once all the reports are generated we should probably use the queryset
        # annotation get_live_dq_score and calculate the rag from that.
        kwargs["dq_score"] = get_data_quality_rag(report) if report else None

        # Handle errors produced by pipeline
        task = live_revision.etl_results.latest()
        error_code = task.error_code
        kwargs["error"] = bool(error_code)
        kwargs["show_pti"] = (
            live_revision.created.date() >= settings.PTI_START_DATE.date()
        )
        kwargs["pti_enforced_date"] = settings.PTI_ENFORCED_DATE
        kwargs["show_pti_link"] = not dataset.is_pti_compliant

        is_subscribed = None
        feed_api = None

        if user.is_authenticated:
            is_subscribed = DatasetSubscription.objects.filter(
                dataset=dataset, user=user
            ).exists()
            feed_api = reverse(
                "api:feed-detail", args=[self.object.id], host=config.hosts.DATA_HOST
            )
            feed_api = f"{feed_api}?api_key={user.auth_token}"

        kwargs.update({"notification": is_subscribed, "feed_api": feed_api})

        return kwargs


class DatasetSubscriptionBaseView(LoginRequiredMixin):
    model = Dataset

    def handle_no_permission(self):
        self.object = self.get_object()
        return render(
            self.request,
            "browse/timetables/feed_subscription_gatekeeper.html",
            context={"object": self.object, "backlink_url": self.get_cancel_url()},
        )

    def get_is_subscribed(self):
        # TODO - memoize
        user = self.request.user
        return user.subscriptions.filter(id=self.object.id).exists()


class DatasetSubscriptionView(DatasetSubscriptionBaseView, UpdateView):
    template_name = "browse/timetables/feed_subscription.html"
    form_class = ConfirmationForm

    def get_queryset(self):
        # Only allow users to subscribe to Datasets which are published
        return (
            super()
            .get_queryset()
            .get_active_org()
            .get_dataset_type(dataset_type=DatasetType.TIMETABLE.value)
            .get_published()
            .add_live_data()
        )

    def get_cancel_url(self):
        # Send user to feed-detail if can't get HTTP_REFERER
        # (more likely to have come from feed-detail because users
        # can only subscribe from that page)
        return self.request.META.get(
            "HTTP_REFERER",
            reverse("feed-detail", args=[self.object.id], host=self.request.host.name),
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
            "feed-subscription",
            args=[self.object.id],
            host=config.hosts.DATA_HOST,
        )

    def get_context_data(self, **kwargs):
        # the success page needs access to the user's origin url. Can't stash
        # in form_valid because at that point the
        # HTTP_REFERER is the current page
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
            "feed-subscription-success",
            args=[self.object.id],
            host=config.hosts.DATA_HOST,
        )
        return redirect(success_url)


class DatasetSubscriptionSuccessView(DatasetSubscriptionBaseView, DetailView):
    template_name = "browse/timetables/feed_subscription_success.html"

    def get_queryset(self):
        # Only allow users to subscribe to Datasets which are published
        return (
            super()
            .get_queryset()
            .get_active_org()
            .get_dataset_type(dataset_type=DatasetType.TIMETABLE.value)
            .get_published()
            .add_live_data()
        )

    def get_back_url(self):
        adapter = get_adapter(self.request)
        if adapter.stash_contains_back_url(self.request):
            return adapter.unstash_back_url(self.request)
        else:
            # Send user to feed-detail if can't retrieve URL (more likely to
            # have come from feed-detail because users
            # can only subscribe from that page)
            return reverse(
                "feed-detail", args=[self.object.id], host=self.request.host.name
            )

    def get_back_button_text(self, previous_url):
        if previous_url == reverse("users:feeds-manage", host=config.hosts.DATA_HOST):
            return _("Go back to manage subscriptions")
        else:
            return _("Go back to data set")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        back_url = self.get_back_url()
        context.update(
            {
                "subscribe": self.get_is_subscribed(),
                "back_url": back_url,
                "back_button_text": self.get_back_button_text(back_url),
            }
        )
        return context


class DatasetChangeLogView(BODSBaseView, SingleTableView):
    template_name = "browse/timetables/feed_change_log.html"
    model = DatasetRevision
    table_class = TimetableChangelogTable
    dataset: Dataset
    paginate_by = 10

    def get_dataset_queryset(self):
        return (
            Dataset.objects.get_active_org()
            .get_dataset_type(dataset_type=DatasetType.TIMETABLE.value)
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
        return context


class SearchView(BaseSearchView):
    template_name = "browse/timetables/search.html"
    model = Dataset
    paginate_by = 10
    filterset_class = TimetableSearchFilter
    strict = False

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .get_dataset_type(dataset_type=TimetableType)
            .get_published()
            .get_active_org()
            .add_organisation_name()
            .add_live_data()
            .add_admin_area_names()
            .add_is_live_pti_compliant()
            .order_by(*self.get_ordering())
        )

        keywords = self.request.GET.get("q", "").strip()
        if keywords:
            qs = qs.search(keywords)

        return qs


class DownloadTimetablesView(LoginRequiredMixin, BaseTemplateView):
    template_name = "browse/timetables/download_timetables.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        bulk_timetable = BulkDataArchive.objects.filter(dataset_type=TimetableType)
        context["show_bulk_archive_url"] = bulk_timetable.filter(
            compliant_archive=False
        ).exists()
        context["show_bulk_compliant_archive_url"] = bulk_timetable.filter(
            compliant_archive=True
        ).exists()
        list_traveline_regions = []
        for region_code, pretty_name_region_code in TravelineRegions.choices:
            list_traveline_regions.append(
                Regions(
                    region_code,
                    pretty_name_region_code,
                    bulk_timetable.filter(traveline_regions=region_code).exists(),
                )
            )

        context["show_bulk_traveline_regions"] = list_traveline_regions

        # Get the change archives from the last 7 days. There should be at most one per
        # day, but use LIMIT 7 anyway
        last_week = timezone.now() - timedelta(days=7)
        change_archives = ChangeDataArchive.objects.filter(published_at__gte=last_week)[
            :7
        ]
        context["change_archives"] = change_archives
        downloader = GTFSFileDownloader(get_gtfs_bucket_service)
        context["gtfs_static_files"] = downloader.get_files()

        return context


class DownloadRegionalGTFSFileView(BaseDownloadFileView):
    """View from downloading a GTFS file from S3 and returning it as FileResponse"""

    def get(self, request, *args, **kwargs):
        return self.render_to_response()

    def render_to_response(self):
        id_ = self.kwargs.get("id", None)
        gtfs = self.get_download_file(id_)
        if gtfs.file is None:
            raise Http404
        return FileResponse(gtfs.file, filename=gtfs.filename, as_attachment=True)

    def get_download_file(self, id_):
        downloader = GTFSFileDownloader(get_gtfs_bucket_service)
        gtfs = downloader.download_file_by_id(id_)
        return gtfs


class DownloadBulkDataArchiveView(DownloadView):
    def get_object(self, queryset=None):
        try:
            return BulkDataArchive.objects.filter(
                dataset_type=TimetableType,
                compliant_archive=False,
                traveline_regions="All",
            ).earliest()  # as objects are already ordered by '-created' in model Meta
        except BulkDataArchive.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": BulkDataArchive._meta.verbose_name}
            )

    def get_download_file(self):
        return self.object.data


class DownloadBulkDataArchiveRegionsView(DownloadView):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object(kwargs["region_code"])
        return self.render_to_response()

    def get_object(self, region_code: str = "All"):
        try:
            return BulkDataArchive.objects.filter(
                dataset_type=TimetableType,
                compliant_archive=False,
                traveline_regions=region_code,
            ).earliest()  # as objects are already ordered by '-created' in model Meta
        except BulkDataArchive.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": BulkDataArchive._meta.verbose_name}
            )

    def get_download_file(self, *args):
        return self.object.data


class DownloadCompliantBulkDataArchiveView(DownloadView):
    def get_object(self, queryset=None):
        try:
            return (
                BulkDataArchive.objects.filter(
                    dataset_type=TimetableType, compliant_archive=True
                )
                .order_by("-created")
                .first()
            )
        except BulkDataArchive.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": BulkDataArchive._meta.verbose_name}
            )

    def get_download_file(self):
        return self.object.data


class DownloadChangeDataArchiveView(DownloadView):
    slug_url_kwarg = "published_at"
    slug_field = "published_at"
    model = ChangeDataArchive

    def setup(self, request, *args, **kwargs):
        """Initialize attributes shared by all view methods."""
        published_at = kwargs.pop("published_at")

        try:
            # Try to parse published_at into a date object
            published_at = datetime.strptime(published_at, "%Y-%m-%d").date()
        except ValueError as e:
            raise Http404 from e

        super().setup(request, *args, published_at=published_at, **kwargs)

    def get_queryset(self):
        # Get the change archives from the last 7 days.
        last_week = timezone.now() - timedelta(days=7)
        return ChangeDataArchive.objects.filter(published_at__gte=last_week)

    def get_download_file(self):
        return self.object.data


class DatasetDownloadView(BaseDetailView):
    dataset_type = DatasetType.TIMETABLE.value

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


class UserFeedbackView(LoginRequiredMixin, SingleObjectMixin, FormView):
    template_name = "browse/timetables/user_feedback.html"
    form_class = UserFeedbackForm
    model = Dataset
    dataset_type = DatasetType.TIMETABLE.value

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        qs = (
            Dataset.objects.get_active_org()
            .get_dataset_type(dataset_type=self.dataset_type)
            .get_published()
            .add_live_data()
        )
        return qs

    def form_valid(self, form):
        client = get_notifications()
        data = form.cleaned_data
        dataset = self.object
        feedback = data["feedback"]
        developer_email = None if data["anonymous"] else self.request.user.email
        admins = User.objects.filter(account_type=SiteAdminType)
        emails = [email["email"] for email in admins.values()]
        emails.append(self.request.user.email)

        for email in emails:
            client.send_dataset_feedback_consumer_copy(
                dataset_id=dataset.id,
                contact_email=email,
                dataset_name=dataset.live_revision.name,
                publisher_name=dataset.organisation.name,
                feedback=feedback,
                time_now=None,
            )

        client.send_feedback_notification(
            dataset_id=dataset.id,
            contact_email=dataset.contact.email,
            dataset_name=dataset.live_revision.name,
            feedback=feedback,
            feed_detail_link=dataset.feed_detail_url,
            developer_email=developer_email,
        )

        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "feed-feedback-success", args=[self.object.id], host=config.hosts.DATA_HOST
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_url"] = reverse(
            "feed-detail",
            args=[self.object.id],
            host=config.hosts.DATA_HOST,
        )
        return context


class UserFeedbackSuccessView(LoginRequiredMixin, TemplateView):
    template_name = "browse/timetables/user_feedback_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        object_id = self.kwargs["pk"]
        url = reverse("feed-detail", args=[object_id], host=config.hosts.DATA_HOST)
        context["back_link"] = url
        return context
