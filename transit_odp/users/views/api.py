"""JSON API views backing the Next.js account management pages: My account,
Account settings, Organisation profile, Member management, and Agent invites."""

import json
import re

from django.contrib.auth import get_user
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_GET, require_POST
from rest_framework.authtoken.models import Token

from transit_odp.notifications import get_notifications
from transit_odp.organisation.constants import DatasetType
from transit_odp.organisation.models import Dataset, Licence, OperatorCode, Organisation
from transit_odp.organisation.models.data import ServiceCodeExemption
from transit_odp.users.constants import DATASET_MANAGE_TABLE_PAGINATE_BY, AccountType
from transit_odp.users.forms.account import PublishAdminNotifications
from transit_odp.users.models import Invitation, User
from transit_odp.users.models import AgentUserInvite, UserSettings

AUTH_REQUIRED_ERROR = "Authentication required"
ORG_ADMIN_REQUIRED_ERROR = "Org admin access required"


def _authenticate_user(request):
    user = get_user(request)
    if user is None or not user.is_authenticated:
        return None
    return user


def _json_body(request) -> dict:
    if not request.body:
        return {}
    try:
        return json.loads(request.body)
    except ValueError:
        return {}


def _serialize_agent_invitation(invite: AgentUserInvite) -> dict:
    return {
        "id": invite.id,
        "organisationName": invite.organisation.name,
        "status": invite.status,
        "isPending": invite.is_pending,
        "isAccepted": invite.is_accepted,
    }


@require_GET
def get_account_api(request):
    """Return the data shown on the "My account" page (users/user_account.html)."""
    user = _authenticate_user(request)
    if user is None:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    organisation = user.organisation

    agent_invitations = None
    if user.is_agent_user:
        agent_invitations = [
            _serialize_agent_invitation(invite)
            for invite in user.agent_invitations.all()
            if invite.is_active
        ]

    return JsonResponse(
        {
            "isDeveloper": user.is_developer,
            "isSingleOrgUser": user.is_single_org_user,
            "isAgentUser": user.is_agent_user,
            "isOrgAdmin": user.is_org_admin,
            "prettyAccountName": user.pretty_account_name,
            "isActive": user.is_active,
            "prettyStatus": user.pretty_status,
            "organisationId": organisation.id if organisation else None,
            "organisationName": organisation.name if organisation else None,
            "agentInvitations": agent_invitations,
        },
        status=200,
    )


@require_GET
def get_account_settings_api(request):
    """Return the data shown on the "Account settings" page (users/users_settings.html)."""
    user = _authenticate_user(request)
    if user is None:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    settings, _created = UserSettings.objects.get_or_create(user=user)
    api_key = Token.objects.get_or_create(user=user)[0]

    return JsonResponse(
        {
            "username": user.username,
            "email": user.email,
            "apiKey": api_key.key,
            "showNotificationsForm": user.is_org_user,
            "showInvitationNotify": user.is_org_admin,
            "notifyInvitationAccepted": settings.notify_invitation_accepted,
            "notifyAvlUnavailable": settings.notify_avl_unavailable,
            "dailyComplianceCheckAlert": settings.daily_compliance_check_alert,
        },
        status=200,
    )


@require_POST
def update_account_settings_api(request):
    user = _authenticate_user(request)
    if user is None:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    if not user.is_org_user:
        return JsonResponse({"error": "Org user access required"}, status=403)

    settings, _created = UserSettings.objects.get_or_create(user=user)
    form = PublishAdminNotifications(
        data=request.POST or _json_body(request), instance=settings
    )

    if not form.is_valid():
        return JsonResponse(
            {"error": "Validation failed", "field_errors": form.errors}, status=400
        )

    form.save()

    return JsonResponse(
        {
            "notifyInvitationAccepted": settings.notify_invitation_accepted,
            "notifyAvlUnavailable": settings.notify_avl_unavailable,
            "dailyComplianceCheckAlert": settings.daily_compliance_check_alert,
        },
        status=200,
    )


def _dataset_type_name(dataset_type: int) -> str:
    if dataset_type == DatasetType.AVL.value:
        return "AVL"
    if dataset_type == DatasetType.FARES.value:
        return "FARES"
    return "TIMETABLE"


