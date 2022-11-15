import logging

from django.http import JsonResponse
from rest_framework import status
from rest_framework.parsers import FileUploadParser

from ..models import FaresValidation
from ..serializers import FaresSerializer
from . import fares_validation

logger = logging.getLogger(__name__)
type_of_observation = "Simple fares validation failure"
category = ""  # Itr2 To be extratced from the xml path


class FaresXmlValidator:
    parser_classes = [FileUploadParser]

    def __init__(self, request, pk1, pk2):
        self.file = request
        self.pk1 = pk1
        self.pk2 = pk2

    def get_errors(self):
        validations = FaresValidation.objects.filter(
            dataset_id=self.pk2, organisation_id=self.pk1
        )
        serializer = FaresSerializer(validations, many=True)
        return JsonResponse(serializer.data, safe=False)

    def set_errors(self):
        file_obj = self.file

        fares_validator = fares_validation.get_fares_validator()
        violations = fares_validator.get_violations(file_obj, self.pk1)
        result = []
        [result.append(violation) for violation in violations if violation not in result]
        if result:
            for error in result:
                fares_validator_model_object = FaresValidation(
                    dataset_id=self.pk2,
                    organisation_id=self.pk1,
                    file_name=error.filename,
                    error_line_no=error.line,
                    error=error.observation,
                    type_of_observation=type_of_observation,
                    category=category,
                )
                fares_validator_model_object.save()

            validations = FaresValidation.objects.filter(
                dataset_id=self.pk2, organisation_id=self.pk1
            )
            serializer = FaresSerializer(validations, many=True)
            return JsonResponse(
                serializer.data, safe=False, status=status.HTTP_201_CREATED
            )
        return JsonResponse({}, status=status.HTTP_200_OK)
