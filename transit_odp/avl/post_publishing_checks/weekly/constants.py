# flake8: noqa
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

DailyReportItem = list[dict[str, Any]]


class DailyReport(BaseModel):
    summary: DailyReportItem = Field(
        default=[], alias="AVLtoTimetable matching summary"
    )
    all_siri_analysed: DailyReportItem = Field(default=[], alias="All SIRI-VM analysed")
    uncounted_vehicles: DailyReportItem = Field(
        default=[], alias="UncountedVehicleActivities"
    )
    direction_ref: DailyReportItem = Field(default=[], alias="DirectionRef")
    destination_ref: DailyReportItem = Field(default=[], alias="DestinationRef")
    origin_ref: DailyReportItem = Field(default=[], alias="OriginRef")
    block_ref: DailyReportItem = Field(default=[], alias="BlockRef")

    class Config:
        allow_population_by_field_name = True


class WeeklyPPCSummaryFiles(str, Enum):
    PPC_SUMMARY_REPORT = "avl_to_timetable_match_summary.csv"
    BLOCK_REF = "blockref.csv"
    DESTINATION_REF = "destinationref.csv"
    DIRECTION_REF = "directionref.csv"
    ORIGIN_REF = "originref.csv"
    SIRI_MESSAGE_ANALYSED = "all_siri_vm_analysed.csv"
    UNCOUNTED_VEHICLE_ACTIVITY = "uncountedvehicleactivities.csv"
    README = "txt_file_read_me.txt"

    @classmethod
    def to_list(cls) -> list[str]:
        return [field.value for field in cls]


README_INTRO = """
Bus Open Data Service AVL to Timetables data matching
 GOV.UK

________________________________________

AVL to Timetable data matching
The AVL to Timetable matching zip contains a series of CSVs which give machine-readable results of the sampled AVL and Timetable data that currently reside in BODS.

Note that the matching report only covers the data from primary data sources on BODS which is timetables data in TransXChange format, bus location data in SIRI-VM format.
Fares data in NeTEX are not included in the AVL to Timetable matching report.

The AVL to Timetables feed matching is a weekly score of a published data feed. Daily random samples of data packets are collected for each published feed to be matched and then collated together to create a weekly report along with a weekly associated summary score for that report. This is usually done on every Monday of the week. This is the latest matching score for this feed.

Please note that BODS doesn't check every single packet of data but we do a random sampling throughout the day in order to determine these reports and scores.

Please work with your technology suppliers to provide the most accurate data so that download data consumers and eventually your bus passengers can benefit.


The zipped CSVs matching report
The AVL to Timetable matching zip contains 7 distinct CSVs:
-   avl_to_timetable_match_summary.csv: this contains a high-level overview result of how
        well the sampled AVL vehicle activities data from collected feeds on BODS matched accurately
        to all of the Timetables data on BODS. This also shows break down scores per key matching
        fields.
-   blockref.csv: this contains a detailed granular view of the missing or mismatched BlockRef value
        within the analysed journeys in SIRI VM and the Block number field in the timetables data
-   destinationref.csv: this contains a detailed granular view of the missing or mismatched
        Destinationref value within the analysed journeys in SIRI VM and the JourneyPatternTimingLink/To/
        StopPointRef field in TransXChange format of the timetables data.
-   directionref.csv: this contains a detailed granular view of the missing or mismatched Direction
        ref value within the analysed journeys in SIRI VM and the Direction from JourneyPattern field in
        TransXChange format of the timetables data
-   originref.csv: this contains a detailed granular view of the missing or mismatched OriginRef value
        within the analysed journeys in SIRI VM and the JourneyPatternTimingLink/from/StopPointRef field
	in TransXChange format of the timetables data
-   all_siri_vm_analysed.csv: this contains helpful counts of all of the AVL messages collected
        and analysed.
-   uncountedvehicleactivities.csv: this contains a detailed granular view of vehicle activities that
        were collected and counted. But unable to analyse due to gross errors in both vehicle location
        and timetables data published within BODS.

Field definitions:
The AVL to Timetables contains certain table field headers, the definitions and explanations of which
can be found below.
"""

README_OUTRO = """
Process
To be able to compare data for any given journey it is necessary to first identify a single journey in both the SIRI and TxC datasets. The SIRI delivery is the starting point for the process.

Step 1
Using OperatorRef and LineRef from the SIRI data locate the TxC files that contain data for the operator and line. There may be multiple files.
Check which of the files contain data valid for the date of the SIRI data. This will require checking the OperatingPeriod to find data which is valid for the date being tested.
a.	If file(s) found, continue to step 2.
b.	If no file found then mark the vehicle journey as failed to be analysed.

Step 2
From the Step 1 subset of TxC files search each file for any that contain a JourneyCode that matches with the DatedVehicleJourneyRef from the SIRI journey.
a.	If file(s) found with matching JourneyCodes, continue to step 3.
b.	If no file found then mark the vehicle journey as failed to be analysed.

Step 3
From the Step 2 subset of TxC files search each file for an OperatingProfile that is appropriate for the date of the SIRI data - type of day for date being tested. For example 1 April 2022 was a Friday.
a.	If file(s) found with a matching OperatingProfile, continue to step 4.
b.	If no matching OperatingProfile is found, then mark the vehicle journey as failed to be analysed.

Step 4
From the Step 3 subset of TxC files use the file with the highest RevisionNumber that is valid for the date of the SIRI data to find the correct file.
a.	If only one file is identified after filtering by RevisionNumber, move to step 5.
b.	If there is more than one file remaining after reading the RevisionNumber, mark they vehicle journey as failed to be analysed.

Step 5
You will have only one file when you reach this Step.
Search within the file for JourneyCode to find the JourneyCode with an OperatingProfile that is valid for the date being tested. There may be more than one matching JourneyCode within a TxC if it is used for example for journeys operating on weekdays and weekends.
a.	If a single JourneyCode is identified that is valid on the correct day, move to step 6.
b.	If there is more than one valid JourneyCode found, mark the vehicle journey as failed to be analysed.

Step 6
Once a single JourneyCode with an appropriate OperatingPeriod and OperatingProfile is identified testing can progress to the remaining pairs of values described earlier in this document.
If DatedVehicleJourneyRef from the selected SIRI delivery is unable to be matched to a single JourneyCode in a TxC file then the analysis should fail for all data types.

Step 7
It will be necessary to identify the correct direction, destination and origin information for the full journey details being tested.
Start with identifying the JourneyPattern for the journeys Direction. Knowing the JourneyPattern allows identification all JourneyPatternSection used in the JourneyPattern. Knowing the JourneyPatternSection allows the first and last sections to be identified. These are required to locate the origin and destination information.
The OriginRef is the StopPointRef in the From element of the first JourneyPatternSection of the JourneyPattern.
The DestinationRef is the StopPointRef in the To element of the last JourneyPatternSection of the JourneyPattern.
"""
