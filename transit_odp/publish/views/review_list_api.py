"""
JSON backing for the Next.js "Review my data" pages (timetables, bus location, fares).

The Django pages are driven by each dataset type's ``BasePublishListView`` subclass:
it picks the queryset for the active/draft/archive tab, builds the django-tables2
table (sorting from ``?sort=`` and pagination from ``?page=``) and computes the
banner figures. This module reuses that view logic as is, so the Next.js pages can
never drift from the Django ones, and only serialises the result.
"""
from urllib.parse import urlparse

from django.core.paginator import EmptyPage, PageNotAnInteger
from django.http import Http404, JsonResponse
from django.utils import formats, timezone

from transit_odp.organisation.tables import get_feed_name_linkify
from transit_odp.users.constants import AccountType

AUTH_REQUIRED_ERROR = "Authentication required"
ORG_ACCESS_REQUIRED_ERROR = "Org user access required"
ORG_NOT_FOUND_ERROR = "Organisation not found"

TIMETABLE = "timetable"
AVL = "avl"
FARES = "fares"


def _display(value):
    """Format a table cell the way ``{{ cell }}`` does in the Django template."""
    if value is None:
        return ""
    if hasattr(value, "tzinfo") or hasattr(value, "isoformat"):
        if hasattr(value, "tzinfo") and value.tzinfo is not None:
            value = timezone.template_localtime(value)
        return formats.localize(value)
    return str(value)


def _iso(value):
    return value.isoformat() if hasattr(value, "isoformat") else None


def _relative_path(url):
    if not url:
        return None
    parsed = urlparse(url)
    return parsed.path


def _row_payload(table, bound_row, dataset_kind):
    record = bound_row.record
    drafts = getattr(record, "draft_revisions", None) or []
    link = get_feed_name_linkify(
        record, app_name=None if dataset_kind == TIMETABLE else dataset_kind
    )

    modified = bound_row.get_cell("modified") if "modified" in table.columns else ""
    payload = {
        "id": record.id,
        "name": getattr(record, "name", None) or "",
        "shortDescription": getattr(record, "short_description", None) or "",
        "status": getattr(record, "status", None),
        "datasetType": record.dataset_type,
        "hasDraftRevision": bool(drafts),
        "draftStatus": drafts[0].status if drafts else None,
        "link": _relative_path(link),
        "modified": _iso(modified),
        "modifiedDisplay": _display(modified),
    }

    if "percent_matching" in table.columns:
        payload["percentMatching"] = _display(bound_row.get_cell("percent_matching"))

    if "avl_feed_last_checked" in table.columns:
        last_checked = bound_row.get_cell("avl_feed_last_checked")
        payload["avlFeedLastChecked"] = _iso(last_checked)
        payload["avlFeedLastCheckedDisplay"] = _display(last_checked)

    return payload


def _column_payload(table):
    columns = []
    sort_param = table.request.GET.get(table.prefixed_order_by_field, "")
    for column in table.columns:
        direction = None
        if column.is_ordered:
            direction = "desc" if column.order_by_alias.is_descending else "asc"
        next_sort = str(column.order_by_alias.next) if column.orderable else None
        columns.append(
            {
                "key": column.name,
                "label": str(column.header),
                "orderable": column.orderable,
                "nextSort": next_sort,
                "direction": direction,
                "width": column.attrs.get("th", {}).get("width"),
            }
        )
    return columns, sort_param


def _banner_payload(context, dataset_kind):
    organisation = context["organisation"]
    stats = getattr(organisation, "stats", None)
    consumer_interactions = (
        getattr(stats, "weekly_downloads", 0)
        + getattr(stats, "weekly_api_hits", 0)
        + (getattr(organisation, "total_subscriptions", 0) or 0)
    )

    if dataset_kind == TIMETABLE:
        return {
            "servicesRequiringAttention": context["services_requiring_attention"],
            "applicableServices": context["applicable_services"],
            "feedbackCount": context["feedback_count"],
            "seasonalServicesCounter": context["seasonal_services_counter"],
        }

    if dataset_kind == AVL:
        return {
            "totalConsumerInteractions": consumer_interactions,
            "overallPpcScore": context["overall_ppc_score"],
            "isAvlRequireAttentionActive": context["is_avl_require_attention_active"],
            "servicesRequiringAttention": context["services_requiring_attention"],
            "applicableServices": context["total_in_scope_in_season_services"],
        }

    return {
        "totalConsumerInteractions": consumer_interactions,
        "isFaresRequireAttentionActive": context["is_fares_require_attention_active"],
        "servicesRequiringAttention": context["services_requiring_attention"],
        "applicableServices": context["applicable_services"],
    }


def build_review_list_response(request, pk1, view_class, dataset_kind):
    """Serialise one tab of a ``BasePublishListView`` subclass as JSON."""
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    # Mirrors OrgUserViewMixin.has_permission: ABODS users never see this page.
    if not user.is_org_user or user.account_type == AccountType.abods_user.value:
        return JsonResponse({"error": ORG_ACCESS_REQUIRED_ERROR}, status=403)

    if not user.organisations.filter(id=pk1).exists():
        return JsonResponse({"error": ORG_NOT_FOUND_ERROR}, status=404)

    view = view_class()
    view.setup(request, pk1=pk1)
    view.datasets = view.get_datasets()
    try:
        context = view.get_context_data(pk1=pk1)
    except (EmptyPage, PageNotAnInteger, Http404):
        return JsonResponse({"error": "Page not found"}, status=404)

    table = context["active_feeds_table"]
    organisation = context["organisation"]
    summary = {
        "tab": context["tab"],
        "pageTitle": str(context["page_title"]),
        "organisation": {"id": organisation.id, "name": organisation.name},
        "isAgentUser": user.is_agent_user,
        "banner": _banner_payload(context, dataset_kind),
    }

    if table is None:
        # Django renders "No data sets found" for an unrecognised tab.
        return JsonResponse(
            {
                **summary,
                "sort": "",
                "columns": [],
                "page": 1,
                "pageSize": view.per_page,
                "totalPages": 1,
                "count": 0,
                "hasNext": False,
                "hasPrevious": False,
                "results": [],
            }
        )

    columns, sort = _column_payload(table)
    page = table.page

    return JsonResponse(
        {
            **summary,
            "sort": sort,
            "columns": columns,
            "page": page.number,
            "pageSize": view.per_page,
            "totalPages": table.paginator.num_pages,
            "count": table.paginator.count,
            "hasNext": page.has_next(),
            "hasPrevious": page.has_previous(),
            "results": [
                _row_payload(table, bound_row, dataset_kind)
                for bound_row in page.object_list
            ],
        },
        status=200,
    )
