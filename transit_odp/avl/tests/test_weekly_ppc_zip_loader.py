import unittest
import factory
import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from pandas.testing import assert_frame_equal
import io
from transit_odp.avl.factories import PostPublishingCheckReportFactory
from transit_odp.avl.models import PPCReportType
from transit_odp.avl.require_attention.weekly_ppc_zip_loader import (
    ALL_SIRIVM_FILENAME,
    UNCOUNTED_VEHICLE_ACTIVITY_FILENAME,
    get_destinationref_df,
    get_directionref_df,
    get_latest_reports_from_db,
    get_originref_df,
    read_all_linenames_from_weekly_files,
)
from transit_odp.organisation.factories import DatasetFactory, OrganisationFactory
from datetime import date, timedelta
from transit_odp.organisation.constants import AVLType


pytestmark = pytest.mark.django_db


ALL_SIRIVM_ANNALYSED = """Version,ResponseTimestamp (ServiceDelivery),ProducerRef,ResponseTimestamp (VehicleMonitoringDelivery),RequestMessageRef,ValidUntil,ShortestPossibleCycle,RecordedAtTime,ItemIdentifier,ValidUntilTime,LineRef,DirectionRef,DataFrameRef,DatedVehicleJourneyRef,PublishedLineName,OperatorRef,OriginRef,OriginName,DestinationRef,DestinationName,OriginAimedDepartureTime,Longitude,Latitude,Bearing,VehicleRef,BlockRef,DriverRef
  \n2.0,2024-10-21T21:45:04.527000+00:00,DepartmentForTransport,2024-10-21T21:45:04.527000+00:00,92df8a55-02ca-45bb-ab2a-304501f314a8,2024-10-21T21:50:04.527000+00:00,PT5S,2024-10-21T21:44:28+00:00,6ca2f7fd-4a84-4ec7-b2af-be10ed3cbf6f,2024-10-21T21:50:04.527000+00:00,4A,inbound,2024-10-21,1034,4A,ACYM,5410AWD70072,Post_Office,5400GYX17359,Bus_Station,2024-10-21T21:08:00+00:00,-4.18436,53.215075,139.0,2932,1111,-
  \n2.0,2024-10-21T21:45:04.527000+00:00,DepartmentForTransport,2024-10-21T21:45:04.527000+00:00,92df8a55-02ca-45bb-ab2a-304501f314a8,2024-10-21T21:50:04.527000+00:00,PT5S,2024-10-21T18:39:09+00:00,478eb580-9152-41ca-9ff8-19130669c570,2024-10-21T21:50:04.527000+00:00,11C,outbound,2024-10-21,1023,11C,ACYM,5120WDB47572,Bus_Station,5110WDB48302,Bus_Station,2024-10-21T17:45:00+00:00,-3.490725,53.318343,-,4409,1216,-
  \n2.0,2024-10-21T21:45:04.527000+00:00,DepartmentForTransport,2024-10-21T21:45:04.527000+00:00,92df8a55-02ca-45bb-ab2a-304501f314a8,2024-10-21T21:50:04.527000+00:00,PT5S,2024-10-21T18:21:47+00:00,07e11872-1103-41cd-bb45-7349b843abfd,2024-10-21T21:50:04.527000+00:00,5,inbound,2024-10-21,1042,5,ACYM,5110WDB48304,Parade_Street,5140WDB25302,Bus_Station,2024-10-21T17:45:00+00:00,-2.996421,53.047666,-,1010,1031,-
  \n2.0,2024-10-21T21:45:04.527000+00:00,DepartmentForTransport,2024-10-21T21:45:04.527000+00:00,92df8a55-02ca-45bb-ab2a-304501f314a8,2024-10-21T21:50:04.527000+00:00,PT5S,2024-10-21T17:53:55+00:00,d00a7203-6e6b-429e-8d04-f97ed74b9b8a,2024-10-21T21:50:04.527000+00:00,12,inbound,2024-10-21,1058,12,ACYM,5140AWQ26507,Library,5140WDB25301,Bus_Station,2024-10-21T17:31:00+00:00,-2.996373,53.047706,-,0703,1027,-
  \n2.0,2024-10-21T21:45:04.527000+00:00,DepartmentForTransport,2024-10-21T21:45:04.527000+00:00,92df8a55-02ca-45bb-ab2a-304501f314a8,2024-10-21T21:50:04.527000+00:00,PT5S,2024-10-21T18:04:52+00:00,ee3f2f1b-c29d-4962-8495-2b7b57f72b43,2024-10-21T21:50:04.527000+00:00,X4,inbound,2024-10-21,1024,X4,ACYM,5120WDB21525,Bus_Station,0610CH2395,Railway_Station,2024-10-21T16:56:00+00:00,-2.89643,53.176345,-,3142,1014,-
  \n2.0,2024-10-21T21:45:04.527000+00:00,DepartmentForTransport,2024-10-21T21:45:04.527000+00:00,92df8a55-02ca-45bb-ab2a-304501f314a8,2024-10-21T21:50:04.527000+00:00,PT5S,2024-10-21T21:33:08+00:00,ecd45933-71a3-48b6-9ae1-999a996ebb23,2024-10-21T21:50:04.527000+00:00,13,outbound,2024-10-21,1033,13,ACYM,5130AWD72329,Gadlas_Road_Shops,5130CWX02027,Clifton_Road,2024-10-21T20:45:00+00:00,-3.835033,53.324028,-,0696,1030,-
  \n2.0,2024-10-21T21:45:04.527000+00:00,DepartmentForTransport,2024-10-21T21:45:04.527000+00:00,92df8a55-02ca-45bb-ab2a-304501f314a8,2024-10-21T21:50:04.527000+00:00,PT5S,2024-10-21T18:20:13+00:00,957baaad-2d82-46ed-8bdd-a62fa5474ca7,2024-10-21T21:50:04.527000+00:00,51,inbound,2024-10-21,1028,51,ACYM,5110AWD71534,Lenten_Pool,5110AWD72156,Bus_Station,2024-10-21T17:35:00+00:00,-3.488575,53.319266,-,4482,1215,-
  \n2.0,2024-10-21T21:45:04.527000+00:00,DepartmentForTransport,2024-10-21T21:45:04.527000+00:00,92df8a55-02ca-45bb-ab2a-304501f314a8,2024-10-21T21:50:04.527000+00:00,PT5S,2024-10-21T17:09:52+00:00,a05ee29c-997d-4177-9d18-5bc15031a035,2024-10-21T21:50:04.527000+00:00,12,inbound,2024-10-21,1098,12,ACYM,5130AWD71192,Palladium,5110AWD72156,Bus_Station,2024-10-21T15:29:00+00:00,-3.490491,53.318538,-,4538,1202,-
  \n2.0,2024-10-21T21:45:04.527000+00:00,DepartmentForTransport,2024-10-21T21:45:04.527000+00:00,92df8a55-02ca-45bb-ab2a-304501f314a8,2024-10-21T21:50:04.527000+00:00,PT5S,2024-10-21T17:23:52+00:00,43f351b5-fb73-4f3f-82c1-8787dd9cc3dd,2024-10-21T21:50:04.527000+00:00,5,inbound,21/10/24,1019,5,ACYM,5400AWD70195,Bus_Station,5130AWD71189,Penmorfa_West_Shore,-,-4.12631,53.227333,-,3186,124693,-"""

