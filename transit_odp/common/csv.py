import csv
import io
import logging
import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from typing import Union

logger = logging.getLogger(__name__)


@dataclass
class CSVColumn:
    header: str
    accessor: Union[str, Callable]


class CSVBuilder:
    columns = None
    queryset = None

    def count(self):
        if self.queryset is None:
            self.queryset = self.get_queryset()
        return self.queryset.count()

    def get_queryset(self):
        raise NotImplementedError

    def _create_row(self, obj):
        values = []
        for column in self.columns:
            if callable(column.accessor):
                value = column.accessor(obj)
            else:
                value = getattr(obj, column.accessor, None)

            # csv.writer doesn't use isoformat strings for datetimes when writing
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            values.append(value)

        return values

    def to_string(self):
        """
        Creates a string representation of a Django model.
        """

        if self.queryset is None:
            self.queryset = self.get_queryset()

        classname = self.__class__.__name__
        prefix = f"CSVExporter - to_string - {classname} - "
        headers = [column.header for column in self.columns]

        rows = [self._create_row(q) for q in self.queryset]
        row_count = len(rows)
        csvfile = io.StringIO()
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        logger.info(prefix + f"Writing {row_count} rows to StringIO file.")

        writer.writerow(headers)
        writer.writerows(rows)

        csvfile.seek(0, os.SEEK_END)
        size = csvfile.tell()
        logger.info(prefix + f"Final file size of {size} bytes.")
        csvfile.seek(0)

        output = csvfile.getvalue()
        csvfile.close()
        logger.info(prefix + "File successfully closed")
        return output

    def to_temporary_file(self):
        """
        Creates a csv file using a temporary file.

        N.B. it is the callers responsiblity for calling close on file returned.
        """
        if self.queryset is None:
            self.queryset = self.get_queryset()

        classname = self.__class__.__name__
        prefix = f"CSVExporter - to_temporary_file - {classname} - "

        headers = [column.header for column in self.columns]
        csvfile = tempfile.NamedTemporaryFile(mode="w")
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)

        logger.info(prefix + f"Writing rows to NamedTemporaryFile {csvfile.name}.")
        writer.writerow(headers)
        for row in self.queryset.iterator():
            writer.writerow(self._create_row(row))

        csvfile.seek(0, os.SEEK_END)
        size = csvfile.tell()
        logger.info(prefix + f"Final file size of {size} bytes.")
        csvfile.seek(0)
        return csvfile
