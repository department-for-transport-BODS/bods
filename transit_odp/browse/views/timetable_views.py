import logging
from collections import namedtuple
from datetime import datetime, timedelta

from allauth.account.adapter import get_adapter
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Max
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView
from django.views.generic.detail import BaseDetailView
from django_hosts import reverse

import config.hosts
from transit_odp.browse.constants import LICENCE_NUMBER_NOT_SUPPLIED_MESSAGE
from transit_odp.browse.filters import TimetableSearchFilter
from transit_odp.browse.forms import ConsumerFeedbackForm
from transit_odp.browse.tables import DatasetPaginatorTable
from transit_odp.browse.views.base_views import (
    BaseSearchView,
    BaseTemplateView,
    ChangeLogView,
)
from transit_odp.common.downloaders import GTFSFileDownloader
from transit_odp.common.forms import ConfirmationForm
from transit_odp.common.services import get_gtfs_bucket_service
from transit_odp.common.view_mixins import (
    BaseDownloadFileView,
    DownloadView,
    ResourceCounterMixin,
)
from transit_odp.data_quality.scoring import get_data_quality_rag
from transit_odp.notifications import get_notifications
from transit_odp.organisation.constants import (
    DatasetType,
    FeedStatus,
    TimetableType,
    TravelineRegions,
)
from transit_odp.organisation.models import (
    ConsumerFeedback,
    Dataset,
    DatasetRevision,
    DatasetSubscription,
    TXCFileAttributes,
)
from transit_odp.pipelines.models import BulkDataArchive, ChangeDataArchive
from transit_odp.site_admin.models import ResourceRequestCounter
from transit_odp.timetables.tables import TimetableChangelogTable
from transit_odp.transmodel.models import BookingArrangements, Service
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
            .get_dataset_type(dataset_type=TimetableType)
            .get_published()
            .get_viewable_statuses()
            .add_admin_area_names()
            .add_live_data()
            .add_nocs()
            .select_related("live_revision")
            .add_is_live_pti_compliant()
        )

    def get_distinct_dataset_txc_attributes(self, revision_id):
        txc_attributes = {}
        txc_file_attributes = TXCFileAttributes.objects.filter(revision_id=revision_id)

        for file_attribute in txc_file_attributes:
            licence_number = (
                file_attribute.licence_number
                and file_attribute.licence_number.strip()
                or LICENCE_NUMBER_NOT_SUPPLIED_MESSAGE
            )

            noc_dict = txc_attributes.setdefault(licence_number, {}).setdefault(
                file_attribute.national_operator_code, {}
            )
            for line_name in file_attribute.line_names:
                line_names_dict = noc_dict.setdefault(line_name, set())
                line_names_dict.add(file_attribute.service_code)

        return txc_attributes

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)

        dataset = self.object
        live_revision = dataset.live_revision
        report = live_revision.report.order_by("-created").first()
        summary = getattr(report, "summary", None)
        user = self.request.user

        kwargs["pk"] = dataset.id
        kwargs["api_root"] = reverse("api:app:api-root", host=config.hosts.DATA_HOST)
        kwargs["admin_areas"] = self.object.admin_area_names
        # Once all the reports are generated we should probably use the queryset
        # annotation get_live_dq_score and calculate the rag from that.
        kwargs["report_id"] = getattr(report, "id", None)
        kwargs["dq_score"] = (
            get_data_quality_rag(report) if report and summary else None
        )

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
        kwargs["distinct_attributes"] = self.get_distinct_dataset_txc_attributes(
            live_revision.id
        )

        return kwargs


