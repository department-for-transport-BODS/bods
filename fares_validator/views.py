from django.http import JsonResponse
from .models import FaresValidation
from .serializers import FaresSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from lxml import etree
import logging


logger = logging.getLogger(__name__)

def FaresXmlValidator(request, pk1):

    with open('fares_validator/xml_schema/fares.xml', 'r') as f:
        source  = f.read()
    
    with open('fares_validator/xml_schema/netex_dataObjectRequest_service.xsd', 'r') as f:
        schema = f.read()

    path_xml = 'fares_validator/xml_schema/fares.xml'

    if schema is not None:
        lxml_schema = get_lxml_schema(schema)
        xmlschema_doc = etree.parse(path_xml)

    # Use the parser if you want to raise etree.XMLSyntaxError on first validation fail

    # parser = etree.XMLParser(schema=lxml_schema)

    try:
        lxml_schema.assertValid(xmlschema_doc)
    except etree.DocumentInvalid:
        print("Validation error(s):")
        for error in lxml_schema.error_log:
            print("  Line {}: {}".format(error.line, error.message))
            b1 = FaresValidation(file_name='fares.xml', error=error.message)
            b1.save()

    validations = FaresValidation.objects.all()
    serializer = FaresSerializer(validations, many=True)
    return JsonResponse({'errors':serializer.data}, safe=False)


def get_lxml_schema(schema):
    """Creates an lxml XMLSchema object from a file, file path or url."""

    if schema is None:
        return

    if not isinstance(schema, etree.XMLSchema):
        logger.info(f"[XML] => Parsing {schema}.")
        root = etree.parse('fares_validator/xml_schema/netex_dataObjectRequest_service.xsd')
        schema = etree.XMLSchema(root)
    return schema