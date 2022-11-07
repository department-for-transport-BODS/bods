from io import BytesIO
from typing import List

import openpyxl
from rest_framework.views import APIView

from transit_odp.fares_validator.types import Violation

from ..models import FaresValidation, FaresValidationResult

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
    def __init__(
        self,
        revision_id: int,
        org_id: int,
        fares_validator_report_name: str,
        violations: List[Violation],
    ):
        self.fares_validator_report_name = fares_validator_report_name
        self.xlsx_columns = list(FARES_VALIDATOR_REPORT_COLUMNS.values())
        self.revision_id = revision_id
        self.org_id = org_id

    def get_fares_validator_report(self) -> str:
        validations = FaresValidation.objects.filter(
            revision_id=self.revision_id, organisation_id=self.org_id
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
        ws.append(self.xlsx_columns)
        for row in validations:
            row_num = row_num + 1
            ws.append(row)

        wb.save(self.fares_validator_report_name)
        return BytesIO(wb.read())

    def get(self, request, pk1, pk2):
        validation_result = FaresValidationResult.objects.filter(revision_id=pk1)
        return validation_result.to_http_response()