DESTINATION_REF = """SD ResponseTimestamp,RecordedAtTime,AVL data set name BODS,AVL data set ID BODS,DatedVehicleJourneyRef in SIRI,VehicleRef in SIRI,Timetable file name,Timetable data set ID BODS,DepartureTime in TXC,DestinationRef in SIRI,StopPointRef in TxC,SIRI XML line number,TransXChange XML line number,Error note,StopPointRef in TXC
    \n2024-10-21T21:45:04.527000+00:00,2024-10-21T18:21:47+00:00,Arriva UK Bus_20201027 14:44:26,705,1042,1010,ACYM_B005_ACYMPG00072451035_20240630_-_1892096.xml,15757,14:25:00,5140WDB25302,-,1,24127,DestinationRef does not match final StopPointRef in timetable,5130AWD71189
    \n2024-10-21T21:45:04.527000+00:00,2024-10-21T17:53:55+00:00,Arriva UK Bus_20201027 14:44:26,705,1058,0703,ACYM_R012_ACYMPG000724521412_20240630_-_1889406.xml,15757,12:29:00,5140WDB25301,-,1,31677,DestinationRef does not match final StopPointRef in timetable,5110AWD72156
    \n2024-10-21T21:45:04.527000+00:00,2024-10-21T18:03:52+00:00,Arriva UK Bus_20201027 14:44:26,705,1026,2664,ACYM_B005_ACYMPG00072451035_20240630_-_1892096.xml,15757,10:25:00,5120WDB21526,-,1,21955,DestinationRef does not match final StopPointRef in timetable,5130AWD71189
    \n2024-10-21T21:45:04.527000+00:00,2024-10-21T18:24:21+00:00,Arriva UK Bus_20201027 14:44:26,705,1015,0693,ACYM_W014_ACYMPG000724543714_20240901_-_1918555.xml,15757,13:20:00,5130AWA17200,-,1,1047,DestinationRef does not match final StopPointRef in timetable,5140AWQ26507
    \n2024-10-21T21:45:04.527000+00:00,2024-10-21T18:35:59+00:00,Arriva UK Bus_20201027 14:44:26,705,1028,2907,ACYM_B005_ACYMPG00072451035_20240630_-_1892096.xml,15757,11:05:00,5120AWF80627,-,1,21955,DestinationRef does not match final StopPointRef in timetable,5130AWD71189"""

