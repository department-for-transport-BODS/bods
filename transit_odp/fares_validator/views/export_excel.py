from django.http import HttpResponse
import openpyxl
from ..models import FaresValidation
from ..serializers import FaresSerializer
from rest_framework.views import APIView
import logging


logger = logging.getLogger(__name__)

class FaresXmlExporter(APIView):

    def get(self, request, pk1, pk2):       
        response = HttpResponse(content_type = 'application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="errors.xlsx"'

        validations = FaresValidation.objects.filter(dataset_id = pk2, organisation_id = pk1).values_list('file_name', 'error_line_no', 'type_of_observation', 'category', 'error', 'reference', 'important_note')

        wb = openpyxl.Workbook()
        ws = wb['Sheet']
        ws.title = 'Warnings'
 
        row_num = 0
        columns = ['File name', 'Line_no', 'Type of observation', 'Category', 'Details', 'Reference', 'important_note'] # Itr 2 To remove hardcoding of the column names
        ws.append(columns)
        for row in validations:
            row_num = row_num + 1
            ws.append(row)
        
        wb.save(response)
        return response
    