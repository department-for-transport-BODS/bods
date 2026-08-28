"""
Session-based authentication API views for the Next.js frontend.

All browser auth uses Django's session framework via HttpOnly cookies.
The session cookie is set/cleared by Django and sent automatically by the browser.
Allauth's email verification and adapter hooks are respected.
"""

import re

from allauth.account import app_settings as allauth_settings
from allauth.account import signals as allauth_signals
from allauth.account.adapter import get_adapter
from allauth.account.forms import SignupForm
from allauth.account.models import (
    EmailAddress,
    EmailConfirmation,
    EmailConfirmationHMAC,
)
from allauth.account.utils import (
    complete_signup,
    logout_on_password_change,
    send_email_confirmation,
)
from allauth.utils import get_form_class
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from transit_odp.organisation.models import Organisation
from transit_odp.users.forms.auth import ChangePasswordForm
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

EMAIL_CONFIRMATION_INVALID = "This email confirmation link expired or is invalid."


class LoginRateThrottle(AnonRateThrottle):
    """Throttle login attempts by IP to match allauth's rate limiting."""

    def get_rate(self):
        limit = getattr(settings, "ACCOUNT_LOGIN_ATTEMPTS_LIMIT", 5)
        timeout = getattr(settings, "ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT", 900)
        return f"{limit}/{timeout}s"

    def parse_rate(self, rate):
        num_requests, period = rate.split("/")
        match = re.fullmatch(r"(?:(\d+))?([smhd])", period)

        if match is None:
            return super().parse_rate(rate)

        multiplier, unit = match.groups()
        duration = {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]
        duration *= int(multiplier or 1)
        return int(num_requests), duration


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