ORIGIN_REF = """SD ResponseTimestamp,RecordedAtTime,AVL data set name BODS,AVL data set ID BODS,DatedVehicleJourneyRef in SIRI,VehicleRef in SIRI,Timetable file name,Timetable data set ID BODS,DepartureTime in TXC,OriginRef in SIRI,StopPointRef in TxC,SIRI XML line number,TransXChange XML line number,Error note,StopPointRef in TXC
 \n2024-10-21T21:45:04.527000+00:00,2024-10-21T18:21:47+00:00,Arriva UK Bus_20201027 14:44:26,705,1042,1010,ACYM_B005_ACYMPG00072451035_20240630_-_1892096.xml,15757,14:25:00,5110WDB48304,-,1,23414,OriginRef does not match first StopPointRef in timetable,5400GYX17361
 \n2024-10-21T21:45:04.527000+00:00,2024-10-21T17:53:55+00:00,Arriva UK Bus_20201027 14:44:26,705,1058,0703,ACYM_R012_ACYMPG000724521412_20240630_-_1889406.xml,15757,12:29:00,5140AWQ26507,-,1,30820,OriginRef does not match first StopPointRef in timetable,5130AWD71192
 \n2024-10-21T21:45:04.527000+00:00,2024-10-21T18:03:52+00:00,Arriva UK Bus_20201027 14:44:26,705,1026,2664,ACYM_B005_ACYMPG00072451035_20240630_-_1892096.xml,15757,10:25:00,0610EP1392,-,1,21242,OriginRef does not match first StopPointRef in timetable,5400GYX17361
 \n2024-10-21T21:45:04.527000+00:00,2024-10-21T18:24:21+00:00,Arriva UK Bus_20201027 14:44:26,705,1015,0693,ACYM_W014_ACYMPG000724543714_20240901_-_1918555.xml,15757,13:20:00,5130AWD72330,-,1,754,OriginRef does not match first StopPointRef in timetable,5140WDB25301
 \n2024-10-21T21:45:04.527000+00:00,2024-10-21T18:35:59+00:00,Arriva UK Bus_20201027 14:44:26,705,1028,2907,ACYM_B005_ACYMPG00072451035_20240630_-_1892096.xml,15757,11:05:00,0610EP1392,-,1,21242,OriginRef does not match first StopPointRef in timetable,5400GYX17361
 \n2024-10-21T21:45:04.527000+00:00,2024-10-21T21:44:47+00:00,Arriva UK Bus_20201027 14:44:26,705,1047,1000,ACYM_B005_ACYMPG00072451035_20240630_-_1892096.xml,15757,18:15:00,5140WDB25302,-,1,37950,OriginRef does not match first StopPointRef in timetable,5130AWD71189
 \n2024-10-21T21:45:04.527000+00:00,2024-10-21T19:17:42+00:00,Arriva UK Bus_20201027 14:44:26,705,1047,4553,ACYM_W035_ACYMPG000724547235_20240630_-_1890599.xml,15757,09:19:00,5110WDB48302,-,1,1540,OriginRef does not match first StopPointRef in timetable,5140WDB25303
 \n2024-10-21T21:45:04.527000+00:00,2024-10-21T17:23:52+00:00,Arriva UK Bus_20201027 14:44:26,705,1019,3186,ACYM_B005_ACYMPG00072451035_20240630_-_1892096.xml,15757,11:05:00,5400AWD70195,-,1,32462,OriginRef does not match first StopPointRef in timetable,5130AWD71189
 \n2024-10-21T21:45:04.527000+00:00,2024-10-21T21:44:26+00:00,Arriva UK Bus_20201027 14:44:26,705,1038,3179,ACYM_C04C_ACYMPG00072452544_20240720_20241026_1909812.xml,15757,15:18:00,5410AWD70516,-,1,9780,OriginRef does not match first StopPointRef in timetable,5120WDB21525"""

