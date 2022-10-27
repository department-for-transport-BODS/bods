import logging

from django.http import JsonResponse
from lxml import etree
from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.parsers import FileUploadParser
from rest_framework.views import APIView
from pathlib import Path

from transit_odp.fares_validator.utils.files_parser import file_to_etree
from . import fares_validation

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
        return JsonResponse(serializer.data, safe=False)

    def post(self, request, pk1, pk2, format=None):
        if "file" not in request.data:
            raise ParseError("Empty content")
        file_obj = request.data["file"]
        etree_obj_list = {}
        error_log_list = []

        with open(
            str(FARES_SCHEMA),
            "r",
        ) as f:
            schema = f.read()

        if schema is not None:
            lxml_schema = self.get_lxml_schema(schema)

        etree_obj_list = file_to_etree(file_obj)

        if etree_obj_list:
            for xmlschema_doc in etree_obj_list:
                try:
                    fares_validator = fares_validation.get_fares_validator()
                    violations = fares_validator.get_violations(
                        file_obj, pk1
                    )  # Not plugged to API response
                    print("Violations>>>>", violations)

                    lxml_schema.assertValid(etree_obj_list[xmlschema_doc])
                except etree.DocumentInvalid:
                    error_log_list = list(lxml_schema.error_log)
                    for error in error_log_list:
                        fares_validator_model_object = FaresValidation(
                            dataset_id=pk2,
                            organisation_id=pk1,
                            file_name=xmlschema_doc,
                            error_line_no=error.line,
                            error=error.message,
                            type_of_observation=type_of_observation,
                            category=category,
                        )
                        fares_validator_model_object.save()

            validations = FaresValidation.objects.filter(
                dataset_id=pk2, organisation_id=pk1
            )
            serializer = FaresSerializer(validations, many=True)
            if error_log_list:
                return JsonResponse(
                    serializer.data, safe=False, status=status.HTTP_201_CREATED
                )
            return JsonResponse({}, status=status.HTTP_200_OK)

        else:
            return JsonResponse({}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def get_lxml_schema(self, schema):
        """Creates an lxml XMLSchema object from a file"""

        if schema is None:
            return

        if not isinstance(schema, etree.XMLSchema):
            logger.info(f"[XML] => Parsing {schema}.")
            root = etree.parse(str(FARES_SCHEMA))
            schema = etree.XMLSchema(root)
        return schema
