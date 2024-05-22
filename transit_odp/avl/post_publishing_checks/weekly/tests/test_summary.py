from datetime import date, timedelta
from unittest.mock import Mock, patch

import pytest

from transit_odp.avl.models import PostPublishingCheckReport
from transit_odp.avl.post_publishing_checks.weekly.summary import (
    PostPublishingChecksSummaryData,
)

"""
All tests in this file checks if the DataFrames are created correctly.
Correctly means the number of columns match keys received in the JSON
received from Daily Reports.
Additionally checks:
    PPC Summary:
        - number of rows is equal to the number of keys in json
        - check if values are aggregated properly
"""


@pytest.fixture()
def ppc_summary_data() -> PostPublishingChecksSummaryData:
    return PostPublishingChecksSummaryData(
        date.today(), date.today() - timedelta(days=7)
    )


@pytest.fixture()
def daily_report_mock() -> PostPublishingCheckReport:
    report = PostPublishingCheckReport(dataset_id=1, created=date.today())
    report.file = Mock()
    report.vehicle_activities_analysed = 0
    report.vehicle_activities_completely_matching = 0
    return report


mock_path_prefix = "transit_odp.avl.post_publishing_checks.weekly.summary."


@patch("json.load")
def test_block_ref(
    json_mock: Mock,
    ppc_summary_data: PostPublishingChecksSummaryData,
    daily_report_mock: PostPublishingCheckReport,
) -> None:
    data = {
        "BlockRef": [
            {
                "SD ResponseTimestamp": "",
                "RecordedAtTime": "",
                "AVL data set name BODS": "",
                "AVL data set ID BODS": "",
                "DatedVehicleJourneyRef in SIRI": "",
                "VehicleRef in SIRI": "",
                "Timetable file name": "",
                "Timetable data set ID BODS": "",
                "DepartureTime in TXC": "",
                "BlockRef in SIRI": "",
                "BlockNumber in TXC": "",
                "SIRI XML line number": "",
                "TransXChange XML line number": "",
                "Error note": "",
            }
        ]
    }

    json_mock.return_value = data

    # Calling with 3x Mock to run loop 3 times.
    result = ppc_summary_data.aggregate_daily_reports(
        daily_reports=[daily_report_mock, daily_report_mock, daily_report_mock]
    )
    df = result.get_block_ref()
    columns = df.columns

    assert df.shape == (3, 14)
    assert columns[0] == "SD ResponseTimestamp"
    assert columns[1] == "RecordedAtTime"
    assert columns[2] == "AVL data set name BODS"
    assert columns[3] == "AVL data set ID BODS"
    assert columns[4] == "DatedVehicleJourneyRef in SIRI"
    assert columns[5] == "VehicleRef in SIRI"
    assert columns[6] == "Timetable file name"
    assert columns[7] == "Timetable data set ID BODS"
    assert columns[8] == "DepartureTime in TXC"
    assert columns[9] == "BlockRef in SIRI"
    assert columns[10] == "BlockNumber in TXC"
    assert columns[11] == "SIRI XML line number"
    assert columns[12] == "TransXChange XML line number"
    assert columns[13] == "Error note"