DIRECTION_REF = """SD ResponseTimestamp,RecordedAtTime,AVL data set name BODS,AVL data set ID BODS,DatedVehicleJourneyRef in SIRI,VehicleRef in SIRI,Timetable file name,Timetable data set ID BODS,DepartureTime in TXC,DirectionRef in SIRI,Direction from JourneyPattern in TXC,SIRI XML line number,TransXChange XML line number,Error note
2024-10-21T21:45:04.527000+00:00,2024-10-21T17:23:52+00:00,Arriva UK Bus_20201027 14:44:26,705,1019,3186,ACYM_B005_ACYMPG00072451035_20240630_-_1892096.xml,15757,11:05:00,inbound,outbound,1,39727,DirectionRef does not match Direction in timetable
"""

UNCOUNTED_VEHICLE_ACTIVITY_DATA = """SD ResponseTimestamp,AVL data set name BODS,AVL data set ID BODS,OperatorRef,LineRef,RecordedAtTime,DatedVehicleJourneyRef in SIRI,Error note: Reason it could not be analysed against TXC
    \n2024-10-22T19:24:39.388000+00:00,Arriva UK Bus_20201027 14:44:26,705,ACYM,4,2024-10-22T19:24:17+00:00,1052,Found more than one matching vehicle journey in timetables belonging to a single service code [CODE_6_2_B]
    \n2024-10-24T22:09:55.661000+00:00,Arriva UK Bus_20201027 14:44:26,705,ACYM,4,2024-10-24T22:09:39+00:00,1052,Found more than one matching vehicle journey in timetables belonging to a single service code [CODE_6_2_B]
    \n2024-10-26T18:45:38.091000+00:00,Arriva UK Bus_20201027 14:44:26,705,ACYM,5,2024-10-26T18:28:41+00:00,3112,No vehicle journeys found with JourneyCode '3112' [CODE_2_1]
    \n2024-10-26T18:45:38.091000+00:00,Arriva UK Bus_20201027 14:44:26,705,ACYM,5,2024-10-26T17:42:03+00:00,3110,No vehicle journeys found with JourneyCode '3110' [CODE_2_1]
    \n2024-10-26T18:45:38.091000+00:00,Arriva UK Bus_20201027 14:44:26,705,ACYM,4,2024-10-26T18:45:19+00:00,3004,Found more than one matching vehicle journey in timetables belonging to a single service code [CODE_6_2_B]"""

BASE_PATH = "transit_odp.avl.require_attention.weekly_ppc_zip_loader"


def test_get_destinationref_df_with_records():
    csv_content = io.StringIO(DESTINATION_REF)
    mock_zip_file = MagicMock()
    mock_zip_file.open.return_value.__enter__.return_value = csv_content

    df_input = pd.read_csv(
        io.StringIO(ALL_SIRIVM_ANNALYSED),
        dtype={"VehicleRef": "object", "DatedVehicleJourneyRef": "int64"},
    )

    expected_df = pd.DataFrame(
        {"OperatorRef": ["ACYM", "ACYM"], "LineRef": ["5", "12"]}
    )
    result_df = get_destinationref_df(mock_zip_file, df_input)
    assert_frame_equal(expected_df, result_df, check_dtype=False)


