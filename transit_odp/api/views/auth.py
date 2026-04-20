"""
Session-based authentication API views for the Next.js frontend.

All browser auth uses Django's session framework via HttpOnly cookies.
The session cookie is set/cleared by Django and sent automatically by the browser.
Allauth's email verification and adapter hooks are respected.
"""

import re

from allauth.account import app_settings as allauth_settings
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView


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


def _serialize_user(user):
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        "account_type": user.account_type,
    }