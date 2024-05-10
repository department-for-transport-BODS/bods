import pandas as pd
import pytest
from transit_odp.browse.timetable_visualiser import TimetableVisualiser
from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.transmodel.factories import ServiceFactory, ServicePatternFactory, ServiceServicePatternFactory
from transit_odp.transmodel.models import Service, ServicePattern
pytestmark = pytest.mark.django_db

def test_review_page():
    df = pd.read_csv('base.csv')

    revision = DatasetRevisionFactory(id=df.iloc[0]['revision_id'])
    unique_services = df['service_code'].unique()
    service_instances = {}
    for service in unique_services:
        df_service = df[df['service_code'] == service].iloc[0]
        service_instance = ServiceFactory(service_code=df_service['service_code'], revision=revision, name=df_service['name'], start_date=df_service['start_date'], end_date=df_service['end_date'])
        service_instances[service] = service_instance

    unique_lines = df['line_name'].unique()
    for line in unique_lines:
        df_service_pattern = df[df["line_name"] == line].iloc[0]
        sp_instance = ServicePatternFactory(line_name=line, destination=df_service_pattern['destination'], origin=df_service_pattern['origin'], description=df_service_pattern['description'])
        ServiceServicePatternFactory(service=service_instances[df_service_pattern['service_code']], servicepattern=sp_instance)


    TimetableVisualiser.test_pytest()