@patch("json.load")
def test_origin_ref(
    json_mock: Mock,
    ppc_summary_data: PostPublishingChecksSummaryData,
    daily_report_mock: PostPublishingCheckReport,
) -> None:
    data = {
        "OriginRef": [
            {
                "SD ResponseTimestamp": "",
                "RecordedAtTime": "",
                "AVL data set name BODS": "",
                "AVL data set ID BODS": "",
                "DatedVehicleJourneyRef in SIRI": "",
                "VehicleRef in SIRI": "",
                "Timetable file name": "",
                "Timetable data set ID BODS": "",
                "DepartureTime in TXC": "",
                "OriginRef in SIRI": "",
                "StopPointRef in TxC": "",
                "SIRI XML line number": "",
                "TransXChange XML line number": "",
                "Error note": "",
            }
        ]
    }

    json_mock.return_value = data

    # Calling with 3x Mock to run loop 3 times.
    result = ppc_summary_data.aggregate_daily_reports(
        daily_reports=[daily_report_mock, daily_report_mock, daily_report_mock]
    )
    df = result.get_origin_ref()
    columns = df.columns

    assert df.shape == (3, 14)
    assert columns[0] == "SD ResponseTimestamp"
    assert columns[1] == "RecordedAtTime"
    assert columns[2] == "AVL data set name BODS"
    assert columns[3] == "AVL data set ID BODS"
    assert columns[4] == "DatedVehicleJourneyRef in SIRI"
    assert columns[5] == "VehicleRef in SIRI"
    assert columns[6] == "Timetable file name"
    assert columns[7] == "Timetable data set ID BODS"
    assert columns[8] == "DepartureTime in TXC"
    assert columns[9] == "OriginRef in SIRI"
    assert columns[10] == "StopPointRef in TxC"
    assert columns[11] == "SIRI XML line number"
    assert columns[12] == "TransXChange XML line number"
    assert columns[13] == "Error note"


@patch("json.load")
def test_destination_ref(
    json_mock: Mock,
    ppc_summary_data: PostPublishingChecksSummaryData,
    daily_report_mock: PostPublishingCheckReport,
) -> None:
    data = {
        "DestinationRef": [
            {
                "SD ResponseTimestamp": "",
                "RecordedAtTime": "",
                "AVL data set name BODS": "",
                "AVL data set ID BODS": "",
                "DatedVehicleJourneyRef in SIRI": "",
                "VehicleRef in SIRI": "",
                "Timetable file name": "",
                "Timetable data set ID BODS": "",
                "DepartureTime in TXC": "",
                "DestinationRef in SIRI": "",
                "StopPointRef in TxC": "",
                "SIRI XML line number": "",
                "TransXChange XML line number": "",
                "Error note": "",
            }
        ]
    }

    json_mock.return_value = data

    # Calling with 3x Mock to run loop 3 times.
    result = ppc_summary_data.aggregate_daily_reports(
        daily_reports=[daily_report_mock, daily_report_mock, daily_report_mock]
    )
    df = result.get_destination_ref()
    columns = df.columns

    assert df.shape == (3, 14)
    assert columns[0] == "SD ResponseTimestamp"
    assert columns[1] == "RecordedAtTime"
    assert columns[2] == "AVL data set name BODS"
    assert columns[3] == "AVL data set ID BODS"
    assert columns[4] == "DatedVehicleJourneyRef in SIRI"
    assert columns[5] == "VehicleRef in SIRI"
    assert columns[6] == "Timetable file name"
    assert columns[7] == "Timetable data set ID BODS"
    assert columns[8] == "DepartureTime in TXC"
    assert columns[9] == "DestinationRef in SIRI"
    assert columns[10] == "StopPointRef in TxC"
    assert columns[11] == "SIRI XML line number"
    assert columns[12] == "TransXChange XML line number"
    assert columns[13] == "Error note"


@patch("json.load")
def test_direction_ref(
    json_mock: Mock,
    ppc_summary_data: PostPublishingChecksSummaryData,
    daily_report_mock: PostPublishingCheckReport,
) -> None:
    data = {
        "DirectionRef": [
            {
                "SD ResponseTimestamp": "",
                "RecordedAtTime": "",
                "AVL data set name BODS": "",
                "AVL data set ID BODS": "",
                "DatedVehicleJourneyRef in SIRI": "",
                "VehicleRef in SIRI": "",
                "Timetable file name": "",
                "Timetable data set ID BODS": "",
                "DepartureTime in TXC": "",
                "DirectionRef in SIRI": "",
                "Direction from JourneyPattern in TXC": "",
                "SIRI XML line number": "",
                "TransXChange XML line number": "",
                "Error note": "",
            }
        ]
    }

    json_mock.return_value = data

    # Calling with 3x Mock to run loop 3 times.
    result = ppc_summary_data.aggregate_daily_reports(
        daily_reports=[daily_report_mock, daily_report_mock, daily_report_mock]
    )
    df = result.get_direction_ref()
    columns = df.columns

    assert df.shape == (3, 14)
    assert columns[0] == "SD ResponseTimestamp"
    assert columns[1] == "RecordedAtTime"
    assert columns[2] == "AVL data set name BODS"
    assert columns[3] == "AVL data set ID BODS"
    assert columns[4] == "DatedVehicleJourneyRef in SIRI"
    assert columns[5] == "VehicleRef in SIRI"
    assert columns[6] == "Timetable file name"
    assert columns[7] == "Timetable data set ID BODS"
    assert columns[8] == "DepartureTime in TXC"
    assert columns[9] == "DirectionRef in SIRI"
    assert columns[10] == "Direction from JourneyPattern in TXC"
    assert columns[11] == "SIRI XML line number"
    assert columns[12] == "TransXChange XML line number"
    assert columns[13] == "Error note"


