import openpyxl
from django.http import HttpResponse
from rest_framework.views import APIView

from ..models import FaresValidation

FARES_VALIDATOR_REPORT_COLUMNS = {
    "file_name": "File Name",
    "error_line_no": "Line Number",
    "type_of_observation": "Type of Observation",
    "category": "Category",
    "error": "Details",
    "reference": "Reference",
    "important_note": "Important Note",
}
REPORT_SHEET_TITLE = "Warnings"


class FaresXmlExporter(APIView):
    def get(self, request, pk1, pk2):
        fares_validator_report_name = f"BODS_fares_validation_{pk1}_{pk2}.xlsx"
        response = HttpResponse(content_type="application/ms-excel")
        response[
            "Content-Disposition"
        ] = f'attachment; filename="{fares_validator_report_name}"'

        validations = FaresValidation.objects.filter(
            dataset_id=pk2, organisation_id=pk1
        ).values_list(
            "file_name",
            "error_line_no",
            "type_of_observation",
            "category",
            "error",
            "reference",
            "important_note",
        )

        wb = openpyxl.Workbook()
        ws = wb["Sheet"]
        ws.title = REPORT_SHEET_TITLE

        row_num = 0
        columns = list(FARES_VALIDATOR_REPORT_COLUMNS.values())
        ws.append(columns)
        for row in validations:
            row_num = row_num + 1
            ws.append(row)

        wb.save(response)
        return response