def _subscription_status_display(
    status: str | None, dataset_type: int
) -> tuple[str, str]:
    """Labels from organisation/snippets/status_indicator.html."""
    if status == "live":
        return ("Published", "status-indicator--success")
    if status in ("indexing", "pending"):
        return ("Processing", "status-indicator--indexing")
    if status == "warning":
        return ("Warning", "status-indicator--warning")
    if status == "expiring":
        return ("Soon to expire", "status-indicator--warning")
    if status == "error":
        if dataset_type == DatasetType.AVL.value:
            return ("Published", "status-indicator--success")
        return ("Error", "status-indicator--error")
    if status in ("draft", "success"):
        return ("Draft", "status-indicator--draft")
    if status == "expired":
        return ("Expired", "status-indicator--inactive")
    if status == "inactive":
        return ("Inactive", "status-indicator--inactive")
    if status == "deleted":
        return ("Deleted", "status-indicator--error")
    return (status or "", "")


def _serialize_subscription(dataset: Dataset) -> dict:
    status_label, status_class = _subscription_status_display(
        getattr(dataset, "status", None),
        dataset.dataset_type,
    )
    return {
        "id": dataset.id,
        "name": getattr(dataset, "name", None) or "",
        "datasetType": _dataset_type_name(dataset.dataset_type),
        "statusLabel": status_label,
        "statusClass": status_class,
    }


@require_GET
def get_subscriptions_api(request):
    """Return the signed-in user's dataset subscriptions (users/feeds_manage.html)."""
    user = _authenticate_user(request)
    if user is None:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    settings, _created = UserSettings.objects.get_or_create(user=user)
    queryset = Dataset.objects.filter(subscribers=user).add_live_data().order_by("id")
    paginator = Paginator(queryset, DATASET_MANAGE_TABLE_PAGINATE_BY)
    page = paginator.get_page(request.GET.get("page"))

    return JsonResponse(
        {
            "muteNotifications": settings.mute_all_dataset_notifications,
            "count": paginator.count,
            "page": page.number,
            "pageSize": DATASET_MANAGE_TABLE_PAGINATE_BY,
            "totalPages": paginator.num_pages,
            "results": [
                _serialize_subscription(dataset) for dataset in page.object_list
            ],
        },
        status=200,
    )


@require_POST
def update_subscriptions_mute_api(request):
    user = _authenticate_user(request)
    if user is None:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    mute = _json_body(request).get("muteNotifications")
    if not isinstance(mute, bool):
        return JsonResponse(
            {"error": "muteNotifications must be true or false"},
            status=400,
        )

    settings, _created = UserSettings.objects.get_or_create(user=user)
    settings.mute_all_dataset_notifications = mute
    settings.save(update_fields=["mute_all_dataset_notifications"])

    return JsonResponse(
        {"muteNotifications": settings.mute_all_dataset_notifications},
        status=200,
    )


def _serialize_agent_invite_detail(invite: AgentUserInvite) -> dict:
    return {
        "id": invite.id,
        "organisationName": invite.organisation.name,
        "agentEmail": invite.email,
        "status": invite.status,
    }


@require_GET
def get_agent_invite_api(request, pk):
    """Return details for a single agent invite, for the accept/leave/remove/resend
    confirmation pages. Visible to the invited agent or the inviting organisation's admin."""
    user = _authenticate_user(request)
    if user is None:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    try:
        invite = AgentUserInvite.objects.get(pk=pk)
    except AgentUserInvite.DoesNotExist:
        return JsonResponse({"error": "Invite not found"}, status=404)

    is_invited_agent = invite.agent_id == user.id
    is_inviting_org_admin = (
        user.is_org_admin and user.organisation_id == invite.organisation_id
    )
    if not (is_invited_agent or is_inviting_org_admin):
        return JsonResponse({"error": "Not found"}, status=404)

    return JsonResponse(_serialize_agent_invite_detail(invite), status=200)


@require_POST
def respond_agent_invite_api(request, pk):
    """Accept or reject a pending invite to act as an agent for an organisation."""
    user = _authenticate_user(request)
    if user is None:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    invite = user.agent_invitations.filter(
        pk=pk, status=AgentUserInvite.PENDING
    ).first()
    if invite is None:
        return JsonResponse({"error": "Invite not found"}, status=404)

    status = _json_body(request).get("status")
    if status == AgentUserInvite.ACCEPTED:
        invite.accept_invite()
    elif status == AgentUserInvite.REJECTED:
        invite.reject_invite()
    else:
        return JsonResponse(
            {"error": "status must be 'accepted' or 'rejected'"}, status=400
        )

    return JsonResponse(_serialize_agent_invite_detail(invite), status=200)