def test_get_destinationref_df_with_blankfile():
    csv_content = io.StringIO(
        """SD ResponseTimestamp,RecordedAtTime,AVL data set name BODS,AVL data set ID BODS,DatedVehicleJourneyRef in SIRI,VehicleRef in SIRI,Timetable file name,Timetable data set ID BODS,DepartureTime in TXC,DestinationRef in SIRI,StopPointRef in TxC,SIRI XML line number,TransXChange XML line number,Error note,StopPointRef in TXC"""
    )
    mock_zip_file = MagicMock()
    mock_zip_file.open.return_value.__enter__.return_value = csv_content

    df_input = pd.read_csv(
        io.StringIO(ALL_SIRIVM_ANNALYSED),
        dtype={"VehicleRef": "object", "DatedVehicleJourneyRef": "int64"},
    )

    expected_df = pd.DataFrame(columns=["OperatorRef", "LineRef"])
    result_df = get_destinationref_df(mock_zip_file, df_input)

    assert_frame_equal(expected_df, result_df, check_dtype=False)


@patch(f"{BASE_PATH}.ZipFile")
def test_get_destinationref_df_file_missing(MockZipFile):
    mock_zipfile = MockZipFile.return_value
    mock_zipfile.open.side_effect = KeyError("File not found in zip")
    result_df = get_destinationref_df(mock_zipfile, pd.DataFrame())
    expected_df = pd.DataFrame(columns=["OperatorRef", "LineRef"])
    assert_frame_equal(expected_df, result_df, check_dtype=False)


def test_get_originref_df_blank_file():
    csv_content = io.StringIO(
        """SD ResponseTimestamp,RecordedAtTime,AVL data set name BODS,AVL data set ID BODS,DatedVehicleJourneyRef in SIRI,VehicleRef in SIRI,Timetable file name,Timetable data set ID BODS,DepartureTime in TXC,OriginRef in SIRI,StopPointRef in TxC,SIRI XML line number,TransXChange XML line number,Error note,StopPointRef in TXC"""
    )
    mock_zip_file = MagicMock()
    mock_zip_file.open.return_value.__enter__.return_value = csv_content

    df_input = pd.read_csv(
        io.StringIO(ALL_SIRIVM_ANNALYSED),
        dtype={"VehicleRef": "object", "DatedVehicleJourneyRef": "int64"},
    )

    expected_df = pd.DataFrame(columns=["OperatorRef", "LineRef"])
    result_df = get_originref_df(mock_zip_file, df_input)

    assert_frame_equal(expected_df, result_df, check_dtype=False)


def test_get_originref_df_with_records():
    csv_content = io.StringIO(ORIGIN_REF)
    mock_zip_file = MagicMock()
    mock_zip_file.open.return_value.__enter__.return_value = csv_content

    df_input = pd.read_csv(
        io.StringIO(ALL_SIRIVM_ANNALYSED),
        dtype={"VehicleRef": "object", "DatedVehicleJourneyRef": "int64"},
    )

    expected_df = pd.DataFrame(
        {"OperatorRef": ["ACYM", "ACYM"], "LineRef": ["5", "12"]}
    )
    result_df = get_originref_df(mock_zip_file, df_input)

    assert_frame_equal(expected_df, result_df, check_dtype=False)


@patch(f"{BASE_PATH}.ZipFile")
def test_get_originref_df_file_missing(MockZipFile):
    mock_zipfile = MockZipFile.return_value
    mock_zipfile.open.side_effect = KeyError("File not found in zip")
    result_df = get_originref_df(mock_zipfile, pd.DataFrame())
    expected_df = pd.DataFrame(columns=["OperatorRef", "LineRef"])
    assert_frame_equal(expected_df, result_df, check_dtype=False)


