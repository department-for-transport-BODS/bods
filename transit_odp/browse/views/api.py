"""JSON APIs backing the Next.js dataset sub-pages on the data host.

Mirrors, for timetable, AVL and fares datasets:

* ``DatasetChangeLogView`` & co. (``feed-changelog``)
* ``DatasetSubscriptionView`` & co. (``feed-subscription`` and its success page)
* ``UserFeedbackView`` & co. (``feed-feedback`` and its success page)

The Django views stay the source of truth: querysets, forms, notifications and the
back-url stash are all reused rather than copied. Only the response shape differs.
"""

from dataclasses import dataclass
from datetime import timedelta
from typing import Optional, Type
from urllib.parse import urlparse

import pytz
from allauth.account.adapter import get_adapter
from django.conf import settings
from django.contrib.auth import get_user
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.views.decorators.http import require_GET, require_http_methods
from django_hosts import reverse

import config.hosts
from transit_odp.browse.forms import ConsumerFeedbackForm
from transit_odp.browse.views import avl_views, fares_views, timetable_views
from transit_odp.common.forms import ConfirmationForm
from transit_odp.common.templatetags.filters import percentage
from transit_odp.data_quality.scoring import get_data_quality_rag
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models import DatasetSubscription
from transit_odp.organisation.models.data import Dataset
from transit_odp.pipelines.models import DataQualityTask
from transit_odp.users.views.api import (
    _form_field_errors,
    _json_body,
    _subscription_status_display,
)

AUTH_REQUIRED_ERROR = "Authentication required"
DATASET_NOT_FOUND_ERROR = "Dataset not found"
PAGE_NOT_FOUND_ERROR = "Page not found"
DATASET_TYPE_NAMES = {
    DatasetType.TIMETABLE.value: "TIMETABLE",
    DatasetType.AVL.value: "AVL",
    DatasetType.FARES.value: "FARES",
}


@dataclass(frozen=True)
class DatasetKind:
    """The Django views and URL names behind one dataset type's sub-pages."""

    changelog_view: Type
    subscription_view: Type
    subscription_success_view: Type
    feedback_view: Type
    feedback_success_view: Type
    detail_url_name: str
    subscription_success_label: str
    shows_data_quality: bool = False


DATASET_KINDS = {
    "timetables": DatasetKind(
        changelog_view=timetable_views.DatasetChangeLogView,
        subscription_view=timetable_views.DatasetSubscriptionView,
        subscription_success_view=timetable_views.DatasetSubscriptionSuccessView,
        feedback_view=timetable_views.UserFeedbackView,
        feedback_success_view=timetable_views.UserFeedbackSuccessView,
        detail_url_name="feed-detail",
        subscription_success_label="Go back to data set",
        shows_data_quality=True,
    ),
    "avl": DatasetKind(
        changelog_view=avl_views.AVLChangeLogView,
        subscription_view=avl_views.AvlSubscriptionView,
        subscription_success_view=avl_views.AvlSubscriptionSuccessView,
        feedback_view=avl_views.AvlUserFeedbackView,
        feedback_success_view=avl_views.AvlUserFeedbackSuccessView,
        detail_url_name="avl-feed-detail",
        subscription_success_label="Go back to data feed",
    ),
    "fares": DatasetKind(
        changelog_view=fares_views.FaresChangeLogView,
        subscription_view=fares_views.FaresSubscriptionView,
        subscription_success_view=fares_views.FaresSubscriptionSuccessView,
        feedback_view=fares_views.FaresUserFeedbackView,
        feedback_success_view=fares_views.FaresUserFeedbackSuccessView,
        detail_url_name="fares-feed-detail",
        subscription_success_label="Go back to data set",
    ),
}


def _error(message: str, status: int, **extra) -> JsonResponse:
    return JsonResponse({"error": message, **extra}, status=status)


def _authenticated_user(request):
    user = get_user(request)
    return user if user is not None and user.is_authenticated else None


def _url_path(url: str) -> str:
    """Public data-host path (with query) for an absolute django-hosts URL."""
    parsed = urlparse(url)
    return f"{parsed.path}?{parsed.query}" if parsed.query else parsed.path


def _detail_path(kind: DatasetKind, dataset_id: int) -> str:
    return _url_path(
        reverse(kind.detail_url_name, args=[dataset_id], host=config.hosts.DATA_HOST)
    )


def _is_safe_back_path(path: Optional[str]) -> bool:
    """Only same-site relative paths may be stashed as a back link."""
    return bool(
        path
        and path.startswith("/")
        and not path.startswith("//")
        and "\\" not in path
        and "\n" not in path
        and "\r" not in path
    )


