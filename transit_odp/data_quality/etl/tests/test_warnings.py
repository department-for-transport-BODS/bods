import json
from pathlib import Path

import pytest
from django.contrib.gis.geos import LineString

from transit_odp.data_quality.dataclasses import Report
from transit_odp.data_quality.etl.warnings import (
    ServiceLinkMissingStopsETL,
)
from transit_odp.data_quality.factories.transmodel import DataQualityReportFactory
from transit_odp.data_quality.models import ServiceLink
from transit_odp.data_quality.models.warnings import (
    ServiceLinkMissingStopWarning,
)
from transit_odp.data_quality.tasks import run_dqs_report_etl_pipeline
from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.pipelines.factories import DataQualityTaskFactory
from transit_odp.pipelines.pipelines.dqs_report_etl import extract, transform_model
from transit_odp.users.constants import AgentUserType

DATA_DIR = Path(__file__).parent.joinpath("data")
TXCFILE = str(DATA_DIR.joinpath("ea_20-1A-A-y08-1.xml"))


pytestmark = pytest.mark.django_db


# def test_notify_on_dqs_completion(mailoutbox):
#     reportfile = DATA_DIR / "journey-partial-timing-overlap.json"
#     dq_report = DataQualityReportFactory(
#         file__from_path=reportfile,
#         revision__upload_file__from_path=TXCFILE,
#     )
#     DataQualityTaskFactory(report=dq_report)
#     run_dqs_report_etl_pipeline(dq_report.id)
#     mail = mailoutbox[0]
#     expected_subject = (
#         "Action required – PTI validation report requires resolution (if applicable)"
#     )
#     assert mail.subject == expected_subject
#     assert mail.to[0] == dq_report.revision.dataset.contact.email


# def test_notify_agent_on_dqs_completion(mailoutbox):
#     revision = DatasetRevisionFactory(
#         dataset__contact__email="agent@agentyagent.com",
#         dataset__contact__account_type=AgentUserType,
#         upload_file__from_path=TXCFILE,
#     )
#     reportfile = DATA_DIR / "journey-partial-timing-overlap.json"
#     dq_report = DataQualityReportFactory(
#         file__from_path=reportfile,
#         revision=revision,
#     )
#     DataQualityTaskFactory(report=dq_report)
#     run_dqs_report_etl_pipeline(dq_report.id)
#     mail = mailoutbox[0]
#     expected_subject = (
#         "Action required – PTI validation report requires resolution (if applicable)"
#     )
#     assert mail.subject == expected_subject
#     assert mail.to[0] == "agent@agentyagent.com"
#     assert revision.dataset.organisation.name in mail.body


def test_run_service_link_missing_stops_pipeline():
    reportfile = DATA_DIR / "service-link-missing-stops.json"
    dq_report = DataQualityReportFactory(
        file__from_path=reportfile,
        revision__upload_file__from_path=TXCFILE,
    )

    # use old pipeline to add the features to the transmodel tables
    extracted = extract.run(dq_report.id)
    transform_model.run(extracted)

    report = Report(dq_report.file)
    pipeline = ServiceLinkMissingStopsETL(
        report_id=dq_report.id, warnings=report.warnings
    )
    pipeline.load()

    warnings = ServiceLinkMissingStopWarning.objects.all()
    assert len(warnings) == 1

    warning = warnings[0]
    assert warning.report == dq_report
    assert warning.service_link.ito_id == "SL005b3c9d9ce8c688040ba4ee6baae14502b9d623"
    assert warning.service_link.geometry == LineString(
        [
            [0.137484664171875576, 52.1940786889398183],
            [-0.249862338202943901, 52.5745735187174859],
        ],
        srid=4326,
    )

    # Check the m2m associations have been created
    assert set(warning.stops.values_list("ito_id", flat=True)) == {"ST9100ELYY"}

    # Check that the ServicePatterns are available
    with dq_report.file.open("r") as fin:
        data = json.load(fin)["warnings"][0]
        data["warning_type"].replace("-", "_")
        warning_json = data["values"][0]
    service_patterns_in = warning_json["service_patterns"]

    sl = ServiceLink.objects.get(id=warning.service_link_id)
    service_patterns = sl.service_patterns.all()
    assert set(sp.ito_id for sp in service_patterns) == set(service_patterns_in)