def test_get_directionref_df_blank_file():
    csv_content = io.StringIO(
        """SD ResponseTimestamp,RecordedAtTime,AVL data set name BODS,AVL data set ID BODS,DatedVehicleJourneyRef in SIRI,VehicleRef in SIRI,Timetable file name,Timetable data set ID BODS,DepartureTime in TXC,DirectionRef in SIRI,Direction from JourneyPattern in TXC,SIRI XML line number,TransXChange XML line number,Error note"""
    )
    mock_zip_file = MagicMock()
    mock_zip_file.open.return_value.__enter__.return_value = csv_content

    df_input = pd.read_csv(
        io.StringIO(ALL_SIRIVM_ANNALYSED),
        dtype={"VehicleRef": "object", "DatedVehicleJourneyRef": "int64"},
    )

    expected_df = pd.DataFrame(columns=["OperatorRef", "LineRef"])
    result_df = get_directionref_df(mock_zip_file, df_input)

    assert_frame_equal(expected_df, result_df, check_dtype=False)


def test_get_directionref_df_with_records():
    csv_content = io.StringIO(DIRECTION_REF)
    mock_zip_file = MagicMock()
    mock_zip_file.open.return_value.__enter__.return_value = csv_content

    df_input = pd.read_csv(
        io.StringIO(ALL_SIRIVM_ANNALYSED),
        dtype={"VehicleRef": "object", "DatedVehicleJourneyRef": "int64"},
    )

    expected_df = pd.DataFrame({"OperatorRef": ["ACYM"], "LineRef": ["5"]})
    result_df = get_directionref_df(mock_zip_file, df_input)
    assert_frame_equal(expected_df, result_df, check_dtype=False)


@patch(f"{BASE_PATH}.ZipFile")
def test_get_directionref_df_file_missing(MockZipFile):
    mock_zipfile = MockZipFile.return_value
    mock_zipfile.open.side_effect = KeyError("File not found in zip")
    result_df = get_directionref_df(mock_zipfile, pd.DataFrame())
    expected_df = pd.DataFrame(columns=["OperatorRef", "LineRef"])
    assert_frame_equal(expected_df, result_df, check_dtype=False)


def test_get_latest_records_from_db():
    today = date.today()
    filename = "ppc_weekly_report_test.zip"
    organisation = OrganisationFactory()
    dataset = DatasetFactory(organisation=organisation, dataset_type=AVLType)
    PostPublishingCheckReportFactory(
        dataset=dataset,
        vehicle_activities_analysed=10,
        vehicle_activities_completely_matching=0,
        granularity=PPCReportType.WEEKLY,
        file=factory.django.FileField(filename=filename),
        created=today,
    )

    filename = "ppc_weekly_report_test.zip"
    dataset_two = DatasetFactory(organisation=organisation, dataset_type=AVLType)
    PostPublishingCheckReportFactory(
        dataset=dataset_two,
        vehicle_activities_analysed=10,
        vehicle_activities_completely_matching=0,
        granularity=PPCReportType.WEEKLY,
        file=factory.django.FileField(filename=filename),
        created=today,
    )

    filename = "ppc_weekly_report_test.zip"
    dataset_three = DatasetFactory(organisation=organisation, dataset_type=AVLType)
    PostPublishingCheckReportFactory(
        dataset=dataset_three,
        vehicle_activities_analysed=0,
        vehicle_activities_completely_matching=0,
        granularity=PPCReportType.WEEKLY,
        file=factory.django.FileField(filename=filename),
        created=today,
    )

    records = get_latest_reports_from_db()
    assert len(records) == 2


def test_get_latest_records_from_db_with_prev_week():
    today = date.today()
    filename = "ppc_weekly_report_test.zip"
    organisation = OrganisationFactory()
    dataset = DatasetFactory(organisation=organisation, dataset_type=AVLType)
    PostPublishingCheckReportFactory(
        dataset=dataset,
        vehicle_activities_analysed=10,
        vehicle_activities_completely_matching=0,
        granularity=PPCReportType.WEEKLY,
        file=factory.django.FileField(filename=filename),
        created=today,
    )

    prev_week = today - timedelta(weeks=1)

    filename = "ppc_weekly_report_test.zip"
    dataset_two = DatasetFactory(organisation=organisation, dataset_type=AVLType)
    PostPublishingCheckReportFactory(
        dataset=dataset_two,
        vehicle_activities_analysed=10,
        vehicle_activities_completely_matching=0,
        granularity=PPCReportType.WEEKLY,
        file=factory.django.FileField(filename=filename),
        created=prev_week,
    )

    filename = "ppc_weekly_report_test.zip"
    dataset_three = DatasetFactory(organisation=organisation, dataset_type=AVLType)
    PostPublishingCheckReportFactory(
        dataset=dataset_three,
        vehicle_activities_analysed=0,
        vehicle_activities_completely_matching=0,
        granularity=PPCReportType.WEEKLY,
        file=factory.django.FileField(filename=filename),
        created=today,
    )

    records = get_latest_reports_from_db()

    assert len(records) == 1