@require_POST
def leave_agent_organisation_api(request, pk):
    """The signed-in agent leaves an organisation they previously accepted."""
    user = _authenticate_user(request)
    if user is None:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    invite = user.agent_invitations.filter(
        pk=pk, status=AgentUserInvite.ACCEPTED
    ).first()
    if invite is None:
        return JsonResponse({"error": "Invite not found"}, status=404)

    invite.leave_organisation()
    return JsonResponse(_serialize_agent_invite_detail(invite), status=200)


@require_POST
def remove_agent_from_organisation_api(request, pk):
    """An org admin removes an accepted agent from their organisation."""
    user = _authenticate_user(request)
    if user is None:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    if not user.is_org_admin:
        return JsonResponse({"error": "Org admin access required"}, status=403)

    invite = user.organisation.agentuserinvite_set.filter(
        pk=pk, status=AgentUserInvite.ACCEPTED
    ).first()
    if invite is None:
        return JsonResponse({"error": "Invite not found"}, status=404)

    invite.remove_agent()
    return JsonResponse(_serialize_agent_invite_detail(invite), status=200)


@require_POST
def resend_agent_invite_api(request, pk):
    """An org admin resends a pending agent invite/confirmation email."""
    user = _authenticate_user(request)
    if user is None:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    if not user.is_org_admin:
        return JsonResponse({"error": "Org admin access required"}, status=403)

    invite = user.organisation.agentuserinvite_set.filter(
        pk=pk, status=AgentUserInvite.PENDING
    ).first()
    if invite is None:
        return JsonResponse({"error": "Invite not found"}, status=404)

    if invite.agent is None:
        invite.invitation.send_invitation(request)
    else:
        invite.send_confirmation()

    return JsonResponse(_serialize_agent_invite_detail(invite), status=200)


LICENCE_NUMBER_RE = re.compile(r"^[A-Za-z]{2}\d{7}$")
LICENCE_FORMAT_ERROR = "Enter a valid PSV licence number, like AB1234567"
LICENCE_REQUIRED_ERROR = (
    "Untick 'I do not have a PSV licence number' to add licence numbers"
)
INVITE_ACCOUNT_TYPES = {
    "admin": AccountType.org_admin.value,
    "staff": AccountType.org_staff.value,
    "agent": AccountType.agent_user.value,
}


def _notify_noc_changed(organisation: Organisation) -> None:
    notifier = get_notifications()
    account_types = [AccountType.org_admin.value, AccountType.agent_user.value]
    recipients = organisation.users.filter(
        account_type__in=account_types, is_active=True
    )
    for recipient in recipients:
        if recipient.is_agent_user:
            notifier.send_agent_noc_changed_notification(
                organisation.name, recipient.email
            )
        else:
            notifier.send_operator_noc_changed_notification(recipient.email)


@require_GET
def get_organisation_profile_api(request, pk):
    user = _authenticate_user(request)
    if user is None:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    organisation = user.organisations.filter(pk=pk).first()
    if organisation is None:
        return JsonResponse({"error": "Organisation not found"}, status=404)

    licences = organisation.licences.all()
    service_code_exemptions = (
        ServiceCodeExemption.objects.filter(licence__in=licences)
        .add_registration_number()
        .order_by("licence__number", "registration_code")
    )

    return JsonResponse(
        {
            "id": organisation.id,
            "name": organisation.name,
            "shortName": organisation.short_name,
            "licenceRequired": organisation.licence_required,
            "nocs": list(organisation.nocs.values_list("noc", flat=True)),
            "licenceNumbers": list(licences.values_list("number", flat=True)),
            "canEdit": user.is_org_admin or user.is_agent_user,
            "serviceCodeExemptions": [
                {
                    "registrationNumber": exemption.registration_number,
                    "justification": exemption.justification,
                }
                for exemption in service_code_exemptions
            ],
        },
        status=200,
    )


