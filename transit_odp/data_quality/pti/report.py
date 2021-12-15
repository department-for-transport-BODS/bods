import csv
import io
import zipfile

from transit_odp.data_quality.pti.models import Violation

UTF8 = "utf-8"

PTI_CSV_COLUMNS = (
    "Filename",
    "XML Line Number",
    "XML Element",
    "Category",
    "Details",
    "Reference",
    "Important Note",
)


class PTIReport:
    def __init__(self, filename: str):
        self.filename = filename
        self.columns = PTI_CSV_COLUMNS
        self._csvfile = io.StringIO()
        self.writer = csv.writer(self._csvfile, quoting=csv.QUOTE_ALL)
        self.writer.writerow(self.columns)

    def write_violation(self, violation: Violation):
        self.writer.writerow(violation.to_bods_csv())

    def to_zip_as_bytes(self):
        bytesio = io.BytesIO()
        with zipfile.ZipFile(bytesio, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(self.filename, self._csvfile.getvalue())
        return bytesio