# @patch(f"{BASE_PATH}.get_latest_reports_from_db")
# @patch(f"{BASE_PATH}.get_destinationref_df")
# @patch(f"{BASE_PATH}.get_originref_df")
# @patch(f"{BASE_PATH}.get_directionref_df")
# @patch(f"{BASE_PATH}.ZipFile")
# def test_read_all_linenames_from_weekly_files(
#     mock_zip_file,
#     mock_direction_ref,
#     mock_origin_ref,
#     mock_destination_ref,
#     mock_reports_fromDB,
# ):
#     mock_origin_ref.return_value = pd.DataFrame(
#         {"OperatorRef": ["ACYM", "ACYM"], "LineRef": ["5", "12"]}
#     )
#     mock_destination_ref.return_value = pd.DataFrame(
#         {"OperatorRef": ["ACYM", "ACYM"], "LineRef": ["5", "10"]}
#     )
#     mock_direction_ref.return_value = pd.DataFrame(
#         {"OperatorRef": ["ACYM", "ACYM"], "LineRef": ["5", "8"]}
#     )

#     mock_record = MagicMock()
#     mock_record.file.path = "mock.zip"
#     mock_reports_fromDB.return_value = [mock_record]

#     mock_zip_instance = mock_zip_file.return_value.__enter__.return_value
#     mock_zip_instance.namelist.return_value = [
#         ALL_SIRIVM_FILENAME,
#         UNCOUNTED_VEHICLE_ACTIVITY_FILENAME,
#     ]

#     csv_data = {
#         ALL_SIRIVM_FILENAME: io.StringIO(ALL_SIRIVM_ANNALYSED),
#         UNCOUNTED_VEHICLE_ACTIVITY_FILENAME: io.StringIO(
#             UNCOUNTED_VEHICLE_ACTIVITY_DATA
#         ),
#     }

#     def mock_open(name):
#         if name in csv_data:
#             return csv_data[name]
#         raise KeyError(f"File {name} not found in zip")

#     mock_zip_instance.open.side_effect = mock_open

#     result_df = read_all_linenames_from_weekly_files()
#     expected_df = pd.DataFrame(
#         {
#             "OperatorRef": ["ACYM", "ACYM", "ACYM", "ACYM", "ACYM"],
#             "LineRef": ["4", "5", "10", "12", "8"],
#         }
#     )
#     assert_frame_equal(expected_df, result_df, check_dtype=False)


# @patch(f"{BASE_PATH}.get_latest_reports_from_db")
# @patch(f"{BASE_PATH}.get_destinationref_df")
# @patch(f"{BASE_PATH}.get_originref_df")
# @patch(f"{BASE_PATH}.get_directionref_df")
# @patch(f"{BASE_PATH}.ZipFile")
# def test_read_all_linenames_from_weekly_files_blank_uncounted_vehicle(
#     mock_zip_file,
#     mock_direction_ref,
#     mock_origin_ref,
#     mock_destination_ref,
#     mock_reports_fromDB,
# ):
#     mock_origin_ref.return_value = pd.DataFrame(
#         {"OperatorRef": ["ACYM", "ACYM"], "LineRef": ["5", "12"]}
#     )
#     mock_destination_ref.return_value = pd.DataFrame(
#         {"OperatorRef": ["ACYM", "ACYM"], "LineRef": ["5", "10"]}
#     )
#     mock_direction_ref.return_value = pd.DataFrame(
#         {"OperatorRef": ["ACYM", "ACYM"], "LineRef": ["5", "8"]}
#     )