@require_POST
def update_organisation_profile_api(request, pk):
    user = _authenticate_user(request)
    if user is None:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    if not (
        user.organisations.filter(pk=pk).exists()
        and (user.is_org_admin or user.is_agent_user)
    ):
        return JsonResponse({"error": "Org admin or agent access required"}, status=403)

    try:
        organisation = Organisation.objects.get(pk=pk)
    except Organisation.DoesNotExist:
        return JsonResponse({"error": "Organisation not found"}, status=404)

    body = _json_body(request)
    short_name = (body.get("shortName") or "").strip()
    licence_required = bool(body.get("licenceRequired"))
    nocs = [noc.strip() for noc in body.get("nocs", []) if noc.strip()]
    licence_numbers = [
        num.strip().upper() for num in body.get("licenceNumbers", []) if num.strip()
    ]

    field_errors = {}
    if not short_name:
        field_errors["shortName"] = ["Enter a short name"]
    if licence_numbers and not licence_required:
        field_errors["licenceRequired"] = [LICENCE_REQUIRED_ERROR]
    invalid_licences = [
        num for num in licence_numbers if not LICENCE_NUMBER_RE.match(num)
    ]
    if invalid_licences:
        field_errors["licenceNumbers"] = [LICENCE_FORMAT_ERROR]

    if field_errors:
        return JsonResponse(
            {"error": "Validation failed", "field_errors": field_errors}, status=400
        )

    noc_changed = set(organisation.nocs.values_list("noc", flat=True)) != set(nocs)

    try:
        with transaction.atomic():
            organisation.short_name = short_name
            organisation.licence_required = licence_required
            organisation.save(update_fields=["short_name", "licence_required"])

            organisation.nocs.all().delete()
            OperatorCode.objects.bulk_create(
                [OperatorCode(organisation=organisation, noc=noc) for noc in nocs]
            )

            organisation.licences.all().delete()
            if licence_required:
                Licence.objects.bulk_create(
                    [
                        Licence(organisation=organisation, number=num)
                        for num in licence_numbers
                    ]
                )
    except IntegrityError:
        return JsonResponse(
            {
                "error": "One of the NOC codes or licence numbers is already registered to another organisation."
            },
            status=400,
        )

    if noc_changed:
        _notify_noc_changed(organisation)

    return JsonResponse({"id": organisation.id}, status=200)


def _serialize_member(member: User) -> dict:
    return {
        "id": member.id,
        "username": member.username,
        "email": member.email,
        "accountType": member.account_type,
        "prettyAccountName": member.pretty_account_name,
        "isActive": member.is_active,
        "prettyStatus": member.pretty_status,
        "isSingleOrgUser": member.is_single_org_user,
        "agentUser": member.is_agent_user,
    }


def _serialize_pending_invite(invite: Invitation) -> dict:
    return {
        "id": invite.id,
        "email": invite.email,
        "accountType": invite.account_type,
        "sent": invite.sent.isoformat() if invite.sent else None,
    }


@require_GET
def get_organisation_members_api(request, pk):
    user = _authenticate_user(request)
    if user is None:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    if not (user.is_org_admin and user.organisation_id == int(pk)):
        return JsonResponse({"error": ORG_ADMIN_REQUIRED_ERROR}, status=403)

    organisation = user.organisation

    return JsonResponse(
        {
            "members": [
                _serialize_member(member) for member in organisation.users.all()
            ],
            "pendingInvites": [
                _serialize_pending_invite(invite)
                for invite in organisation.invitation_set.filter(
                    accepted=False, agent_user_invite=None
                )
            ],
            "pendingAgentInvites": [
                _serialize_agent_invitation(invite)
                for invite in organisation.agentuserinvite_set.filter(
                    status=AgentUserInvite.PENDING
                )
            ],
        },
        status=200,
    )


@require_POST
def create_organisation_invite_api(request, pk):
    user = _authenticate_user(request)
    if user is None:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    if not (user.is_org_admin and user.organisation_id == int(pk)):
        return JsonResponse({"error": ORG_ADMIN_REQUIRED_ERROR}, status=403)

    body = _json_body(request)
    email = (body.get("email") or "").strip().lower()
    account_type = INVITE_ACCOUNT_TYPES.get(body.get("accountType"))

    field_errors = {}
    if not email:
        field_errors["email"] = ["Enter a valid email address"]
    if account_type is None:
        field_errors["accountType"] = ["Choose the account type"]
    if field_errors:
        return JsonResponse(
            {"error": "Validation failed", "field_errors": field_errors}, status=400
        )

    organisation = user.organisation

    if account_type == AccountType.agent_user.value:
        existing_agent = User.objects.filter(
            email__iexact=email, account_type=AccountType.agent_user.value
        ).first()
        if existing_agent is not None:
            if existing_agent.organisations.filter(id=organisation.id).exists():
                return JsonResponse(
                    {
                        "error": "Validation failed",
                        "field_errors": {
                            "email": [
                                "This agent is already active for this organisation"
                            ]
                        },
                    },
                    status=400,
                )

            agent_invite, created = AgentUserInvite.objects.get_or_create(
                agent=existing_agent,
                organisation=organisation,
                defaults={"inviter": user, "status": AgentUserInvite.PENDING},
            )
            if not created:
                agent_invite.inviter = user
                agent_invite.status = AgentUserInvite.PENDING
                agent_invite.save()
            agent_invite.send_confirmation()
            return JsonResponse(
                {"email": email, "accountType": account_type}, status=201
            )

    if User.objects.filter(email__iexact=email).exists():
        return JsonResponse(
            {
                "error": "Validation failed",
                "field_errors": {
                    "email": ["A user with this email address already has an account"]
                },
            },
            status=400,
        )

    invitation = Invitation.objects.filter(email__iexact=email).first()
    if invitation is not None:
        invitation.accepted = False
        invitation.key = get_random_string(64).lower()
    else:
        invitation = Invitation(email=email)

    invitation.organisation = organisation
    invitation.account_type = account_type
    invitation.inviter = user
    invitation.is_key_contact = False
    invitation.save()
    invitation.send_invitation(request)

    if account_type == AccountType.agent_user.value:
        agent_invite, created = AgentUserInvite.objects.get_or_create(
            invitation=invitation,
            defaults={
                "agent": None,
                "inviter": user,
                "status": AgentUserInvite.PENDING,
                "organisation": organisation,
            },
        )
        if not created:
            agent_invite.inviter = user
            agent_invite.organisation = organisation
            agent_invite.save()

    return JsonResponse({"email": email, "accountType": account_type}, status=201)