@patch("json.load")
def test_uncounted_vehicles(
    json_mock: Mock,
    ppc_summary_data: PostPublishingChecksSummaryData,
    daily_report_mock: PostPublishingCheckReport,
) -> None:
    data = {
        "UncountedVehicleActivities": [
            {
                "SD ResponseTimestamp": "",
                "AVL data set name BODS": "",
                "AVL data set ID BODS": "",
                "OperatorRef": "",
                "LineRef": "",
                "RecordedAtTime": "",
                "DatedVehicleJourneyRef in SIRI": "",
                "Error note: Reason it could not be analysed against TXC": "",
            },
        ]
    }

    json_mock.return_value = data

    # Calling with 3x Mock to run loop 3 times.
    result = ppc_summary_data.aggregate_daily_reports(
        daily_reports=[daily_report_mock, daily_report_mock, daily_report_mock]
    )
    df = result.get_uncounted_vehicle_activities()
    columns = df.columns

    assert df.shape == (3, 8)
    assert columns[0] == "SD ResponseTimestamp"
    assert columns[1] == "AVL data set name BODS"
    assert columns[2] == "AVL data set ID BODS"
    assert columns[3] == "OperatorRef"
    assert columns[4] == "LineRef"
    assert columns[5] == "RecordedAtTime"
    assert columns[6] == "DatedVehicleJourneyRef in SIRI"
    assert columns[7] == "Error note: Reason it could not be analysed against TXC"


@patch("json.load")
def test_all_siri_analysed(
    json_mock: Mock,
    ppc_summary_data: PostPublishingChecksSummaryData,
    daily_report_mock: PostPublishingCheckReport,
) -> None:
    data = {
        "All SIRI-VM analysed": [
            {
                "Version": "",
                "ResponseTimestamp (ServiceDelivery)": "",
                "ProducerRef": "",
                "ResponseTimestamp (VehicleMonitoringDelivery)": "",
                "RequestMessageRef": "",
                "ValidUntil": "",
                "ShortestPossibleCycle": "",
                "RecordedAtTime": "",
                "ItemIdentifier": "",
                "ValidUntilTime": "",
                "LineRef": "",
                "DirectionRef": "",
                "DataFrameRef": "",
                "DatedVehicleJourneyRef": "",
                "PublishedLineName": "",
                "OperatorRef": "",
                "OriginRef": "",
                "OriginName": "",
                "DestinationRef": "",
                "DestinationName": "",
                "OriginAimedDepartureTime": "",
                "Longitude": "",
                "Latitude": "",
                "Bearing": "",
                "VehicleRef": "",
                "BlockRef": "",
                "DriverRef": "",
            },
        ]
    }

    json_mock.return_value = data

    # Calling with 3x Mock to run loop 3 times.
    result = ppc_summary_data.aggregate_daily_reports(
        daily_reports=[daily_report_mock, daily_report_mock, daily_report_mock]
    )
    df = result.get_siri_message_analysed()
    columns = df.columns

    assert df.shape == (3, 27)
    assert columns[0] == "Version"
    assert columns[1] == "ResponseTimestamp (ServiceDelivery)"
    assert columns[2] == "ProducerRef"
    assert columns[3] == "ResponseTimestamp (VehicleMonitoringDelivery)"
    assert columns[4] == "RequestMessageRef"
    assert columns[5] == "ValidUntil"
    assert columns[6] == "ShortestPossibleCycle"
    assert columns[7] == "RecordedAtTime"
    assert columns[8] == "ItemIdentifier"
    assert columns[9] == "ValidUntilTime"
    assert columns[10] == "LineRef"
    assert columns[11] == "DirectionRef"
    assert columns[12] == "DataFrameRef"
    assert columns[13] == "DatedVehicleJourneyRef"
    assert columns[14] == "PublishedLineName"
    assert columns[15] == "OperatorRef"
    assert columns[16] == "OriginRef"
    assert columns[17] == "OriginName"
    assert columns[18] == "DestinationRef"
    assert columns[19] == "DestinationName"
    assert columns[20] == "OriginAimedDepartureTime"
    assert columns[21] == "Longitude"
    assert columns[22] == "Latitude"
    assert columns[23] == "Bearing"
    assert columns[24] == "VehicleRef"
    assert columns[25] == "BlockRef"
    assert columns[26] == "DriverRef"


