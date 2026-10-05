import datetime

import pytest
from django_hosts import reverse

from config.hosts import DATA_HOST, PUBLISH_HOST
from transit_odp.dqs.constants import Checks, Level
from transit_odp.dqs.factories import (
    ChecksFactory,
    ObservationResultsFactory,
    ReportFactory,
    TaskResultsFactory,
)
from transit_odp.naptan.factories import StopPointFactory
from transit_odp.organisation.constants import TimetableType
from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetRevisionFactory,
    TXCFileAttributesFactory,
)
from transit_odp.transmodel.factories import (
    ServiceFactory,
    ServicePatternFactory,
    ServicePatternStopFactory,
    VehicleJourneyFactory,
)
from transit_odp.transmodel.models import BookingArrangements, OperatingProfile
from transit_odp.users.constants import OrgAdminType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db

SERVICE_CODE = "PB0000001:1"
LINE_NAME = "42"
DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
TODAY = datetime.date.today()


def build_line(revision, journeys=2, stops=3, service_type="standard"):
    txc = TXCFileAttributesFactory(
        revision=revision,
        service_code=SERVICE_CODE,
        line_names=[LINE_NAME],
        filename="line-42.xml",
        revision_number=0,
        operating_period_start_date=TODAY - datetime.timedelta(days=30),
        operating_period_end_date=TODAY + datetime.timedelta(days=30),
    )
    service = ServiceFactory(
        revision=revision,
        txcfileattributes=txc,
        service_code=SERVICE_CODE,
        name=LINE_NAME,
        service_type=service_type,
        start_date=TODAY - datetime.timedelta(days=30),
        end_date=None,
    )
    pattern = ServicePatternFactory(
        revision=revision, line_name=LINE_NAME, description="Town - Station"
    )
    service.service_patterns.add(pattern)
    stop_points = [
        StopPointFactory(
            common_name=f"Stop {index}",
            street=f"Street {index}",
            indicator="Stand A",
            stop_type="BCT",
        )
        for index in range(stops)
    ]
    pattern_stops = []
    for journey in range(journeys):
        vehicle_journey = VehicleJourneyFactory(
            service_pattern=pattern,
            journey_code=f"VJ{journey:02d}",
            direction="outbound",
            start_time=datetime.time(6, journey),
            departure_day_shift=False,
        )
        for day in DAYS:
            OperatingProfile.objects.create(
                vehicle_journey=vehicle_journey, day_of_week=day
            )
        for sequence, stop_point in enumerate(stop_points):
            pattern_stops.append(
                ServicePatternStopFactory(
                    service_pattern=pattern,
                    naptan_stop=stop_point,
                    atco_code=stop_point.atco_code,
                    sequence_number=sequence,
                    departure_time=datetime.time(6 + sequence, journey),
                    vehicle_journey=vehicle_journey,
                )
            )
    return service, txc, pattern_stops


def add_observation(revision, txc, pattern_stop, title):
    report = ReportFactory(revision=revision)
    task = TaskResultsFactory(
        dataquality_report=report,
        transmodel_txcfileattributes=txc,
        checks=ChecksFactory(observation=title, importance=Level.critical.value),
    )
    ObservationResultsFactory(
        taskresults=task,
        service_pattern_stop=pattern_stop,
        vehicle_journey=pattern_stop.vehicle_journey,
    )


@pytest.fixture
def publish_context(client_factory):
    user = UserFactory(account_type=OrgAdminType)
    revision = DatasetRevisionFactory(
        dataset__organisation=user.organisations.first(),
        dataset__dataset_type=TimetableType,
        is_published=False,
        name="Draft revision",
    )
    client = client_factory(host=PUBLISH_HOST)
    client.force_login(user)
    return client, revision


def publish_url(revision, **params):
    url = reverse(
        "nextjs-timetables-line-detail",
        host=PUBLISH_HOST,
        kwargs={"pk1": revision.dataset.organisation_id, "pk": revision.dataset_id},
    )
    query = {"line": LINE_NAME, "service": SERVICE_CODE, "revision_id": revision.id}
    query.update(params)
    return url, query


def data_url(dataset, **params):
    url = reverse(
        "api:browser-timetable-line-detail", host=DATA_HOST, kwargs={"pk": dataset.id}
    )
    query = {"line": LINE_NAME, "service": SERVICE_CODE}
    query.update(params)
    return url, query


def test_publish_requires_login(client_factory, publish_context):
    _, revision = publish_context
    url, query = publish_url(revision)
    response = client_factory(host=PUBLISH_HOST).get(url, query)
    assert response.status_code == 401


def test_publish_revision_must_belong_to_dataset_and_org(publish_context):
    client, revision = publish_context
    other_revision = DatasetRevisionFactory(dataset__dataset_type=TimetableType)
    url, query = publish_url(revision, revision_id=other_revision.id)
    response = client.get(url, query)
    assert response.status_code == 404