def _get_view(view_class: Type, request, pk: int):
    view = view_class()
    view.setup(request, pk=pk)
    return view


# --- Changelog ---------------------------------------------------------------


def _changelog_data_quality(revision) -> dict:
    """Structured form of ``TimetableChangelogTable.render_data_quality``."""
    report = revision.report.order_by("-id").first()
    if report is None:
        task = revision.data_quality_tasks.order_by("-id").first()
        if task is None or task.status == DataQualityTask.FAILURE:
            return {"text": "Not available"}
        if now() - task.created < timedelta(minutes=settings.DQS_WAIT_TIMEOUT):
            return {"text": "Generating..."}
        return {"text": "Not available"}

    rag = get_data_quality_rag(report)
    if rag:
        return {
            "score": percentage(rag.score, 0),
            "ragLevel": rag.rag_level.upper(),
            "indicator": rag.css_indicator,
        }
    return {"text": ""}


def _serialize_changelog_row(revision, dataset_type: int, kind: DatasetKind) -> dict:
    label, css_class = _subscription_status_display(revision.status, dataset_type)
    # The Django table adds an extra error row (even an empty one) for error status
    show_errors = revision.status == "error"
    errors = (
        [error.description for error in revision.errors.all()] if show_errors else []
    )

    updated_at = ""
    if revision.published_at:
        updated_at = revision.published_at.astimezone(
            pytz.timezone("Europe/London")
        ).strftime("%d %b %Y %H:%M")

    row = {
        "revisionId": revision.id,
        "comment": revision.comment or "",
        "statusLabel": label,
        "statusClass": css_class,
        "updatedAt": updated_at,
        "showErrors": show_errors,
        "errors": errors,
    }
    if kind.shows_data_quality:
        row["dataQuality"] = _changelog_data_quality(revision)
    return row


@require_GET
def get_dataset_changelog_api(request, pk, kind):
    """Data ``feed-changelog`` page data. Public, like the Django page."""
    dataset_kind = DATASET_KINDS[kind]
    view = _get_view(dataset_kind.changelog_view, request, pk)
    try:
        queryset = view.get_queryset()
    except Http404:
        return _error(DATASET_NOT_FOUND_ERROR, 404)

    paginator = Paginator(
        queryset.prefetch_related("errors"), dataset_kind.changelog_view.paginate_by
    )
    try:
        page = paginator.page(request.GET.get("page", 1))
    except (PageNotAnInteger, EmptyPage):
        return _error(PAGE_NOT_FOUND_ERROR, 404)

    dataset = view.dataset
    return JsonResponse(
        {
            "datasetId": dataset.id,
            "datasetType": DATASET_TYPE_NAMES[dataset.dataset_type],
            "name": dataset.name or "",
            "showDataQuality": dataset_kind.shows_data_quality,
            "count": paginator.count,
            "page": page.number,
            "pageSize": paginator.per_page,
            "totalPages": paginator.num_pages,
            "results": [
                _serialize_changelog_row(revision, dataset.dataset_type, dataset_kind)
                for revision in page.object_list
            ],
        }
    )


# --- Subscription ------------------------------------------------------------


def _get_subscribable_dataset(view):
    """The Django view's own queryset: published datasets of the right type."""
    try:
        return view.get_object()
    except Http404:
        return None


def _subscription_payload(request, dataset, kind: DatasetKind) -> dict:
    user = _authenticated_user(request)
    return {
        "datasetId": dataset.id,
        "datasetType": DATASET_TYPE_NAMES[dataset.dataset_type],
        "name": dataset.name or "",
        "detailPath": _detail_path(kind, dataset.id),
        "isAuthenticated": user is not None,
        "isSubscribed": (
            user.subscriptions.filter(id=dataset.id).exists() if user else None
        ),
    }


@require_http_methods(["GET", "POST"])
def dataset_subscription_api(request, pk, kind):
    """Data ``feed-subscription`` (confirm page) data, and the subscribe toggle."""
    dataset_kind = DATASET_KINDS[kind]
    view = _get_view(dataset_kind.subscription_view, request, pk)
    dataset = _get_subscribable_dataset(view)
    if dataset is None:
        return _error(DATASET_NOT_FOUND_ERROR, 404)

    user = _authenticated_user(request)
    detail_path = _detail_path(dataset_kind, dataset.id)

    if request.method == "GET":
        payload = _subscription_payload(request, dataset, dataset_kind)
        if user is not None:
            # The success page needs the user's origin page (feed detail or manage
            # subscriptions), which is no longer the referrer by then.
            back_path = request.GET.get("backPath")
            get_adapter(request).stash_back_url(
                request, back_path if _is_safe_back_path(back_path) else detail_path
            )
        return JsonResponse(payload)

    if user is None:
        return _error(AUTH_REQUIRED_ERROR, 401)

    form = ConfirmationForm(cancel_url=detail_path, data=_json_body(request))
    if not form.is_valid():
        return _error("Validation failed", 400, field_errors=_form_field_errors(form))

    # Toggle subscription (DatasetSubscriptionView.form_valid)
    if user.subscriptions.filter(id=dataset.id).exists():
        DatasetSubscription.objects.filter(dataset=dataset, user=user).delete()
    else:
        DatasetSubscription.objects.create(user=user, dataset=dataset)

    return JsonResponse(
        {"isSubscribed": user.subscriptions.filter(id=dataset.id).exists()}
    )