@patch("json.load")
def test_ppc_summary(
    json_mock: Mock,
    ppc_summary_data: PostPublishingChecksSummaryData,
    daily_report_mock: PostPublishingCheckReport,
) -> None:
    daily_report_mock.vehicle_activities_completely_matching = 25
    daily_report_mock.vehicle_activities_analysed = 50
    data = [
        {
            "AVLtoTimetable matching summary": [
                {
                    "SIRI field": "BlockRef",
                    "TXC match field": "BlockNumber",
                    "Total vehicleActivities analysed": 185,
                    "Total count of SIRI fields populated": 185,
                    "%populated": "100.0%",
                    "Successful match with TXC": "0",
                    "%match": "0.0%",
                    "Notes": "dummy_1",
                },
                {
                    "SIRI field": "DatedVehicleJourneyRef",
                    "TXC match field": "TicketMachine/JourneyCode",
                    "Total vehicleActivities analysed": 185,
                    "Total count of SIRI fields populated": 185,
                    "%populated": "100.0%",
                    "Successful match with TXC": "0",
                    "%match": "0.0%",
                    "Notes": "dummy_1",
                },
                {
                    "SIRI field": "DestinationRef",
                    "TXC match field": "JourneyPatternTimingLink/To/StopPointRef",
                    "Total vehicleActivities analysed": 185,
                    "Total count of SIRI fields populated": 185,
                    "%populated": "100.0%",
                    "Successful match with TXC": "0",
                    "%match": "0.0%",
                    "Notes": "dummy_1",
                },
                {
                    "SIRI field": "DirectionRef",
                    "TXC match field": "Direction",
                    "Total vehicleActivities analysed": 185,
                    "Total count of SIRI fields populated": 185,
                    "%populated": "100.0%",
                    "Successful match with TXC": "0",
                    "%match": "0.0%",
                    "Notes": "dummy_1",
                },
                {
                    "SIRI field": "LineRef",
                    "TXC match field": "LineName",
                    "Total vehicleActivities analysed": 185,
                    "Total count of SIRI fields populated": 185,
                    "%populated": "100.0%",
                    "Successful match with TXC": "15",
                    "%match": "85.0%",
                    "Notes": "dummy_1",
                },
                {
                    "SIRI field": "OperatorRef",
                    "TXC match field": "NationalOperatorCode",
                    "Total vehicleActivities analysed": 185,
                    "Total count of SIRI fields populated": 185,
                    "%populated": "100.0%",
                    "Successful match with TXC": "0",
                    "%match": "0.0%",
                    "Notes": "dummy_1",
                },
                {
                    "SIRI field": "OriginRef",
                    "TXC match field": "JourneyPatternTimingLink/from/StopPointRef",
                    "Total vehicleActivities analysed": 185,
                    "Total count of SIRI fields populated": 185,
                    "%populated": "100.0%",
                    "Successful match with TXC": "0",
                    "%match": "0.0%",
                    "Notes": "dummy_1",
                },
                {
                    "SIRI field": "PublishedLineName",
                    "TXC match field": "LineName",
                    "Total vehicleActivities analysed": 185,
                    "Total count of SIRI fields populated": 185,
                    "%populated": "100.0%",
                    "Successful match with TXC": "0",
                    "%match": "0.0%",
                    "Notes": "dummy_1",
                },
            ]
        },
        {
            "AVLtoTimetable matching summary": [
                {
                    "SIRI field": "BlockRef",
                    "TXC match field": "BlockNumber",
                    "Total vehicleActivities analysed": 50,
                    "Total count of SIRI fields populated": 30,
                    "%populated": "40.0%",
                    "Successful match with TXC": "20",
                    "%match": "11.0%",
                    "Notes": "dummy_2",
                },
                {
                    "SIRI field": "DatedVehicleJourneyRef",
                    "TXC match field": "TicketMachine/JourneyCode",
                    "Total vehicleActivities analysed": 50,
                    "Total count of SIRI fields populated": 30,
                    "%populated": "40.0%",
                    "Successful match with TXC": "20",
                    "%match": "11.0%",
                    "Notes": "dummy_2",
                },
                {
                    "SIRI field": "DestinationRef",
                    "TXC match field": "JourneyPatternTimingLink/To/StopPointRef",
                    "Total vehicleActivities analysed": 50,
                    "Total count of SIRI fields populated": 30,
                    "%populated": "40.0%",
                    "Successful match with TXC": "20",
                    "%match": "11.0%",
                    "Notes": "dummy_2",
                },
                {
                    "SIRI field": "DirectionRef",
                    "TXC match field": "Direction",
                    "Total vehicleActivities analysed": 50,
                    "Total count of SIRI fields populated": 30,
                    "%populated": "40.0%",
                    "Successful match with TXC": "20",
                    "%match": "11.0%",
                    "Notes": "dummy_2",
                },
                {
                    "SIRI field": "LineRef",
                    "TXC match field": "LineName",
                    "Total vehicleActivities analysed": 50,
                    "Total count of SIRI fields populated": 30,
                    "%populated": "40.0%",
                    "Successful match with TXC": "20",
                    "%match": "11.0%",
                    "Notes": "dummy_2",
                },
                {
                    "SIRI field": "OperatorRef",
                    "TXC match field": "NationalOperatorCode",
                    "Total vehicleActivities analysed": 50,
                    "Total count of SIRI fields populated": 30,
                    "%populated": "40.0%",
                    "Successful match with TXC": "20",
                    "%match": "11.0%",
                    "Notes": "dummy_2",
                },
                {
                    "SIRI field": "OriginRef",
                    "TXC match field": "JourneyPatternTimingLink/from/StopPointRef",
                    "Total vehicleActivities analysed": 50,
                    "Total count of SIRI fields populated": 30,
                    "%populated": "40.0%",
                    "Successful match with TXC": "20",
                    "%match": "11.0%",
                    "Notes": "dummy_2",
                },
                {
                    "SIRI field": "PublishedLineName",
                    "TXC match field": "LineName",
                    "Total vehicleActivities analysed": 50,
                    "Total count of SIRI fields populated": 30,
                    "%populated": "40.0%",
                    "Successful match with TXC": "20",
                    "%match": "11.0%",
                    "Notes": "dummy_2",
                },
            ]
        },
    ]

    json_mock.side_effect = data

    # Calling with 2x Mock to run loop 2 times.
    result = ppc_summary_data.aggregate_daily_reports(
        daily_reports=[daily_report_mock, daily_report_mock]
    )
    df = result.get_summary_report()
    columns = df.columns

    assert df.shape == (8, 8)
    assert columns[0] == "SIRI field"
    assert columns[1] == "TXC match field"
    assert columns[2] == "Total vehicleActivities analysed"
    assert columns[3] == "Total count of SIRI fields populated"
    assert columns[4] == "%populated"
    assert columns[5] == "Successful match with TXC"
    assert columns[6] == "%match"
    assert columns[7] == "Notes"

    # Check order of fields
    assert df.iloc[0]["SIRI field"] == "OperatorRef"
    assert df.iloc[1]["SIRI field"] == "PublishedLineName"
    assert df.iloc[2]["SIRI field"] == "DatedVehicleJourneyRef"
    assert df.iloc[3]["SIRI field"] == "DestinationRef"
    assert df.iloc[4]["SIRI field"] == "OriginRef"
    assert df.iloc[5]["SIRI field"] == "DirectionRef"
    assert df.iloc[6]["SIRI field"] == "BlockRef"

    # Check "LineRef" is not included in the summary
    assert not (df["SIRI field"].str.contains("LineRef").any())

    assert df.iloc[0]["TXC match field"] == "NationalOperatorCode"
    assert df.iloc[0]["Total vehicleActivities analysed"] == 235
    assert df.iloc[0]["Total count of SIRI fields populated"] == 215
    assert df.iloc[0]["%populated"] == str(float(215 * 100 // 235)) + "%"
    assert df.iloc[0]["Successful match with TXC"] == 20
    assert df.iloc[0]["%match"] == str(float(20 * 100 // 235)) + "%"
    assert df.iloc[0]["Notes"] == "dummy_1"

    # All fields complete matching row 2 daily reports aggregated
    # 2 x 50 = 100 for analysed vehicles
    # 2 x 25 = 50 for all fields matching vehicles
    assert df.iloc[1]["Successful match with TXC"] == 20
    assert df.iloc[1]["%match"] == str(float(8)) + "%"


@patch("json.load")
def test_ppc_summary_no_data(
    json_mock: Mock,
    ppc_summary_data: PostPublishingChecksSummaryData,
    daily_report_mock: PostPublishingCheckReport,
) -> None:
    daily_report_mock.vehicle_activities_completely_matching = 0
    daily_report_mock.vehicle_activities_analysed = 0
    data = [
        {
            "AVLtoTimetable matching summary": [
                {
                    "SIRI field": "BlockRef",
                    "TXC match field": "BlockNumber",
                    "Total vehicleActivities analysed": 0,
                    "Total count of SIRI fields populated": 0,
                    "%populated": "0.0%",
                    "Successful match with TXC": "0",
                    "%match": "0.0%",
                    "Notes": "dummy_1",
                },
                {
                    "SIRI field": "DatedVehicleJourneyRef",
                    "TXC match field": "TicketMachine/JourneyCode",
                    "Total vehicleActivities analysed": 0,
                    "Total count of SIRI fields populated": 0,
                    "%populated": "0.0%",
                    "Successful match with TXC": "0",
                    "%match": "0.0%",
                    "Notes": "dummy_1",
                },
                {
                    "SIRI field": "DestinationRef",
                    "TXC match field": "JourneyPatternTimingLink/To/StopPointRef",
                    "Total vehicleActivities analysed": 0,
                    "Total count of SIRI fields populated": 0,
                    "%populated": "0.0%",
                    "Successful match with TXC": "0",
                    "%match": "0.0%",
                    "Notes": "dummy_1",
                },
                {
                    "SIRI field": "DirectionRef",
                    "TXC match field": "Direction",
                    "Total vehicleActivities analysed": 0,
                    "Total count of SIRI fields populated": 0,
                    "%populated": "0.0%",
                    "Successful match with TXC": "0",
                    "%match": "0.0%",
                    "Notes": "dummy_1",
                },
                {
                    "SIRI field": "LineRef",
                    "TXC match field": "LineName",
                    "Total vehicleActivities analysed": 0,
                    "Total count of SIRI fields populated": 0,
                    "%populated": "0.0%",
                    "Successful match with TXC": "15",
                    "%match": "85.0%",
                    "Notes": "dummy_1",
                },
                {
                    "SIRI field": "OperatorRef",
                    "TXC match field": "NationalOperatorCode",
                    "Total vehicleActivities analysed": 0,
                    "Total count of SIRI fields populated": 0,
                    "%populated": "0.0%",
                    "Successful match with TXC": "0",
                    "%match": "0.0%",
                    "Notes": "dummy_1",
                },
                {
                    "SIRI field": "OriginRef",
                    "TXC match field": "JourneyPatternTimingLink/from/StopPointRef",
                    "Total vehicleActivities analysed": 0,
                    "Total count of SIRI fields populated": 0,
                    "%populated": "0.0%",
                    "Successful match with TXC": "0",
                    "%match": "0.0%",
                    "Notes": "dummy_1",
                },
                {
                    "SIRI field": "PublishedLineName",
                    "TXC match field": "LineName",
                    "Total vehicleActivities analysed": 0,
                    "Total count of SIRI fields populated": 0,
                    "%populated": "0.0%",
                    "Successful match with TXC": "0",
                    "%match": "0.0%",
                    "Notes": "dummy_1",
                },
            ]
        },
        {
            "AVLtoTimetable matching summary": [
                {
                    "SIRI field": "BlockRef",
                    "TXC match field": "BlockNumber",
                    "Total vehicleActivities analysed": 0,
                    "Total count of SIRI fields populated": 0,
                    "%populated": "0.0%",
                    "Successful match with TXC": "0",
                    "%match": "0.0%",
                    "Notes": "dummy_2",
                },
                {
                    "SIRI field": "DatedVehicleJourneyRef",
                    "TXC match field": "TicketMachine/JourneyCode",
                    "Total vehicleActivities analysed": 0,
                    "Total count of SIRI fields populated": 0,
                    "%populated": "0.0%",
                    "Successful match with TXC": "0",
                    "%match": "0.0%",
                    "Notes": "dummy_2",
                },
                {
                    "SIRI field": "DestinationRef",
                    "TXC match field": "JourneyPatternTimingLink/To/StopPointRef",
                    "Total vehicleActivities analysed": 0,
                    "Total count of SIRI fields populated": 0,
                    "%populated": "0.0%",
                    "Successful match with TXC": "0",
                    "%match": "0.0%",
                    "Notes": "dummy_2",
                },
                {
                    "SIRI field": "DirectionRef",
                    "TXC match field": "Direction",
                    "Total vehicleActivities analysed": 0,
                    "Total count of SIRI fields populated": 0,
                    "%populated": "0.0%",
                    "Successful match with TXC": "0",
                    "%match": "0.0%",
                    "Notes": "dummy_2",
                },
                {
                    "SIRI field": "LineRef",
                    "TXC match field": "LineName",
                    "Total vehicleActivities analysed": 0,
                    "Total count of SIRI fields populated": 0,
                    "%populated": "0.0%",
                    "Successful match with TXC": "0",
                    "%match": "0.0%",
                    "Notes": "dummy_2",
                },
                {
                    "SIRI field": "OperatorRef",
                    "TXC match field": "NationalOperatorCode",
                    "Total vehicleActivities analysed": 0,
                    "Total count of SIRI fields populated": 0,
                    "%populated": "0.0%",
                    "Successful match with TXC": "0",
                    "%match": "0.0%",
                    "Notes": "dummy_2",
                },
                {
                    "SIRI field": "OriginRef",
                    "TXC match field": "JourneyPatternTimingLink/from/StopPointRef",
                    "Total vehicleActivities analysed": 0,
                    "Total count of SIRI fields populated": 0,
                    "%populated": "0.0%",
                    "Successful match with TXC": "0",
                    "%match": "0.0%",
                    "Notes": "dummy_2",
                },
                {
                    "SIRI field": "PublishedLineName",
                    "TXC match field": "LineName",
                    "Total vehicleActivities analysed": 0,
                    "Total count of SIRI fields populated": 0,
                    "%populated": "0.0%",
                    "Successful match with TXC": "0",
                    "%match": "0.0%",
                    "Notes": "dummy_2",
                },
            ]
        },
    ]

    json_mock.side_effect = data

    # Calling with 2x Mock to run loop 2 times.
    result = ppc_summary_data.aggregate_daily_reports(
        daily_reports=[daily_report_mock, daily_report_mock]
    )
    df = result.get_summary_report()
    columns = df.columns

    assert df.shape == (8, 8)
    assert columns[0] == "SIRI field"
    assert columns[1] == "TXC match field"
    assert columns[2] == "Total vehicleActivities analysed"
    assert columns[3] == "Total count of SIRI fields populated"
    assert columns[4] == "%populated"
    assert columns[5] == "Successful match with TXC"
    assert columns[6] == "%match"
    assert columns[7] == "Notes"

    assert df.iloc[0]["SIRI field"] == "OperatorRef"
    assert df.iloc[0]["TXC match field"] == "NationalOperatorCode"
    assert df.iloc[0]["Total vehicleActivities analysed"] == 0
    assert df.iloc[0]["Total count of SIRI fields populated"] == 0
    assert df.iloc[0]["%populated"] == str(float(0)) + "%"
    assert df.iloc[0]["Successful match with TXC"] == 0
    assert df.iloc[0]["%match"] == str(float(0)) + "%"
    assert df.iloc[0]["Notes"] == "dummy_1"

    assert df.iloc[1]["Successful match with TXC"] == 0
    assert df.iloc[1]["%match"] == str(float(0)) + "%"


def test_create_error_data_df(
    ppc_summary_data: PostPublishingChecksSummaryData,
):
    error_data = {
        "CODE_3_1": [
            {
                "Dataset ID": "6839",
                "Filename": "PTI_PASS_DQ_PASS_2GmrsMk.xml",
                "Modification date": "2020-12-18T12:13:57.543011+00:00",
                "Revision number": "-",
                "Operation period start date": "2020-12-17",
                "Operating period end date": "-",
                "Operating Profile": '<OperatingProfile xmlns="http://www.transxchange.org.uk/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n        <RegularDayType>\n          <DaysOfWeek>\n            <Monday/>\n            <Tuesday/>\n            <Wednesday/>\n            <Thursday/>\n            <Friday/>\n            <Saturday/>\n          </DaysOfWeek>\n        </RegularDayType>\n        <BankHolidayOperation>\n          <DaysOfOperation>\n            <Jan2ndScotland/>\n            <StAndrewsDay/>\n            <EasterMonday/>\n            <AugustBankHolidayScotland/>\n            <Jan2ndScotlandHoliday/>\n            <StAndrewsDayHoliday/>\n          </DaysOfOperation>\n        </BankHolidayOperation>\n      </OperatingProfile>\n      \n',
                "Service Code": "PD1073423:5",
            },
            {
                "Dataset ID": "1234",
                "Filename": "PTI_PASS_DQ_PASS_2GmrsMk.xml",
                "Modification date": "2020-12-18T12:13:57.543011+00:00",
                "Revision number": "-",
                "Operation period start date": "2020-12-17",
                "Operating period end date": "-",
                "Operating Profile": "-",
                "Service Code": "PD1073423:5",
            },
        ],
        "CODE_1_2": [
            {
                "Dataset ID": "6839",
                "Filename": "PTI_PASS_DQ_PASS_2GmrsMk.xml",
                "Modification date": "2020-12-18T12:13:57.543011+00:00",
                "Revision number": "-",
                "Operation period start date": "2020-12-17",
                "Operating period end date": "-",
            }
        ],
    }
    expected_df_columns = [
        "Dataset ID",
        "Filename",
        "Modification date",
        "Revision number",
        "Operation period start date",
        "Operating period end date",
        "error_code",
        "Operating Profile",
        "Service Code",
    ]
    error_data_df = ppc_summary_data.create_error_data_df(error_data)
    assert len(error_data_df) == 3
    for column in expected_df_columns:
        if column not in error_data_df.columns:
            assert False
