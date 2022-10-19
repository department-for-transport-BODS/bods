import logging

from django.http import JsonResponse
from lxml import etree
from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.parsers import FileUploadParser
from rest_framework.views import APIView

from transit_odp.fares_validator.utils.files_parser import file_to_etree

from ..models import FaresValidation
from ..serializers import FaresSerializer

logger = logging.getLogger(__name__)
type_of_observation = "Simple fares validation failure"
category = ""  # Itr2 To be extratced from the xml path
schema_path = (
    "transit_odp/fares_validator/xml_schema/netex_dataObjectRequest_service.xsd"
)


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
        # if "file" not in self.file:
        #     raise ParseError("Empty content")
        file_obj = self.file
        etree_obj_list = {}

        with open(
            schema_path,
            "r",
        ) as f:
            schema = f.read()

        if schema is not None:
            lxml_schema = self.get_lxml_schema(schema)

        etree_obj_list = file_to_etree(file_obj)

        if etree_obj_list:
            for xmlschema_doc in etree_obj_list:
                try:
                    lxml_schema.assertValid(etree_obj_list[xmlschema_doc])
                except etree.DocumentInvalid:
                    for error in lxml_schema.error_log:
                        fares_validator_model_object = FaresValidation(
                            dataset_id=self.pk2,
                            organisation_id=self.pk1,
                            file_name=xmlschema_doc,
                            error_line_no=error.line,
                            error=error.message,
                            type_of_observation=type_of_observation,
                            category=category,
                        )
                        fares_validator_model_object.save()
                        validations = FaresValidation.objects.filter(dataset_id=self.pk2)
                        serializer = FaresSerializer(validations, many=True)
                        return JsonResponse(
                            serializer.data, safe=False, status=status.HTTP_201_CREATED
                        )

                return JsonResponse(status=status.HTTP_200_OK)

        else:
            return JsonResponse({}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def get_lxml_schema(self, schema):
        """Creates an lxml XMLSchema object from a file, file path or url."""

        if schema is None:
            return

        if not isinstance(schema, etree.XMLSchema):
            logger.info(f"[XML] => Parsing {schema}.")
            root = etree.parse(schema_path)
            schema = etree.XMLSchema(root)
        return schema
