import logging

from django.http import JsonResponse
from lxml import etree
from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.parsers import FileUploadParser
from rest_framework.views import APIView
from pathlib import Path

from ..models import FaresValidation
from ..serializers import FaresSerializer
from .fares_validation import get_fares_validator

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
        return JsonResponse({"errors": serializer.data}, safe=False)

    def post(self, request, pk1, pk2, format=None):
        if "file" not in request.data:
            raise ParseError("Empty content")
        file_obj = request.data["file"]
        file_name = file_obj

        with open(
            str(FARES_SCHEMA),
            "r",
        ) as f:
            schema = f.read()

        if schema is not None:
            lxml_schema = self.get_lxml_schema(schema)
            xmlschema_doc = etree.parse(file_obj)

        try:
            fares_validator = get_fares_validator()
            violations = fares_validator.get_violations(file_obj, pk1)
            lxml_schema.assertValid(xmlschema_doc)

        except etree.DocumentInvalid:
            for error in lxml_schema.error_log:
                fares_validator_model_object = FaresValidation(
                    dataset_id=pk2,
                    organisation_id=pk1,
                    file_name=file_name,
                    error_line_no=error.line,
                    error=error.message,
                    type_of_observation=type_of_observation,
                    category=category,
                )
                fares_validator_model_object.save()

        validations = FaresValidation.objects.filter(dataset_id=pk2)
        serializer = FaresSerializer(validations, many=True)
        return JsonResponse({"errors": serializer.data}, status=status.HTTP_201_CREATED)

    def get_lxml_schema(self, schema):
        """Creates an lxml XMLSchema object from a file"""

        if schema is None:
            return

        if not isinstance(schema, etree.XMLSchema):
            logger.info(f"[XML] => Parsing {schema}.")
            root = etree.parse(str(FARES_SCHEMA))
            schema = etree.XMLSchema(root)
        return schema
