import logging
from pathlib import Path

from django.http import JsonResponse
from lxml import etree
from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.parsers import FileUploadParser
from rest_framework.views import APIView

from ..models import FaresValidation
from ..serializers import FaresSerializer
from . import fares_validation

logger = logging.getLogger(__name__)
type_of_observation = "Simple fares validation failure"
category = ""  # Itr2 To be extratced from the xml path
FARES_SCHEMA = (
    Path(__file__).parent.parent / "schema" / "netex_dataObjectRequest_service.xsd"
)


class FaresXmlValidator(APIView):
    parser_classes = [FileUploadParser]

    def get(self, request, pk1, pk2):
        validations = FaresValidation.objects.filter(
            dataset_id=pk2, organisation_id=pk1
        )
        serializer = FaresSerializer(validations, many=True)
        return JsonResponse(serializer.data, safe=False)

    def post(self, request, pk1, pk2, format=None):
        if "file" not in request.data:
            raise ParseError("Empty content")
        file_obj = request.data["file"]

        fares_validator = fares_validation.get_fares_validator()
        violations = fares_validator.get_violations(file_obj, self.pk1)
        if violations:
            for error in violations:
                fares_validator_model_object = FaresValidation(
                    dataset_id=self.pk2,
                    organisation_id=self.pk1,
                    file_name=error.filename,
                    error_line_no=error.line,
                    error=error.observation.details,
                    type_of_observation=error.observation.category,
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

    def get_lxml_schema(self, schema):
        """Creates an lxml XMLSchema object from a file"""

        if schema is None:
            return

        if not isinstance(schema, etree.XMLSchema):
            logger.info(f"[XML] => Parsing {schema}.")
            root = etree.parse(str(FARES_SCHEMA))
            schema = etree.XMLSchema(root)
        return schema