@method_decorator(csrf_protect, name="dispatch")
class LoginAPIView(APIView):
    """Authenticate and create a Django session.

    Uses allauth's email verification check while returning JSON
    instead of redirects.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = authenticate(request, username=email, password=password)

        if user is None or not user.is_active:
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Respect allauth's mandatory email verification
        if (
            allauth_settings.EMAIL_VERIFICATION
            == allauth_settings.EmailVerificationMethod.MANDATORY
        ):
            email_address = EmailAddress.objects.filter(
                user=user, email__iexact=email
            ).first()

            if email_address is None or not email_address.verified:
                send_email_confirmation(request, user)
                return Response(
                    {"detail": "Email address not verified."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        login(request, user)

        get_token(request)

        return Response(
            {
                "user": _serialize_user(user),
            },
            status=status.HTTP_200_OK,
        )


@method_decorator(csrf_protect, name="dispatch")
class SignupAPIView(APIView):
    """Register an account using the same allauth forms as Django's SignupView.

    Developer sign up is self-service. Operator and agent sign up is only
    reachable from an invitation, which stashes the invited email in the session.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        # allauth mutates the session and calls django.contrib.auth, so it needs
        # the underlying HttpRequest rather than the DRF wrapper.
        django_request = request._request
        adapter = get_adapter(django_request)

        if not adapter.is_open_for_signup(django_request):
            return Response(
                {"detail": "Registration is closed."},
                status=status.HTTP_403_FORBIDDEN,
            )

        form = _signup_form_class(django_request)(data=request.data)
        if not form.is_valid():
            return Response(
                {
                    "error": "Validation failed",
                    "field_errors": _serialize_form_errors(form),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # try_save emails the existing account holder instead of creating a
        # duplicate, which is what Django's account_exists page reports.
        user = form.try_save(django_request)[0]
        if user is None:
            return Response({"account_exists": True}, status=status.HTTP_200_OK)

        # Sends the verification email and, because verification is mandatory,
        # leaves the user signed out until they confirm.
        complete_signup(django_request, user, allauth_settings.EMAIL_VERIFICATION, None)

        return Response(
            {"account_exists": False, "email": user.email},
            status=status.HTTP_201_CREATED,
        )


class ConfirmEmailSerializer(serializers.Serializer):
    key = serializers.CharField()


@method_decorator(csrf_protect, name="dispatch")
class ConfirmEmailAPIView(APIView):
    """Confirm an email address from the key in the verification email."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = ConfirmEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        confirmation = _find_email_confirmation(serializer.validated_data["key"])
        if confirmation is None:
            return Response(
                {"detail": EMAIL_CONFIRMATION_INVALID},
                status=status.HTTP_400_BAD_REQUEST,
            )

        django_request = request._request
        email_address = confirmation.email_address

        if confirmation.confirm(django_request) is None:
            return Response(
                {"detail": EMAIL_CONFIRMATION_INVALID},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Confirming one account while signed in as another ends the current
        # session, as allauth's ConfirmEmailView does.
        if (
            django_request.user.is_authenticated
            and django_request.user.pk != email_address.user_id
        ):
            logout(django_request)

        get_adapter(django_request).stash_verified_email(
            django_request, email_address.email
        )

        return Response({"email": email_address.email}, status=status.HTTP_200_OK)


class LogoutAPIView(APIView):
    """Destroy the current session."""

    permission_classes = [AllowAny]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_200_OK)


class CurrentUserAPIView(APIView):
    """Return the authenticated user from the session cookie."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(_serialize_user(request.user), status=status.HTTP_200_OK)


class CurrentUserOrganisationsAPIView(APIView):
    """Return organisations available to the authenticated user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        organisations = [
            {
                "id": organisation.id,
                "name": organisation.name,
                "short_name": organisation.short_name,
            }
            for organisation in request.user.organisations.all().order_by("name")
        ]

        return Response(
            {
                "count": len(organisations),
                "next": None,
                "previous": None,
                "results": organisations,
            },
            status=status.HTTP_200_OK,
        )


class CSRFTokenAPIView(APIView):
    """Return a CSRF token for use in subsequent form submissions."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response({"csrfToken": get_token(request)})


@method_decorator(csrf_protect, name="dispatch")
class PasswordChangeAPIView(APIView):
    """Change the signed-in user's password using allauth's ChangePasswordForm."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        form = ChangePasswordForm(user=request.user, data=request.data)
        if not form.is_valid():
            return Response(
                {
                    "error": "Validation failed",
                    "field_errors": _serialize_form_errors(form),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        form.save()
        logout_on_password_change(request, request.user)
        allauth_signals.password_changed.send(
            sender=request.user.__class__,
            request=request,
            user=request.user,
        )
        return Response(status=status.HTTP_200_OK)


class OrganisationStatsAPIView(APIView):
    """Return consumer activity stats for an organisation available to the user."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk1):
        has_org_access = request.user.organisations.filter(id=pk1).exists()
        if not has_org_access:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        organisation = (
            Organisation.objects.select_related("stats")
            .add_total_subscriptions()
            .filter(id=pk1)
            .first()
        )
        if organisation is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "total_subscriptions": organisation.total_subscriptions,
                "weekly_downloads": organisation.stats.weekly_downloads,
                "weekly_api_hits": organisation.stats.weekly_api_hits,
                "weekly_unique_consumers": organisation.stats.weekly_unique_consumers,
            },
            status=status.HTTP_200_OK,
        )


def _signup_form_class(request):
    """Pick the signup form Django's SignupView would use for this session."""
    adapter = get_adapter(request)

    if not adapter.stash_contains_account_verified_email(request):
        form_id = "developer_signup"
    else:
        invitation = adapter.invitation
        form_id = (
            "agent_signup"
            if invitation is not None and invitation.is_agent_user
            else "operator_signup"
        )

    return get_form_class(allauth_settings.FORMS, form_id, SignupForm)


def _find_email_confirmation(key):
    confirmation = EmailConfirmationHMAC.from_key(key)
    if confirmation is not None:
        return confirmation

    return EmailConfirmation.objects.all_valid().filter(key=key.lower()).first()


def _serialize_form_errors(form):
    return {
        field: [str(message) for message in error_list]
        for field, error_list in form.errors.items()
    }


def _serialize_user(user):
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "account_type": user.account_type,
        "organisation_id": user.organisation_id,
        "is_org_user": user.is_org_user,
        "is_single_org_user": user.is_single_org_user,
        "is_agent_user": user.is_agent_user,
        "is_org_admin": user.is_org_admin,
    }