class LineMetadataDetailView(DetailView):
    template_name = "browse/timetables/dataset_detail/review_line_metadata.html"
    model = Dataset

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .get_active_org()
            .get_dataset_type(dataset_type=TimetableType)
            .get_published()
            .get_viewable_statuses()
            .add_admin_area_names()
            .add_live_data()
            .add_nocs()
            .select_related("live_revision")
            .add_is_live_pti_compliant()
        )

    def get_service_type(self, revision_id, service_code, line_name) -> str:
        all_service_types_list = []
        service_types_qs = (
            Service.objects.filter(
                revision=revision_id,
                service_code=service_code,
                name=line_name,
            )
            .values_list("service_type", flat=True)
            .distinct()
        )
        for service_type in service_types_qs:
            all_service_types_list.append(service_type)

        if all(service_type == "standard" for service_type in all_service_types_list):
            return "Standard"
        elif all(service_type == "flexible" for service_type in all_service_types_list):
            return "Flexible"
        return "Flexible/Standard"

    def get_current_files(self, revision_id, service_code, line_name) -> list:
        valid_file_names = []
        today = datetime.now().date()

        highest_revision_number = TXCFileAttributes.objects.filter(
            revision=revision_id,
            service_code=service_code,
            line_names__contains=[line_name],
        ).aggregate(highest_revision_number=Max("revision_number"))[
            "highest_revision_number"
        ]

        file_name_qs = TXCFileAttributes.objects.filter(
            revision=revision_id,
            service_code=service_code,
            line_names__contains=[line_name],
            revision_number=highest_revision_number,
        ).values_list(
            "filename",
            "operating_period_start_date",
            "operating_period_end_date",
        )

        for file_name in file_name_qs:
            operating_period_start_date = file_name[1]
            operating_period_end_date = file_name[2]

            if operating_period_start_date and operating_period_end_date:
                if (
                    operating_period_start_date <= today
                    and today <= operating_period_end_date
                ):
                    valid_file_names.append(
                        {
                            "filename": file_name[0],
                            "start_date": operating_period_start_date,
                            "end_date": operating_period_end_date,
                        }
                    )
            elif operating_period_start_date:
                if operating_period_start_date <= today:
                    valid_file_names.append(
                        {
                            "filename": file_name[0],
                            "start_date": operating_period_start_date,
                            "end_date": None,
                        }
                    )
            elif operating_period_end_date:
                if today <= operating_period_end_date:
                    valid_file_names.append(
                        {
                            "filename": file_name[0],
                            "start_date": None,
                            "end_date": operating_period_end_date,
                        }
                    )

        return valid_file_names

    def get_most_recent_modification_datetime(
        self, revision_id, service_code, line_name
    ):
        return TXCFileAttributes.objects.filter(
            revision_id=revision_id,
            service_code=service_code,
            line_names__contains=[line_name],
        ).aggregate(max_modification_datetime=Max("modification_datetime"))[
            "max_modification_datetime"
        ]

    def get_lastest_operating_period_start_date(
        self, revision_id, service_code, line_name, recent_modification_datetime
    ):
        return TXCFileAttributes.objects.filter(
            revision_id=revision_id,
            service_code=service_code,
            line_names__contains=[line_name],
            modification_datetime=recent_modification_datetime,
        ).aggregate(max_start_date=Max("operating_period_start_date"))["max_start_date"]

    def get_single_booking_arrangements_file(self, revision_id, service_code):
        """
        Add docstring + return type
        """
        try:
            service_ids = (
                Service.objects.filter(revision=revision_id)
                .filter(service_code=service_code)
                .values_list("id", flat=True)
            )
        except Service.DoesNotExist:
            return None
        return (
            BookingArrangements.objects.filter(service_id__in=service_ids)
            .values_list("description", "email", "phone_number", "web_address")
            .distinct()
        )

    def get_valid_files(self, revision_id, valid_files, service_code, line_name):
        if len(valid_files) == 1:
            return self.get_single_booking_arrangements_file(revision_id, service_code)
        elif len(valid_files) > 1:
            booking_arrangements_qs = None
            most_recent_modification_datetime = (
                self.get_most_recent_modification_datetime(
                    revision_id, service_code, line_name
                )
            )
            booking_arrangements_qs = TXCFileAttributes.objects.filter(
                revision_id=revision_id,
                service_code=service_code,
                line_names__contains=[line_name],
                modification_datetime=most_recent_modification_datetime,
            )

            if len(booking_arrangements_qs) == 1:
                return self.get_single_booking_arrangements_file(
                    booking_arrangements_qs.first().revision_id, [service_code]
                )

            lastest_operating_period_start = (
                self.get_lastest_operating_period_start_date(
                    revision_id,
                    service_code,
                    line_name,
                    most_recent_modification_datetime,
                )
            )
            booking_arrangements_qs = booking_arrangements_qs.filter(
                operating_period_start_date=lastest_operating_period_start
            )

            if len(booking_arrangements_qs) == 1:
                return self.get_single_booking_arrangements_file(
                    booking_arrangements_qs.first().revision_id, [service_code]
                )

            booking_arrangements_qs = booking_arrangements_qs.order_by(
                "-filename"
            ).first()

            return self.get_single_booking_arrangements_file(
                booking_arrangements_qs.revision_id, [service_code]
            )

    def get_context_data(self, **kwargs):
        """
        Get the context data for the view.

        This method retrieves various contextual data based on the request parameters
        and the object's attributes.
        """
        line = self.request.GET.get("line")
        service_code = self.request.GET.get("service")
        kwargs = super().get_context_data(**kwargs)

        dataset = self.object
        live_revision = dataset.live_revision
        kwargs["pk"] = dataset.id

        kwargs["line_name"] = line
        kwargs["service_code"] = service_code
        kwargs["service_type"] = self.get_service_type(
            live_revision.id, kwargs["service_code"], kwargs["line_name"]
        )
        kwargs["current_valid_files"] = self.get_current_files(
            live_revision.id, kwargs["service_code"], kwargs["line_name"]
        )
        kwargs["api_root"] = reverse("api:app:api-root", host=config.hosts.DATA_HOST)

        if (
            kwargs["service_type"] == "Flexible"
            or kwargs["service_type"] == "Flexible/Standard"
        ):
            booking_arrangements_info = self.get_valid_files(
                live_revision.id,
                kwargs["current_valid_files"],
                kwargs["service_code"],
                kwargs["line_name"],
            )
            if booking_arrangements_info:
                kwargs["booking_arrangements"] = booking_arrangements_info[0][0]
                kwargs["booking_methods"] = booking_arrangements_info[0][1:]

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
        return self.request.headers.get(
            "Referer",
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


class DatasetSubscriptionSuccessView(
    DatasetPaginatorTable, DatasetSubscriptionBaseView, DetailView
):
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


class DatasetChangeLogView(ChangeLogView):
    template_name = "browse/timetables/feed_change_log.html"
    table_class = TimetableChangelogTable
    dataset_type = DatasetType.TIMETABLE.value


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
            .get_viewable_statuses()
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
        if self.kwargs.get("id") == TravelineRegions.ALL.lower():
            db_starttime = datetime.now()
            ResourceRequestCounter.from_request(request)
            db_endtime = datetime.now()
            logger.info(
                f"Database call for GTFS ResourceRequestCounter took {(db_endtime-db_starttime).total_seconds()} seconds"
            )
        return self.render_to_response()

    def render_to_response(self):
        id_ = self.kwargs.get("id", None)
        gtfs = self.get_download_file(id_)
        if gtfs.file is None:
            raise Http404
        return FileResponse(gtfs.file, filename=gtfs.filename, as_attachment=True)

    def get_download_file(self, id_):
        s3_start = datetime.now()
        downloader = GTFSFileDownloader(get_gtfs_bucket_service)
        gtfs = downloader.download_file_by_id(id_)
        s3_endtime = datetime.now()
        logger.info(
            f"S3 bucket download for GTFS took {(s3_endtime-s3_start).total_seconds()} seconds"
        )
        return gtfs


class DownloadBulkDataArchiveView(ResourceCounterMixin, DownloadView):
    def get_object(self, queryset=None):
        db_starttime = datetime.now()
        try:
            bulk_data_archive = BulkDataArchive.objects.filter(
                dataset_type=TimetableType,
                compliant_archive=False,
                traveline_regions="All",
            ).earliest()  # as objects are already ordered by '-created' in model Meta
            db_endtime = datetime.now()
            logger.info(
                f"Database call for bulk archive took {(db_endtime-db_starttime).total_seconds()} seconds"
            )
            return bulk_data_archive
        except BulkDataArchive.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": BulkDataArchive._meta.verbose_name}
            )

    def get_download_file(self):
        s3_start = datetime.now()
        data = self.object.data
        s3_endtime = datetime.now()
        logger.info(
            f"S3 bucket download for bulk archive took {(s3_endtime-s3_start).total_seconds()} seconds"
        )
        return data