@require_GET
def get_dataset_subscription_success_api(request, pk, kind):
    """Data ``feed-subscription-success`` page data."""
    dataset_kind = DATASET_KINDS[kind]
    view = _get_view(dataset_kind.subscription_success_view, request, pk)
    dataset = _get_subscribable_dataset(view)
    if dataset is None:
        return _error(DATASET_NOT_FOUND_ERROR, 404)

    payload = _subscription_payload(request, dataset, dataset_kind)
    user = _authenticated_user(request)
    if user is None:
        return JsonResponse(payload)

    adapter = get_adapter(request)
    back_path = adapter.unstash_back_url(request) or payload["detailPath"]
    manage_path = _url_path(reverse("users:feeds-manage", host=config.hosts.DATA_HOST))
    is_manage_page = urlparse(back_path).path.rstrip("/") == manage_path.rstrip("/")
    if is_manage_page:
        # DatasetPaginatorTable: the unsubscribed row may have emptied the last page.
        num_pages = view._get_paginator(user).num_pages
        back_path = f"{manage_path.rstrip('/')}?page={num_pages}"

    payload.update(
        {
            "backPath": back_path,
            "backButtonText": (
                "Go back to manage subscriptions"
                if is_manage_page
                else dataset_kind.subscription_success_label
            ),
        }
    )
    return JsonResponse(payload)


# --- Feedback ----------------------------------------------------------------


def _get_feedback_view(request, pk, kind: DatasetKind):
    """The Django feedback view primed the way its get()/post() prime it."""
    dataset = get_object_or_404(
        Dataset.objects.select_related("live_revision", "organisation"), id=pk
    )
    if dataset.live_revision is None:
        # Django raises on a dataset with no live revision; there is nothing to
        # send feedback about.
        raise Http404(DATASET_NOT_FOUND_ERROR)

    view = _get_view(kind.feedback_view, request, pk)
    view.dataset = dataset
    view.object = None
    return view


@require_http_methods(["GET", "POST"])
def dataset_feedback_api(request, pk, kind):
    """Data ``feed-feedback`` page data, and the feedback submission."""
    if _authenticated_user(request) is None:
        return _error(AUTH_REQUIRED_ERROR, 401)

    dataset_kind = DATASET_KINDS[kind]
    try:
        view = _get_feedback_view(request, pk, dataset_kind)
    except Http404:
        return _error(DATASET_NOT_FOUND_ERROR, 404)
    dataset = view.dataset

    if request.method == "GET":
        context = view.get_context_data()
        return JsonResponse(
            {
                "datasetId": dataset.id,
                "datasetType": DATASET_TYPE_NAMES[dataset.dataset_type],
                "name": dataset.live_revision.name,
                "service": context.get("service"),
                "lineName": context.get("line_name"),
                "stopName": context.get("stop_name"),
                "atcoCode": context.get("atco_code"),
                "journeyStartTime": context.get("journey_start_time"),
                "direction": context.get("direction"),
                "backPath": _url_path(context["back_url"]),
            }
        )

    data = _json_body(request)
    form = ConsumerFeedbackForm(
        data={
            "feedback": data.get("feedback", ""),
            "anonymous": data.get("anonymous", False),
        },
        initial=view.get_initial(),
    )
    if not form.is_valid():
        return _error("Validation failed", 400, field_errors=_form_field_errors(form))

    # Saves the feedback and sends the notification emails.
    view.form_valid(form)
    return JsonResponse({"redirectPath": _url_path(view.get_success_url())})


@require_GET
def get_dataset_feedback_success_api(request, pk, kind):
    """Data ``feed-feedback-success`` page data. Like Django, it never looks up the
    dataset: timetables go back to the line detail page, the rest to their detail."""
    if _authenticated_user(request) is None:
        return _error(AUTH_REQUIRED_ERROR, 401)

    view = _get_view(DATASET_KINDS[kind].feedback_success_view, request, pk)
    return JsonResponse({"backPath": _url_path(view.get_context_data()["back_link"])})
