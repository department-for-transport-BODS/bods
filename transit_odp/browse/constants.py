from collections import OrderedDict

from transit_odp.common.collections import Column

INTRO = """

Bus Open Data Service Data Catalogue
 GOV.UK

________________________________________

Data Catalogue
The data catalogue zip contains a series of CSVs which gives a machine-readable
overview of all the data that resides in BODS currently.

Note that the data catalogue only covers the data from primary data sources on BODS
which is timetables data in TransxChange format, bus location data in SIRI-VM format
and fares data in NeTEx format. Other non-primary data on BODS (e.g disruptions data
or GTFS converted forms) are not represented on the data catalogue.

The data catalogue zip contains 5 distinct CSVs:
-   Overall data catalogue: this contains a high-level overview of all the static
        data on BODS: timetables and fares data.
-   Timetables data catalogue: this contains a detailed granular view of the
        timetables data within BODS. It also contains a detailed mapping of the BODS
        timetables data with the data from the Office of the Traffic Commissioner (OTC).
-   Organisations data catalogue: this contains helpful counts of data at an
        organisation level: which is at the level of the publishing operators (e.g
        overall service data)
-   Location data catalogue: this contains a detailed granular view of the automatic
        vehicle location data within BODS.

Field definitions:
The data catalogue contains certain fields the definitions and explanations of which
can be found below.

"""

INTRO_WITH_FARES_FEATURE_FLAG_ACTIVE = """

Bus Open Data Service Data Catalogue
 GOV.UK

________________________________________

Data Catalogue
The data catalogue zip contains a series of CSVs which gives a machine-readable
overview of all the data that resides in BODS currently.

Note that the data catalogue only covers the data from primary data sources on BODS
which is timetables data in TransxChange format, bus location data in SIRI-VM format
and fares data in NeTEx format. Other non-primary data on BODS (e.g GTFS converted forms)
are not represented on the data catalogue.

The data catalogue zip contains 7 distinct CSVs:
-   Overall data catalogue: this contains a high-level overview of all the static data on BODS: timetables and fares data.
-   Timetables data catalogue: this contains a detailed granular view of the timetables data within BODS. It also contains a detailed mapping of the BODS timetables data with the data from the Office of the Traffic Commissioner (OTC).
-   Fares data catalogue: this contains a detailed granular view of the fares data within BODS.
-   Disruptions data catalogue: this contains a detailed view of all of the disruptions active and pending within BODS.
-   Organisations data catalogue: this contains helpful counts of data at an organisation level.
-   Location data catalogue: this contains an overview of the location data within BODS.
-   Operator NOC data catalogue: this describes all organisations on BODS and the National Operator Codes (NOCs) that are associated with them.

Field definitions:
The data catalogue contains certain fields the definitions and explanations of which can be found below.

"""