class DownloadBulkDataArchiveRegionsView(DownloadView):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object(kwargs["region_code"])
        return self.render_to_response()

    def get_object(self, region_code: str = "All"):
        db_starttime = datetime.now()
        try:
            region_bulk_data_archive = BulkDataArchive.objects.filter(
                dataset_type=TimetableType,
                compliant_archive=False,
                traveline_regions=region_code,
            ).earliest()  # as objects are already ordered by '-created' in model Meta
            db_endtime = datetime.now()
            logger.info(
                f"Database call for region-wise bulk archive took {(db_endtime-db_starttime).total_seconds()} seconds"
            )
            return region_bulk_data_archive
        except BulkDataArchive.DoesNotExist:
            raise Http404(
                _("No %(verbose_name)s found matching the query")
                % {"verbose_name": BulkDataArchive._meta.verbose_name}
            )

    def get_download_file(self, *args):
        s3_start = datetime.now()
        data = self.object.data
        s3_endtime = datetime.now()
        logger.info(
            f"S3 bucket download for region-wise bulk archive took {(s3_endtime-s3_start).total_seconds()} seconds"
        )
        return data


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


class DatasetDownloadView(ResourceCounterMixin, BaseDetailView):
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


class UserFeedbackView(LoginRequiredMixin, CreateView):
    template_name = "browse/timetables/user_feedback.html"
    form_class = ConsumerFeedbackForm
    model = ConsumerFeedback
    dataset = None

    def get(self, request, *args, **kwargs):
        self.dataset = get_object_or_404(
            Dataset.objects.select_related("live_revision", "organisation"),
            id=self.kwargs.get("pk"),
        )
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.dataset = get_object_or_404(
            Dataset.objects.select_related("live_revision"), id=self.kwargs.get("pk")
        )
        return super().post(request, *args, **kwargs)

    def get_initial(self):
        return {
            "dataset_id": self.dataset.id,
            "organisation_id": self.dataset.organisation.id,
            "consumer_id": self.request.user.id,
        }

    @transaction.atomic
    def form_valid(self, form):
        client = get_notifications()
        response = super().form_valid(form)
        admins = User.objects.filter(account_type=SiteAdminType)
        emails = [email["email"] for email in admins.values()]
        emails.append(self.request.user.email)

        for email in emails:
            client.send_dataset_feedback_consumer_copy(
                dataset_id=self.dataset.id,
                contact_email=email,
                dataset_name=self.dataset.live_revision.name,
                publisher_name=self.dataset.organisation.name,
                feedback=self.object.feedback,
                time_now=None,
            )

        client.send_feedback_notification(
            dataset_id=self.dataset.id,
            contact_email=self.dataset.contact.email,
            dataset_name=self.dataset.live_revision.name,
            feedback=self.object.feedback,
            feed_detail_link=self.dataset.feed_detail_url,
            developer_email=self.request.user.email if self.object.consumer else None,
        )

        return response

    def get_success_url(self):
        return reverse(
            "feed-feedback-success",
            args=[self.dataset.id],
            host=config.hosts.DATA_HOST,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["back_url"] = reverse(
            "feed-detail",
            args=[self.dataset.id],
            host=config.hosts.DATA_HOST,
        )
        context["dataset"] = self.dataset
        return context


class UserFeedbackSuccessView(LoginRequiredMixin, TemplateView):
    template_name = "browse/timetables/user_feedback_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        object_id = self.kwargs["pk"]
        url = reverse("feed-detail", args=[object_id], host=config.hosts.DATA_HOST)
        context["back_link"] = url
        return context
