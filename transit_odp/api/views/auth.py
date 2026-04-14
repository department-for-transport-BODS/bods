"""
Authentication API views for NextJS integration
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


class CurrentUserAPIView(APIView):
    """
    API endpoint to get current user data using JWT authentication.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "account_type": user.account_type,
                "organisation_id": user.organisation_id,
                "is_org_user": user.is_org_user,
                "is_agent_user": user.is_agent_user,
                "groups": [{"name": g.name} for g in user.groups.all()],
            },
            status=status.HTTP_200_OK,
        )
