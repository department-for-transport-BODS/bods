import csv
import io
from typing import List

from django.db.models.expressions import Value
from django.db.models.fields import CharField

from transit_odp.data_quality.constants import Observation


class ObservationCSV:
    def __init__(self, report_id, observations: List[Observation]):
        self._report_id = report_id
        self._observation_types = observations

    def to_csv(self):
        string_ = io.StringIO()
        writer = csv.writer(string_, quoting=csv.QUOTE_ALL)
        writer.writerow(["Importance", "Line", "Observation", "Detail"])

        observations = [o for o in self._observation_types if o.model]
        for o in observations:
            rows = self.get_rows(o)
            writer.writerows(rows)

        string_.seek(0)
        return string_

    def get_rows(self, observation: Observation):
        qs = observation.model.objects.filter(report_id=self._report_id)

        if hasattr(qs, "get_csv_queryset"):
            qs = qs.get_csv_queryset()

        qs = qs.annotate(
            importance=Value(observation.level.value, output_field=CharField()),
            observation=Value(observation.title, output_field=CharField()),
        )

        if hasattr(qs, "add_line"):
            qs = qs.add_line()
        else:
            qs = qs.annotate(line=Value("", output_field=CharField()))

        if hasattr(qs, "add_message"):
            qs = qs.add_message()
        else:
            qs = qs.annotate(message=Value("", output_field=CharField()))

        return list(qs.values_list("importance", "line", "observation", "message"))
