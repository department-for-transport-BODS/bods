from transit_odp.data_quality.dataclasses import Model
from transit_odp.data_quality.models.transmodel import Service


class DQModelPipeline:
    def __init__(self, report_id: int, model: Model):
        self.report_id = report_id
        self._model = model

    def load_lines(self) -> None:
        """
        Loads the lines from the DQS model into the data quality transmodel Service
        table.
        """
        ThroughModel = Service.reports.through
        services = [Service.from_line(line) for line in self._model.lines]
        Service.objects.bulk_create(services, ignore_conflicts=True)

        ito_ids = [line.id for line in self._model.lines]
        services = Service.objects.filter(ito_id__in=ito_ids)
        throughs = [
            ThroughModel(dataqualityreport_id=self.report_id, service_id=s.id)
            for s in services
        ]
        ThroughModel.objects.bulk_create(throughs, ignore_conflicts=True)

    def load(self):
        self.load_lines()