@require_GET
def get_organisation_member_api(request, pk):
    user = _authenticate_user(request)
    if user is None:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    if not user.is_org_admin:
        return JsonResponse({"error": ORG_ADMIN_REQUIRED_ERROR}, status=403)

    allowed_accounts = [
        AccountType.org_admin.value,
        AccountType.org_staff.value,
        AccountType.agent_user.value,
    ]
    member = user.organisation.users.filter(
        pk=pk, account_type__in=allowed_accounts
    ).first()
    if member is None:
        return JsonResponse({"error": "User not found"}, status=404)

    data = _serialize_member(member)
    if member.is_agent_user:
        invite = member.agent_invitations.filter(organisation=user.organisation).last()
        data["agentInviteId"] = invite.id if invite else None
    return JsonResponse(data, status=200)


@require_POST
def update_organisation_member_api(request, pk):
    user = _authenticate_user(request)
    if user is None:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    if not user.is_org_admin:
        return JsonResponse({"error": ORG_ADMIN_REQUIRED_ERROR}, status=403)

    allowed_accounts = [AccountType.org_admin.value, AccountType.org_staff.value]
    member = (
        user.organisation.users.filter(pk=pk, account_type__in=allowed_accounts)
        .exclude(pk=user.id)
        .first()
    )
    if member is None:
        return JsonResponse({"error": "User not found"}, status=404)

    body = _json_body(request)
    username = (body.get("username") or "").strip()
    email = (body.get("email") or "").strip()
    account_type = body.get("accountType")

    field_errors = {}
    if not username:
        field_errors["username"] = ["Enter a username"]
    if not email:
        field_errors["email"] = ["Enter a valid email address"]
    if account_type not in (AccountType.org_admin.value, AccountType.org_staff.value):
        field_errors["accountType"] = ["Choose the account type"]
    if field_errors:
        return JsonResponse(
            {"error": "Validation failed", "field_errors": field_errors}, status=400
        )

    member.username = username
    member.email = email
    member.account_type = account_type
    member.save(update_fields=["username", "email", "account_type"])

    return JsonResponse(_serialize_member(member), status=200)


@require_POST
def toggle_organisation_member_active_api(request, pk):
    user = _authenticate_user(request)
    if user is None:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    if not user.is_org_admin:
        return JsonResponse({"error": ORG_ADMIN_REQUIRED_ERROR}, status=403)

    member = user.organisation.users.exclude(pk=user.id).filter(pk=pk).first()
    if member is None:
        return JsonResponse({"error": "User not found"}, status=404)

    member.is_active = not member.is_active
    member.save(update_fields=["is_active"])

    return JsonResponse(_serialize_member(member), status=200)


@require_POST
def resend_organisation_invite_api(request, pk):
    user = _authenticate_user(request)
    if user is None:
        return JsonResponse({"error": AUTH_REQUIRED_ERROR}, status=401)

    if not user.is_org_admin:
        return JsonResponse({"error": ORG_ADMIN_REQUIRED_ERROR}, status=403)

    invitation = user.organisation.invitation_set.filter(pk=pk).first()
    if invitation is None:
        return JsonResponse({"error": "Invite not found"}, status=404)

    invitation.send_invitation(request)
    return JsonResponse(_serialize_pending_invite(invitation), status=200)
