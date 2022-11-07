import logging

from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import FileUploadParser

from ..models import FaresValidation, FaresValidationResult
from ..serializers import FaresSerializer
from . import fares_validation

logger = logging.getLogger(__name__)


class FaresXmlValidator:
    parser_classes = [FileUploadParser]

    def __init__(self, request, pk1, pk2):
        self.file = request
        self.pk1 = pk1
        self.pk2 = pk2

    def get_errors(self):
        validations = FaresValidation.objects.filter(
            revision_id=self.pk2, organisation_id=self.pk1
        )
        serializer = FaresSerializer(validations, many=True)
        return JsonResponse(serializer.data, safe=False)

    def set_errors(self):
        file_obj = self.file

        fares_validator = fares_validation.get_fares_validator()
        violations = fares_validator.get_violations(file_obj, self.pk1)
        if violations and len(violations) > 0:
            fares_violations = [
                FaresValidation.save_observations(
                    revision_id=self.pk2, org_id=self.pk1, violation=error
                )
                for error in violations
            ]
            FaresValidationResult.save_validation_result(
                revision_id=self.pk2, org_id=self.pk1, violation=violations
            )

            serializer = FaresSerializer(fares_violations, many=True)
            return JsonResponse(
                serializer.data, safe=False, status=status.HTTP_201_CREATED
            )
        return JsonResponse({}, status=status.HTTP_200_OK)