def test_publish_returns_line_properties_without_timetable_by_default(
    publish_context,
):
    client, revision = publish_context
    build_line(revision)
    url, query = publish_url(revision)

    data = client.get(url, query).json()

    assert data["feedName"] == "Draft revision"
    assert data["lineName"] == LINE_NAME
    assert data["serviceCode"] == SERVICE_CODE
    assert data["serviceType"] == "Standard"
    assert [file["filename"] for file in data["currentValidFiles"]] == ["line-42.xml"]
    assert data["currentValidFiles"][0]["startDate"]
    assert data["bookingMethods"] is None
    assert data["timetable"] is None


def test_publish_timetable_serialises_rows_and_cells(publish_context):
    client, revision = publish_context
    build_line(revision, journeys=2, stops=3)
    url, query = publish_url(revision, includeTimetable="true", date=TODAY.isoformat())

    timetable = client.get(url, query).json()["timetable"]

    assert timetable["currDate"] == TODAY.isoformat()
    assert timetable["isTimetableInfoAvailable"] is True
    outbound, inbound = timetable["directions"]
    assert outbound["journeyName"] == "Outbound - Town - Station"
    assert [column["name"] for column in outbound["columns"]] == [
        "Journey Code",
        "VJ00",
        "VJ01",
    ]
    assert [row["stop"]["name"] for row in outbound["rows"]] == [
        "Stop 0",
        "Stop 1",
        "Stop 2",
    ]
    first_row = outbound["rows"][0]
    assert first_row["stop"]["street"] == "Street 0"
    assert first_row["stop"]["indicator"] == "Stand A"
    assert [cell["departureTime"] for cell in first_row["cells"]] == [
        "06:00",
        "06:01",
    ]
    assert inbound["isEmpty"] is True
    assert inbound["rows"] == []


def test_publish_timetable_pages_columns_and_rows(publish_context):
    client, revision = publish_context
    build_line(revision, journeys=12, stops=12)
    url, query = publish_url(revision, includeTimetable="true", date=TODAY.isoformat())

    outbound = client.get(url, query).json()["timetable"]["directions"][0]
    assert outbound["totalPage"] == 2
    assert outbound["currPage"] == 1
    assert outbound["totalRowCount"] == 12
    assert len(outbound["columns"]) == 11
    assert len(outbound["rows"]) == 10

    query.update({"outboundPage": "2", "showAllOutbound": "true"})
    outbound = client.get(url, query).json()["timetable"]["directions"][0]
    assert outbound["currPage"] == 2
    assert outbound["showAll"] is True
    assert [column["name"] for column in outbound["columns"]] == [
        "Journey Code",
        "VJ10",
        "VJ11",
    ]
    assert len(outbound["rows"]) == 12


def test_publish_timetable_includes_stop_and_cell_observations(publish_context):
    client, revision = publish_context
    _, txc, pattern_stops = build_line(revision, journeys=1, stops=2)
    add_observation(revision, txc, pattern_stops[0], Checks.IncorrectStopType.value)
    add_observation(revision, txc, pattern_stops[1], Checks.LastStopIsPickUpOnly.value)
    url, query = publish_url(revision, includeTimetable="true", date=TODAY.isoformat())

    outbound = client.get(url, query).json()["timetable"]["directions"][0]

    first_stop, last_stop = outbound["rows"]
    assert first_stop["stop"]["observation"]["title"] == "Incorrect stop type"
    assert first_stop["stop"]["stopType"] == "BCT"
    assert first_stop["cells"][0]["observations"] == []
    assert last_stop["stop"]["observation"] is None
    assert [o["title"] for o in last_stop["cells"][0]["observations"]] == [
        "Last stop is pick up only"
    ]


def test_publish_booking_methods_follow_django_template_mapping(publish_context):
    client, revision = publish_context
    service, _, _ = build_line(revision, service_type="flexible")
    BookingArrangements.objects.create(
        service=service,
        description="Call ahead",
        email=None,
        phone_number="0123",
        web_address="https://book.example.com",
    )
    url, query = publish_url(revision)

    data = client.get(url, query).json()

    assert data["serviceType"] == "Flexible"
    assert data["bookingArrangements"] == "Call ahead"
    # Django prints Email from index 0 gated on index 2, and URL from index 2
    # gated on index 0, so a missing email shows "Email - None" and hides URL.
    assert data["bookingMethods"] == {
        "phone": "0123",
        "email": "None",
        "url": None,
    }


def test_data_line_detail_is_public_and_uses_live_revision(client_factory):
    dataset = DatasetFactory(dataset_type=TimetableType)
    build_line(dataset.live_revision)
    url, query = data_url(dataset, includeTimetable="true", date=TODAY.isoformat())

    response = client_factory(host=DATA_HOST).get(url, query)

    assert response.status_code == 200
    data = response.json()
    assert data["datasetId"] == dataset.id
    assert data["datasetName"] == dataset.live_revision.name
    assert data["revisionId"] == dataset.live_revision_id
    assert data["serviceType"] == "Standard"
    assert data["timetable"]["isTimetableInfoAvailable"] is True


def test_data_line_detail_404s_for_unpublished_dataset(client_factory):
    revision = DatasetRevisionFactory(
        dataset__dataset_type=TimetableType, is_published=False
    )
    url, query = data_url(revision.dataset)

    response = client_factory(host=DATA_HOST).get(url, query)

    assert response.status_code == 404
