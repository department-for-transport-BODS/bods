from django.http import JsonResponse
from rest_framework.exceptions import ParseError
from ..models import FaresValidation
from ..serializers import FaresSerializer
from rest_framework import status
from rest_framework.views import APIView
from lxml import etree
import logging
from rest_framework.parsers import FileUploadParser


logger = logging.getLogger(__name__)
type_of_observation = 'Simple fares validation failure'
category= '' # Itr2 To be extratced from the xml path


class FaresXmlValidator(APIView):
    parser_classes = [FileUploadParser]

    def get(self, request, pk1, pk2):
        validations = FaresValidation.objects.filter(dataset_id = pk2, organisation_id = pk1)
        serializer = FaresSerializer(validations, many=True)
        return JsonResponse({'errors':serializer.data}, safe=False)
    
    def post(self, request, pk1, pk2, format = None):
        if 'file' not in request.data:
            raise ParseError("Empty content")
        file_obj = request.data['file']
        file_name = file_obj
        
        with open('transit_odp/fares_validator/xml_schema/netex_dataObjectRequest_service.xsd', 'r') as f:
            schema = f.read()

        if schema is not None:
            lxml_schema = self.get_lxml_schema(schema)
            xmlschema_doc = etree.parse(file_obj)

        try:
            lxml_schema.assertValid(xmlschema_doc)
        except etree.DocumentInvalid:
            print("Validation error(s):")
            for error in lxml_schema.error_log:
                print("  Line {}: {}".format(error.line, error.message))
                b1 = FaresValidation(dataset_id = pk2, organisation_id = pk1, file_name=file_name, error_line_no = error.line, error=error.message, type_of_observation = type_of_observation, category = category)
                b1.save()

        validations = FaresValidation.objects.filter(dataset_id = pk2)
        serializer = FaresSerializer(validations, many=True)
        return JsonResponse({'errors': serializer.data}, status= status.HTTP_201_CREATED)


    def get_lxml_schema(self, schema):
        """Creates an lxml XMLSchema object from a file, file path or url."""

        if schema is None:
            return

        if not isinstance(schema, etree.XMLSchema):
            logger.info(f"[XML] => Parsing {schema}.")
            root = etree.parse('transit_odp/fares_validator/xml_schema/netex_dataObjectRequest_service.xsd')
            schema = etree.XMLSchema(root)
        return schema