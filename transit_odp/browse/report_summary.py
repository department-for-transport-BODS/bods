from transit_odp.dqs.models import  ObservationResults
import pandas as pd
from django.db.models import F




class ReportSummary:
    def __init__(self, report_id) -> None:
        self.report_id = report_id

    def get_dataframe_report(self):
        columns = ["importance","category", "observation","service_code", "details", "line_name", "vehicle_journey_id"]
        data = (
            ObservationResults.objects.filter(
            taskresults__dataquality_report_id=19
            )
            .annotate(
            details_annotation=F("details"),
            dd_vehicle_journey_id=F("vehicle_journey_id"),
            importance=F("taskresults__checks__importance"),
            category=F("taskresults__checks__category"),
            observation=F("taskresults__checks__observation"),
            service_code=F("taskresults__transmodel_txcfileattributes__service_code"),
            line_name=F("taskresults__transmodel_txcfileattributes__service_txcfileattributes__name")
            )
            .values(*columns)
        )
        print("data2: ", data.query)
        print(data)
        df = pd.DataFrame(data)
        print(df)
        return df
        

    def get_summary(self) -> dict:
        data = f"this should be a dataframe based on the {self.report_id}"
        self.report_id = 19
        return self.get_dataframe_report()