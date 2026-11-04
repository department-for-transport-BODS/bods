from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from transit_odp.feedback.forms import GlobalFeedbackForm


@method_decorator(csrf_protect, name="dispatch")
class GlobalFeedbackAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = request.data
        form = GlobalFeedbackForm(
            data=payload,
            url=payload.get("page_url", ""),
        )

        if not form.is_valid():
            field_errors = {
                field: [str(message) for message in messages]
                for field, messages in form.errors.items()
            }
            return Response(
                {"field_errors": field_errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        form.save()
        return Response(status=status.HTTP_201_CREATED)