GUIDANCE_TEXT_TIMETABLE_COLUMN_MAP = OrderedDict(
    {
        "service_code": Column(
            "XML:Service Code",
            "The ServiceCode(s) as extracted from the files provided by "
            "the operator/publisher to BODS.",
        ),
        "string_lines": Column(
            "XML:Line Name",
            "The line name(s) as extracted from the files provided by "
            "the operator/publisher to BODS.",
        ),
        "requires_attention": Column(
            "Requires Attention",
            (
                """No:
                <pre>                             Default state for correctly published services, will be “No” unless any of the logic below is met.
                                             Yes:
                                             Yes If OTC status = Registered and Scope Status = In scope and Seasonal Status ≠ Out of season and Published Status = Unpublished.
                                             Yes if OTC status = Registered and Scope Status = In scope and Seasonal Status ≠ Out of season and Published Status = Published and Timeliness Status ≠ Up to date.
                </pre>
                """
            ),
        ),
        "published_status": Column(
            "Published Status",
            (
                """Published: Published to BODS by an Operator/Agent.
                <pre>                             Unpublished: Not published to BODS by an Operator/Agent.</pre>
                """
            ),
        ),
        "otc_status": Column(
            "OTC Status",
            (
                """Registered: Registered and not cancelled within the OTC database.
                <pre>                             Unregistered: Not Registered within the OTC.</pre>
                """
            ),
        ),
        "scope_status": Column(
            "Scope Status",
            (
                """In scope: Default status for services registered with the OTC and other enhanced partnerships.
                <pre>                             Out of Scope: Service code has been marked as exempt by the DVSA or the BODS team.</pre>
                """
            ),
        ),
        "seasonal_status": Column(
            "Seasonal Status",
            (
                """In season: Service code has been marked as seasonal by the operator or their agent and todays date falls within the relevant date range for that service code.
                <pre>                             Out of Season: Service code has been marked as seasonal by the operator or their agent and todays date falls outside the relevant date range for that service code.
                                             Not Seasonal: Default status for published or unpublished services to BODS.
                                             Assumed Not seasonal unless service code has been marked with a date range within the seasonal services flow.
                </pre>
                """
            ),
        ),
        "staleness_status": Column(
            "Timeliness Status",
            (
                """Up to date: Default status for service codes published to BODS.
                <pre>                             Timeliness checks are evaluated in this order:

                                             1) OTC variation not published:
                                             If 'XML:Last modified date' is earlier than 'Date OTC variation needs to be published'
                                             and
                                             'Date OTC variation needs to be published' is earlier than today's date.
                                             and
                                             No associated data has been published.
                                             NB there are two association methods:
                                             Method 1:
                                             Data for that service code has been updated 70 days before the OTC variation effective date.
                                             Method 2:
                                             Data for that service code has been updated with a 'XML:Operating Period Start Date' which equals OTC variation effective date.

                                             2) 42 day lookahead is incomplete:
                                             If not out of date due to 'OTC variation not published'
                                             and
                                             'XML:Operating Period End Date' is earlier than 'Date for complete 42 day look ahead'.

                                             3) Service hasn't been updated within a year:
                                             If not out of date due to '42 day lookahead is incomplete' or 'OTC variation not published'
                                             and
                                            'Date when data is over 1 year old' is earlier than today's date.
                </pre>
                """
            ),
        ),
        "organisation_name": Column(
            "Organisation Name",
            "The name of the operator/publisher providing data on BODS.",
        ),
        "dataset_id": Column(
            "Data set ID",
            "The internal BODS generated ID of the dataset "
            "that contains the data for this row.",
        ),
        "effective_stale_date_from_otc_effective": Column(
            "Date OTC variation needs to be published",
            "OTC:Effective date from timetable data catalogue minus 42 days.",
        ),
        "date_42_day_look_ahead": Column(
            "Date for complete 42 day look ahead",
            "Today's date + 42 days.",
        ),
        "effective_stale_date_from_last_modified": Column(
            "Date when data is over 1 year old",
            "'XML:Last Modified date' from timetable data catalogue plus 12 months.",
        ),
        "effective_seasonal_start": Column(
            "Date seasonal service should be published",
            "If Seasonal Start Date is present, then Seasonal Start Date minus "
            "42 days, else null.",
        ),
        "seasonal_start": Column(
            "Seasonal Start Date",
            "If service has been assigned a date range from within the seasonal "
            "services flow, then take start date, else null.",
        ),
        "seasonal_end": Column(
            "Seasonal End Date",
            "If service has been assigned a date range from within the "
            "seasonal services flow, then take end date, else null.",
        ),
        "filename": Column(
            "XML:Filename",
            "The exact name of the file provided to BODS. This is usually "
            "generated by the publisher or their supplier.",
        ),
        "last_modified_date": Column(
            "XML:Last Modified Date",
            "Date of last modified file within the service codes dataset.",
        ),
        "national_operator_code": Column(
            "XML:National Operator Code",
            "The National Operator Code(s) as extracted from the files provided "
            "by the operator/publisher to BODS.",
        ),
        "licence_number": Column(
            "XML:Licence Number",
            "The License number(s) as extracted from the files provided by "
            "the operator/publisher to BODS.",
        ),
        "public_use": Column(
            "XML:Public Use Flag",
            "The Public Use Flag element as extracted from the files provided "
            "by the operator/publisher to BODS.",
        ),
        "revision_number": Column(
            "XML:Revision Number",
            "The service revision number date as extracted from the files "
            "provided by the operator/publisher to BODS.",
        ),
        "operating_period_start_date": Column(
            "XML:Operating Period Start Date",
            "The operating period start date as extracted from the files provided "
            "by the operator/publisher to BODS.",
        ),
        "operating_period_end_date": Column(
            "XML:Operating Period End Date",
            "The operating period end date as extracted from the files "
            "provided by the operator/publisher to BODS.",
        ),
        "origin": Column(
            "OTC:Origin",
            "The origin element as extracted from the files provided by "
            "the operator/publisher to BODS.",
        ),
        "destination": Column(
            "OTC:Destination",
            "The destination element as extracted from the files provided "
            "by the operator/publisher to BODS.",
        ),
        "otc_operator_id": Column(
            "OTC:Operator ID",
            "The operator ID element as extracted from the OTC database.",
        ),
        "operator_name": Column(
            "OTC:Operator Name",
            "The operator name element as extracted from the OTC database.",
        ),
        "address": Column(
            "OTC:Address",
            "The address as extracted from the OTC database.",
        ),
        "otc_licence_number": Column(
            "OTC:Licence Number",
            "The licence number element as extracted from the OTC database.",
        ),
        "licence_status": Column(
            "OTC:Licence Status",
            "The licence status element as extracted from the OTC database.",
        ),
        "registration_number": Column(
            "OTC:Registration Number",
            "The registration number element as extracted from the OTC database.",
        ),
        "service_type_description": Column(
            "OTC:Service Type Description",
            "The service type description element as extracted from the OTC database.",
        ),
        "variation_number": Column(
            "OTC:Variation Number",
            "The variation number element as extracted from the OTC database.",
        ),
        "service_numbers": Column(
            "OTC:Service Number",
            "The service number element as extracted from the OTC database.",
        ),
        "start_point": Column(
            "OTC:Start Point",
            "The start point element as extracted from the OTC database.",
        ),
        "finish_point": Column(
            "OTC:Finish Point",
            "The finish point element as extracted from the OTC database.",
        ),
        "via": Column(
            "OTC:Via",
            "The via element as extracted from the OTC database.",
        ),
        "granted_date": Column(
            "OTC:Granted Date",
            "The granted date element as extracted from the OTC database.",
        ),
        "expiry_date": Column(
            "OTC:Expiry Date",
            "The expiry date element as extracted from the OTC database.",
        ),
        "effective_date": Column(
            "OTC:Effective Date",
            "The effective date element as extracted from the OTC database.",
        ),
        "received_date": Column(
            "OTC:Received Date",
            "The received date element as extracted from the OTC database.",
        ),
        "service_type_other_details": Column(
            "OTC:Service Type Other Details",
            "The service type other details element as extracted from the "
            "OTC database.",
        ),
        "traveline_region": Column(
            "OTC:Traveline Region",
            "The Traveline Region details element as extracted from the OTC database.",
        ),
        "local_authority_name": Column(
            "OTC:Local Authority",
            "The Local Authority element as extracted from the OTC database.",
        ),
        "local_authority_ui_lta": Column(
            "OTC:UI LTA",
            "The UI LTA element as extracted from the OTC database.",
        )
    }
)

LICENCE_NUMBER_NOT_SUPPLIED_MESSAGE = "Licence number not supplied"
