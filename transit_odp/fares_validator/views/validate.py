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
        # For 'Update data' flow which allows validation to occur multiple times
        FaresValidation.objects.filter(
            revision_id=self.pk2, organisation_id=self.pk1
        ).delete()
        validations = FaresValidation.objects.filter(
            revision_id=self.pk2, organisation_id=self.pk1
        )
        serializer = FaresSerializer(validations, many=True)
        return JsonResponse(serializer.data, safe=False)

    def set_errors(self):
        response = ""
        file_obj = self.file
        fares_validator = fares_validation.get_fares_validator()
        raw_violations = fares_validator.get_violations(file_obj, self.pk1)
        violations = []
        [
            violations.append(violation)
            for violation in raw_violations
            if violation not in violations
        ]
        logger.info(f"Revision {self.pk2} contains {len(violations)} fares violations.")
        if violations:
            for violation in violations:
                # For 'Update data' flow
                FaresValidation.objects.filter(
                    revision_id=self.pk2, organisation_id=self.pk1
                ).delete()
                fares_violations = FaresValidation.create_observations(
                    revision_id=self.pk2, org_id=self.pk1, violation=violation
                ).save()

            serializer = FaresSerializer(fares_violations, many=True)
            response = JsonResponse(
                serializer.data, safe=False, status=status.HTTP_201_CREATED
            )
        # For 'Update data' flow
        FaresValidationResult.objects.filter(
            revision_id=self.pk2, organisation_id=self.pk1
        ).delete()
        FaresValidationResult.create_validation_result(
            revision_id=self.pk2, org_id=self.pk1, violations=violations
        ).save()
        return (
            response
            if response
            else JsonResponse({}, safe=False, status=status.HTTP_200_OK)
        )
