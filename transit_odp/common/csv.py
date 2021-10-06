import csv
import io
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from typing import Union


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
        if self.queryset is None:
            self.queryset = self.get_queryset()

        headers = [column.header for column in self.columns]
        rows = [self._create_row(q) for q in self.queryset]

        csvfile = io.StringIO()
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)

        writer.writerow(headers)
        writer.writerows(rows)

        output = csvfile.getvalue()
        csvfile.close()
        return output

    def to_temporary_file(self):
        """
        Creates a csv file using a temporary file.

        N.B. it is the callers responsiblity for calling close on file returned.
        """
        if self.queryset is None:
            self.queryset = self.get_queryset()

        headers = [column.header for column in self.columns]
        csvfile = tempfile.NamedTemporaryFile(mode="w")
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        writer.writerow(headers)
        for row in self.queryset.iterator():
            writer.writerow(self._create_row(row))

        csvfile.seek(0)
        return csvfile
