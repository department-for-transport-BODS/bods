import io
import zipfile
from typing import List

import pandas as pd

from transit_odp.data_quality.pti.models import Violation

UTF8 = "utf-8"

PTI_CSV_COLUMNS = {
    "filename": "Filename",
    "line": "XML Line Number",
    "name": "XML Element",
    "observation_category": "Category",
    "observation_details": "Details",
    "reference": "Reference",
    "note": "Important Note",
}
PTI_SUMMARY_COLUMNS = {
    "observation_number": "Check ID",
    "count": "Number of Occurrences",
    "name": "XML Element",
    "observation_category": "Category",
    "observation_details": "Details",
    "reference": "Reference",
}


class PTIReport:
    def __init__(self, filename_ending: str, violations: List[Violation]):
        self.pti_report_filename = f"BODS_TXC_validation_{filename_ending}"
        self.pti_summary_filename = f"BODS_TXC_validation_summary_{filename_ending}"
        self._dataframe = pd.DataFrame(
            [violation.to_pandas_dict() for violation in violations]
        )
        self.csv_columns = PTI_CSV_COLUMNS
        self.summary_columns = PTI_SUMMARY_COLUMNS

    def get_pti_report(self) -> str:
        if self._dataframe.empty:
            return ""

        report = self._dataframe[PTI_CSV_COLUMNS.keys()]
        report = report.rename(columns=PTI_CSV_COLUMNS)
        return report.to_csv(index=False)

    def get_pti_summary_report(self) -> str:
        if self._dataframe.empty:
            return ""

        summary_keys = list(PTI_SUMMARY_COLUMNS.keys())
        no_count = summary_keys[:1] + summary_keys[2:]
        summary = self._dataframe[no_count]
        summary = summary.groupby(no_count, as_index=False).agg(
            count=pd.NamedAgg(column="name", aggfunc="count")
        )
        summary = summary[summary_keys].rename(columns=PTI_SUMMARY_COLUMNS)
        return summary.to_csv(index=False)

    def to_zip_as_bytes(self):
        bytesio = io.BytesIO()
        with zipfile.ZipFile(bytesio, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(self.pti_report_filename, self.get_pti_report())
            archive.writestr(self.pti_summary_filename, self.get_pti_summary_report())
        return bytesio