#     mock_record = MagicMock()
#     mock_record.file.path = "mock.zip"
#     mock_reports_fromDB.return_value = [mock_record]

#     mock_zip_instance = mock_zip_file.return_value.__enter__.return_value
#     mock_zip_instance.namelist.return_value = [
#         ALL_SIRIVM_FILENAME,
#         UNCOUNTED_VEHICLE_ACTIVITY_FILENAME,
#     ]

#     csv_data = {
#         ALL_SIRIVM_FILENAME: io.StringIO(ALL_SIRIVM_ANNALYSED),
#         UNCOUNTED_VEHICLE_ACTIVITY_FILENAME: io.StringIO(
#             "SD ResponseTimestamp,AVL data set name BODS,AVL data set ID BODS,OperatorRef,LineRef,RecordedAtTime,DatedVehicleJourneyRef in SIRI,Error note: Reason it could not be analysed against TXC"
#         ),
#     }

#     def mock_open(name):
#         if name in csv_data:
#             return csv_data[name]
#         raise KeyError(f"File {name} not found in zip")

#     mock_zip_instance.open.side_effect = mock_open

#     result_df = read_all_linenames_from_weekly_files()
#     expected_df = pd.DataFrame(
#         {
#             "OperatorRef": ["ACYM", "ACYM", "ACYM", "ACYM"],
#             "LineRef": ["5", "10", "12", "8"],
#         }
#     )
#     assert_frame_equal(expected_df, result_df, check_dtype=False)


@patch(f"{BASE_PATH}.get_latest_reports_from_db")
def test_read_all_linenames_from_weekly_files_blank_record_from_db(
    mock_reports_fromDB,
):
    mock_reports_fromDB.return_value = []
    result_df = read_all_linenames_from_weekly_files()
    expected_df = pd.DataFrame(columns=["OperatorRef", "LineRef"])
    assert_frame_equal(expected_df, result_df, check_dtype=False)


@patch(f"{BASE_PATH}.get_latest_reports_from_db")
@patch(f"{BASE_PATH}.get_destinationref_df")
@patch(f"{BASE_PATH}.get_originref_df")
@patch(f"{BASE_PATH}.get_directionref_df")
@patch(f"{BASE_PATH}.ZipFile")
def test_read_all_linenames_from_weekly_files_get_destinationref_df_exception(
    mock_zip_file,
    mock_direction_ref,
    mock_origin_ref,
    mock_destination_ref,
    mock_reports_fromDB,
):
    mock_origin_ref.return_value = pd.DataFrame(
        {"OperatorRef": ["ACYM", "ACYM"], "LineRef": ["5", "12"]}
    )
    mock_destination_ref.side_effect = KeyError("File is not present")
    mock_direction_ref.return_value = pd.DataFrame(
        {"OperatorRef": ["ACYM", "ACYM"], "LineRef": ["5", "8"]}
    )

    mock_record = MagicMock()
    mock_record.file.path = "mock.zip"
    mock_reports_fromDB.return_value = [mock_record]

    mock_zip_instance = mock_zip_file.return_value.__enter__.return_value
    mock_zip_instance.namelist.return_value = [
        ALL_SIRIVM_FILENAME,
        UNCOUNTED_VEHICLE_ACTIVITY_FILENAME,
    ]

    csv_data = {
        ALL_SIRIVM_FILENAME: io.StringIO(ALL_SIRIVM_ANNALYSED),
        UNCOUNTED_VEHICLE_ACTIVITY_FILENAME: io.StringIO(
            "SD ResponseTimestamp,AVL data set name BODS,AVL data set ID BODS,OperatorRef,LineRef,RecordedAtTime,DatedVehicleJourneyRef in SIRI,Error note: Reason it could not be analysed against TXC"
        ),
    }

    def mock_open(name):
        if name in csv_data:
            return csv_data[name]
        raise KeyError(f"File {name} not found in zip")

    mock_zip_instance.open.side_effect = mock_open

    result_df = read_all_linenames_from_weekly_files()
    expected_df = pd.DataFrame(columns=["OperatorRef", "LineRef"])
    assert_frame_equal(expected_df, result_df, check_dtype=False)
