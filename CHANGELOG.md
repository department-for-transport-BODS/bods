# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Note changes prior to [0.1.0] are not documented as these changes were released internally.

## [1.18.0] - 2022-21-06

### Bug

BODP-5350 \[Regression\] AVL: Notifications - Agent/Admin receive double emails for publishing datasets

BODP-5347 \[Regression\] PBODS: Customer activity summary - API hits not reflected when query parameters are used

BODP-5343 \[Regression\] FBODS Operator Profile page: General UI - User is redirected to homepage after sign in.

BODP-5340 \[Regression\] AVL_API: General UI - Query ignores multiples inputs for the 'operatorRef' parameter

BODP-5333 \[Regression\] PBODS: Data Consumer Activity - Unable to download the "consumer interactions" file on Staging

BODP-5332 "Choose data type" always defaults to "Timetables" data type on the 'Review my published data' page

BODP-5331 \[Regression\] BODS Admin: Publisher Metrics - `feedback_report_operator_breakdown.csv` file is updated with a delay

BODP-5329 \[Regression\] PBODS Timetables/Fares/AVL: Publishing process stuck in validation step

BODP-5328 \[Regression\] PBODS Data Requiring Attention: General UI - Improve 'Service codes' table layout

BODP-5327 \[Regression\] Internal: Incorrect NOC Code Link in DQ service is showing Field Error

BODP-5325 \[Regression\] PBODS: New dashboard page - "Choose data type" option defaults to "Timetables" with each selection

BODP-5324 \[Regression\] BODS Admin: Publisher Metrics - `feedback_report_operator_breakdown.csv` file is empty on Staging

BODP-5321 Timetables Requiring Attention page has wrong breadcrumb for Agents

BODP-5320 Sorting by Line crashes in Data Requiring Attention

BODP-5319 AVL API requests not reflected correctly on consumer activity CSV download

BODP-5316 Staging: Existing users cannot login

BODP-5304 PBODS site: Timetables Data - Not possible to complete an upload process

BODP-5258 Django Admin: General UI - Search-box input is returning an Internal Server Error

BODP-5257 Review my Data: General UI - Incorrect behaviour for 'Choose data type' drop down input

BODP-5254 FBODS site: General UI - Unexpected wording for 'Service changelog' link

BODP-5243 AVL – validation reports are not available to Django admin user

BODP-5242 AVL – sync up the CAVL config API for inactive feeds with BODS status

BODP-5238 "Data sets" instead of "data feeds" text on "Bus location data" page

BODP-5156 FBODS Data Catalogue/Glossary - Page content not matching designs

BODP-5152 Some AVL records on Overall Data Catalogue have an incorrect status

BODP-5131 \[Regression\] FBODS Download: Timetables - Regional links display Inactive/Pending Invite organisations

BODP-5081 Data issue - "123 Ltd." is displayed as "Pending Invite" under "Active" filter

BODP-5076 Accessibility - Error using "Skip to main content" button without using the screen reader

BODP-5002 FBODS Developer documentation page: General UI - The 'Timetables data API parameters' section should be consistent with the Swagger UI

BODP-5001 FBODS Timetables API: Swagger UI - 'Error' status should not be listed as an option for the 'Status' parameter

BODP-4967 Accessibility page: General UI - Hyperlinks to third party sites should open in a new tab

BODP-4882 \[Regression\] PBODS Observation definitions page: General UI - AXE Analysis raise Critical issues

BODP-4576 \[Publisher\] Agent Publisher Timetables Dashboard: not listing all datasets and showing some datasets more than once

BODP-4528 \[Emails\] \(Regression\) Agent Notifications: General UI - 'Error publishing data set' email, wrong text on the second paragraph.

BODP-4525 \[Emails\] \(Regression\) Agent Notifications: General UI - 'Action required – PTI validation...' email, second parapgrah displays wrong template

BODP-4400 \[Users\] \(REGRESSION\) Organisation Management: General UI - 'Invitation has been re-sent' page is not showing

### Story

BODP-5344 Update the version of notifications-python-client from 5.7.1 to 6.3.0

BODP-5336 Changelog: Release Notes - June 2022 \(1.18.0\)

BODP-5267 Publisher-Timetables data requiring attention CSV

BODP-5266 Publisher-Timetables data requiring attention

BODP-5265 Publisher-Timetables data requiring attention: addition of search box

BODP-5264 Publisher- Location and Fares data Review page UI changes as per new design

BODP-5263 Publisher - Timetable data Review page UI changes as per new design

BODP-5262 Publisher- Timetables data - Addition of Tool tip for timetables data requiring attention

BODP-5261 Publishers- Timetables data- Creation of the tool tip explaining what line is

BODP-5260 Agent- General- Dashboard Review my published data page for Agent \(without notification centre\)

BODP-5259 Publisher-Review page: Hyperlink addition for license set up

BODP-5255 BODS PTI Profile validation - Versioning - CreationDataTime

BODP-5179 SIRI-VM compliance: addition of new status. This will enable the user to understand that for inactive feeds the validation has failed

BODP-5157 Package upgrade

BODP-5146 Removal of disruptions API link: this will remove the hyperlink relating to disruptions on BODS \(which will come in the future\)

BODP-5145 Additional CSV for C&M: feedback issues: this will enable the BCM/DfT team to have complete oversight of all the feedback on specific data sets/feeds that are provided to operators by consumers.

BODP-5144 New summary PTI report: this enables the publisher to have a high-level view of their PTI observations

BODP-5143 CSV 2 for consumer activity \(feedback issues\): This will enable the publishers to have a centralized place where they can see all of their feedback, henceforth improving transparency and their ability to track/reply to feedback.

BODP-5142 CSV 1 for consumer activity \(consumer interactions\): This will enable the publishers to directly understand how consumers are using their data. This is a novel feature that wasn’t available before.

BODP-5141 Logic and UI for consumers accessing BODS data page: This will enable the publishers to directly understand how consumers are using their data. This is a novel feature that wasn’t available before

BODP-5138 Post Publishing check reports\[Second Draft\]

BODP-5089 Logic for Data requiring attention \(Location data\): this will enable the user to auto-triage AVL data \(prev manually done\) and identify the things they should be spending most of their time reviewing on BODS

BODP-5087 Logic for review page Consumer counter: This will enable the publishers to readily view the amount of consumer interactions on their data in the last 7 days

BODP-5086 Review my published data Fares \(Publisher admin \+ standard\): This will enable users to review some high level extra info about their data e.g data consumers

BODP-5085 Review my published data AVL \(Publisher admin \+ standard\): This will enable users to review some high level extra info about their data e.g data consumers

BODP-5084 Review my Published Data Timetables \(Publisher admin \+ standard \+ Agent\): This will enable users to review some high level extra info about their data e.g OTC matching & data consumers for timetables

BODP-5073 PE2E: Information Page to be shown when user do not have access to links from Guide Me page. This will enable users to understand which pages they don’t have access to

BODP-5072 PE2E: New Guide me page for Publisher Admin \+ Agent \+ Staff, this will enable the publisher to view a more helpful step by step guide

BODP-5049 PE2E: Publish homepage \(Publisher Admin \+ Publisher Standard \+ Publisher admin\)

BODP-5048 PE2E: Bus Open data Service Landing page

BODP-5047 Header updates 2: Publisher BODS

BODP-5024 Analysis - Post Publishing check reports\[First Draft\]

## [1.17.3] - 2022-17-06

### Bug

BODP-5337 \[Regression\] PBODS Timetables: Unable to publish a valid file

## [1.17.2] - 2022-06-06

### Story

BODP-5275 Data Retention - API requests table clean-up script

## [1.17.1] - 2022-04-14

### Bug

BODP-5097 Staging_Publisher_Publishing Timetables Update: Data that should pass validation is failing when uploaded as an update to an existing published datsaet

BODP-4874 TransXchange Error: unexpectedly failed the PTI validation check when updating timetable datasets

## [1.17.0] - 2022-04-01

### Bug

BODP-5136 \[Regression\] Admin_Publisher: General UI - Org Admin user can't remove an Agent

BODP-5135 \[Regression\] PBODS Publisher: General UI - Unexpected body text on Create Account form

BODP-5134 \[Regression\] FBODS: API - Accessibility warnings on "data API" pages for Timetables, Locations and Fares

BODP-5133 \[Regression\] FBODS Download: General UI - User without been logged in should be redirected to the Sign In page

BODP-5130 \[Regression\] BODS Admin - User initially not taken to "Organisation management" when clicking on that link

BODP-5129 \[Regression\] BODS Admin - "Sort by" doesn't work on "Organisation management" data sets pages

BODP-5128 \[Regression\] FBODS: Browse & Download - Comma at the end of sentence on "Developer documentation > Overview" page

BODP-5124 \[Regression\] FBODS Data Catalogue/Glossary - Page content not matching the document - typos only

BODP-5122 \[Added in error\] FBODS: All - Data doesn't correspond with column names in "overall_data_catalogue.csv"

BODP-5117 \[Regression\] BODS Admin: Admin - Expired data sets listed in Django Admin

BODP-5116 \[KPMG Regression\] AVL: After deactivating the AVL feed, the datafeed is not showing up on the inactive tab

BODP-5115 \[Regression\] BODS Admin: Timetables - Timetables data sets listed as 'Expired' status

BODP-5114 \[Regression\] BODS Admin: Admin_Metrics - 'Consumer Name' column do not populate in 'rawapimetrics.csv' file

BODP-5112 \[Regression\] BODS Admin: General UI - Organisation timetables/fares data set page display unexpected Status

BODP-5111 \[Regression\] BODS Admin: General UI - Organisation location data feeds page display unexpected Statuses

BODP-5110 \[Regression\] FBODS: All - "Data quality" page not displayed in FBODS > Guidance section

BODP-5043 \[KPMG Regression\] AVL: After deactivating the AVL feed, the datafeed is not showing up on the inactive tab

BODP-5033 Duplicate | Developer documentation - Add guidance on GTFS and GTFS-RT are missing on page

BODP-5019 General UI: Update to 'dataset' instead of datafeed for text in PBODS errored file

BODP-5014 Changelog: Update for patch release / 1.17.0 - take out OTC info

BODP-4957 PBODS User Management: User Management - Clicking on user "test123abc@gmail.com" causes \(500\) Internal Server Error

BODP-4878 \[Regression\] PBODS Fares publishing page: General UI - AXE Analysis raise two critical issues

BODP-4674 \[Publishing\] 'Fares Data Browser' page: General UI - Data sets with the status 'Expired' or 'Error' shouldn't be listed

### Story

BODP-5160 Changelog: Release Notes - April 2022 \(1.17.0\)

BODP-5050 Developer documentation: Updates to Maintaining data quality section

BODP-5046 Developer documentation: Add GTFS details to Data formats section

BODP-5045 DfT admin portal update: dailyaggregates \(with download all\) - this would enable the admin user to report on the usage of download all on a daily aggregate basis

BODP-5044 DfT admin portal update: Consumerbreakdownmetrics \(with download all\) - this would enable the admin user to report on the usage of download all on a per consumer per day basis.

BODP-5005 Duplicate | Developer documentation - Updates to Data Quality guidance

BODP-4961 DfT Admin - UI change to Data Consumers, Agents, Organisation Management screen for filtering data on screen

BODP-4927 FBODS: All location data - add GTFS-RT data type in Data Format list and respective tooltip which was missing

BODP-4925 BODS admin portal: In data catalogue file populate the email ID of whoever made the last manual change to the data set for system updates so that DfT Admin is able to chase them up when something is wrong within the data set

BODP-4924 Update Accessibility statement page to make it inline with current updates

BODP-4922 DfT admin portal: Data consumers - I would like to be sort the columns in data consumers So that I can find the data consumer I want much faster

BODP-4921 DfT admin portal: Agents - I would like to be sort the first two columns in Agent So that I can find the Agent organisation and contact I want much faster

BODP-4920 DfT admin portal: Agents - I would like to be able to filter alphabetically using a checkbox So that I am able to easily find the agent user I’m looking for.

BODP-4919 DfT admin portal: Agents - I would like to be able to search agent organisation names or emails using a search bar So that I am able to easily find the agent I’m looking for.

BODP-4918 DfT Admin portal: Org Management - I would like to be able to filter alphabetically using a checkbox So that I am able to easily find the organisation I’m looking for.

BODP-4917 DfT Admin portal: Org Management - I would like to be able to search orgs using a search bar So that I am able to easily find what I’m looking for.

BODP-4916 DfT Admin portal: Data consumers - I would like to be able to filter alphabetically using a checkbox So that I am able to easily find the data consumer I’m looking for

BODP-4915 DfT Admin portal: Data consumers - I would like to be able to search data consumers using a search bar So that I am able to easily find what I’m looking for

BODP-4827 \[Tech debt\] Improve logging around Django app

BODP-4819 \[Tech debt\] Refactor Dataset models code

BODP-4817 \[Tech debt\] Remove expired/expiring datasets

BODP-4807 \[Tech debt\] Remove unused feature flags

BODP-4803 \[Tech debt\] Refactor package name/structure/views to use Python conventions

BODP-4801 \[Tech debt\] Refactor Data quality service checks that still use pandas so that they use the non pandas method

BODP-4799 \[Tech debt\] Moving and building front-end in BODS package

BODP-4797 \[Tech debt\] Build Crispforms_GovUK as PY PI application

BODP-4795 \[Tech debt\] CAVL Client - Re-implement the CAVL client in a more concise way and move it into BODS

BODP-4793 \[Tech debt\] Increase unit test coverage

## [1.16.4] - 2022-03-04

### Bug

BODP-5032 \[DataCatalogue\] Organisations data catalogue file: Is not displaying the expected information for the published Timetables Services

BODP-5017 SIRI-VM TfL download times out on production

BODP-5012 \[Data Catalogue\] Improve query performance to generate Organisation.csv file

### Story

BODP-4986 \[APIV2\] Retrieve avl data feed details via the API - Detail

BODP-4984 \[APIV2\] Retrieve avl data feed details via the API - List

BODP-4982 \[APIV2\] Retrieve timetable file details via the API - Detail

BODP-4980 \[APIV2\] Retrieve timetable file details via the API - List

BODP-4978 \[APIV2\] Retrieve timetable datasets via the API - List

BODP-4976 \[APIV2\] Retrieve a timetable dataset via the API - Detail

BODP-4974 \[APIV2\] Retrieve an operator/organisation via the API - Detail

BODP-4972 \[APIV2\] Retrieve operators/organisations via the API - List

## [1.16.3] - 2022-02-21

### Bug

BODP-4998 \[DataCatalogue\] Data catalogue zip files fail to generate on Production

## [1.16.2] - 2022-02-17

### Bug

BODP-4968 \[PTI\] Invalid ServiceCode passes PTI check

### Story

BODP-4969 \[PTI\]Disable Service Code OTC validation check

## [1.16.1] - 2022-02-17

### Story

- BODP-4737 TFL Download all link

## [1.16.0] - 2022-02-03

### Bug

- [BODP-4890](https://itoworld.atlassian.net/browse/BODP-4890) \(Regression\) Publishing data: Timetables - Uploading a TXC file with multiple causes system error
- [BODP-4887](https://itoworld.atlassian.net/browse/BODP-4887) \[Regression\] Location data download: General UI - The GTFS RT bin file populates with an error message
- [BODP-4886](https://itoworld.atlassian.net/browse/BODP-4886) \(REGRESSION\) PBODS Data set / feed details page: General UI - The short description field value is not inline
- [BODP-4884](https://itoworld.atlassian.net/browse/BODP-4884) \(REGRESSION\) BODS Admin Organisation User Management : Re-inviting a user with no email address causes 500 - Internal Server Error
- [BODP-4883](https://itoworld.atlassian.net/browse/BODP-4883) \[Regression\] Invite new user page: General UI - AXE Analysis raise a Critical issue
- [BODP-4882](https://itoworld.atlassian.net/browse/BODP-4882) \[Regression\] PBODS Observation definitions page: General UI - AXE Analysis raise Critical issues
- [BODP-4880](https://itoworld.atlassian.net/browse/BODP-4880) \(REGRESSION\) FBODS Timetable Data Details Page: General UI - PTI compliant datasets has the "Download validation report" link
- [BODP-4879](https://itoworld.atlassian.net/browse/BODP-4879) \[Regression\] PBODS Timetables publishing page: General UI - AXE Analysis raise Critical and Serious issues for the 'Choose file' input
- [BODP-4878](https://itoworld.atlassian.net/browse/BODP-4878) \[Regression\] PBODS Fares publishing page: General UI - AXE Analysis raise two critical issues
- [BODP-4877](https://itoworld.atlassian.net/browse/BODP-4877) \[Regression\] FBODS Timetables Detail page: General UI - Breadcrumb links should be consistent across the Browse section
- [BODP-4876](https://itoworld.atlassian.net/browse/BODP-4876) \[Regression\] PBODS Update AVL page: General UI - Axe Analysis raise a Serious issue
- [BODP-4875](https://itoworld.atlassian.net/browse/BODP-4875) \[Regression\] FBODS Fares Detail Page: General UI - 'Expired' data set is not displaying the map
- [BODP-4873](https://itoworld.atlassian.net/browse/BODP-4873) \(REGRESSION\) FBODS: Location Data Swagger API - Making a request with no parameter values causes the page to crash
- [BODP-4872](https://itoworld.atlassian.net/browse/BODP-4872) Cannot open the ZIP file of timetable's validation report on staging
- [BODP-4871](https://itoworld.atlassian.net/browse/BODP-4871) \[Regression\] PBODS Data feed detail page: General UI - 'My account' dropdown button does not expand
- [BODP-4870](https://itoworld.atlassian.net/browse/BODP-4870) \(REGRESSION\) PBODS: DQS Service - The Review & Publish page does not automatically refresh the page when the DQ report is available.
- [BODP-4868](https://itoworld.atlassian.net/browse/BODP-4868) \(REGRESSION\) FBODS Fares Data Details: General UI - The tab name in the <title> tag is incorrect
- [BODP-4865](https://itoworld.atlassian.net/browse/BODP-4865) \[Regression\] PBODS Location Detail page: General UI - The counter for 'Feeds need attention' should include the Dormant feeds
- [BODP-4859](https://itoworld.atlassian.net/browse/BODP-4859) \[Regression\] Location Data Detail Page: General UI - 'Awaiting Publisher Review' status should display the 'Download validation report' link
- [BODP-4842](https://itoworld.atlassian.net/browse/BODP-4842) Publisher is being sent daily emails about Non-Compliant, Partially Compliant and Dormant AVL Feeds
- [BODP-4772](https://itoworld.atlassian.net/browse/BODP-4772) Text update: SIRI VM 2.0, not 2.4
- [BODP-4761](https://itoworld.atlassian.net/browse/BODP-4761) General UI: Text update to the Download All AVL download upgraded to 10 seconds
- [BODP-4753](https://itoworld.atlassian.net/browse/BODP-4753) Transmach unable to publish AVL data
- [BODP-4720](https://itoworld.atlassian.net/browse/BODP-4720) GTFS RT download link says GTFS only
- [BODP-4688](https://itoworld.atlassian.net/browse/BODP-4688) General UI - The listed parameters for Bus location should be the same as the swagger API
- [BODP-4687](https://itoworld.atlassian.net/browse/BODP-4687) Developer documentation: General UI - The listed parameters for Timetables should be the same as the swagger API
- [BODP-4621](https://itoworld.atlassian.net/browse/BODP-4621) \[Users\] Invite New Organisation: BODS Admin - Inviting a new organisation with an email address that already exists in the database where the invite was not accepted produces Error 500 - Internal Server Error
- [BODP-4589](https://itoworld.atlassian.net/browse/BODP-4589) \[Data\] Timetable Dataset 255 from Go-ahead was disappeared because of a wrong status of Live revision on Django
- [BODP-4588](https://itoworld.atlassian.net/browse/BODP-4588) AVL contact data feed owner directly: General UI - The link and page when clicked is displaying "dataset"
- [BODP-4586](https://itoworld.atlassian.net/browse/BODP-4586) \[PTI\] STAGING Timetables DQ / Timetables: NationalOperatorCode and OperatorCode throwing different errors for DQ and PTI
- [BODP-4571](https://itoworld.atlassian.net/browse/BODP-4571) A file without bank holidays passes PTI validation
- [BODP-4566](https://itoworld.atlassian.net/browse/BODP-4566) CLONE - PBODS My Account Dropdown Agent: General UI - Clicking on "My account" and "Account settings" causes dropdown to not display "My account" and "Organisation profile"
- [BODP-4565](https://itoworld.atlassian.net/browse/BODP-4565) CLONE - PBODS My Account Dropdown Org Staff: General UI - Clicking on "My account" and "Account settings" causes dropdown to not display "My account" and "Organisation profile"
- [BODP-4560](https://itoworld.atlassian.net/browse/BODP-4560) PBODS My Account Dropdown Agent: General UI - Clicking on "My account" and "Account settings" causes dropdown to not display "My account" and "Organisation profile"
- [BODP-4559](https://itoworld.atlassian.net/browse/BODP-4559) PBODS My Account Dropdown Org Staff: General UI - Clicking on "My account" and "Account settings" causes dropdown to not display "My account" and "Organisation profile"
- [BODP-4557](https://itoworld.atlassian.net/browse/BODP-4557) PBODS My Account Dropdown: General UI - Clicking on "Account settings" in the dropdown directs the user to the BODS Admin "Account setting" page
- [BODP-4556](https://itoworld.atlassian.net/browse/BODP-4556) PBODS My Account Dropdown Org Admin: General UI - Clicking on "My account" and "Account settings" causes dropdown to not display "My account", "User management" and "Organisation profile"
- [BODP-4555](https://itoworld.atlassian.net/browse/BODP-4555) FBODS My Account Dropdown: General UI - Clicking on "My account" in the dropdown does not display "Account settings" link in the "My account page"
- [BODP-4554](https://itoworld.atlassian.net/browse/BODP-4554) FBODS My Account Dropdown: General UI - Clicking on "Account settings" in the dropdown directs the user to the BODS Admin "Account setting" page
- [BODP-4553](https://itoworld.atlassian.net/browse/BODP-4553) FBODS My Account Dropdown: General UI - Clicking on "My account" and "Account settings" causes dropdown to not display "My account" and "Manage subscriptions"
- [BODP-4552](https://itoworld.atlassian.net/browse/BODP-4552) All timetables data: Timetables - Download data set updates in TransXChange format generating duplicate of days links causing MultipleObjectsReturned exception
- [BODP-4539](https://itoworld.atlassian.net/browse/BODP-4539) \[AXE\] API \(timetables\): General UI - axe-core accessibility tool raised Critical issues for multi-select fields and dropdown field
- [BODP-4538](https://itoworld.atlassian.net/browse/BODP-4538) \[AXE\] API \(timetables\): General UI - axe-core accessibility tool raised Serious issues for elements that have insufficient colour contrast
- [BODP-4537](https://itoworld.atlassian.net/browse/BODP-4537) \[AXE\] API \(timetables\): General UI - axe-core accessibility tool raised critical issues for the "servers" drop down
- [BODP-4521](https://itoworld.atlassian.net/browse/BODP-4521) \[Guidance\] Data Quality page: General UI - Schema Validation information is not listed
- [BODP-4472](https://itoworld.atlassian.net/browse/BODP-4472) \[Users\] Error handling request /account/signup
- [BODP-4451](https://itoworld.atlassian.net/browse/BODP-4451) \[Bulk Downloads\] GTFS \(TfWM\) Downloadable Timetable Data Errors
- [BODP-4399](https://itoworld.atlassian.net/browse/BODP-4399) \(REGRESSION\) My account \(BODS Admin\): General UI - Missing 'Account settings' link, body paragraph and dropdown menu
- [BODP-4392](https://itoworld.atlassian.net/browse/BODP-4392) \[Changelog\] Fail to create an entry in changelog after Automated update for Fares
- [BODP-4377](https://itoworld.atlassian.net/browse/BODP-4377) \[DQS\] Incorrectly flagging a stop as not on naptan although it is present on naptan download
- [BODP-4340](https://itoworld.atlassian.net/browse/BODP-4340) Changelog page: Right-hand section Heading - AXE Analysis raise one moderate issue
- [BODP-4258](https://itoworld.atlassian.net/browse/BODP-4258) \[DQS\] DQ Report: where the line description and/or the data it links to, does not relate to operators services.
- [BODP-4187](https://itoworld.atlassian.net/browse/BODP-4187) \[DQS\] DQ report lists observations for lines belonging to different operator
- [BODP-3783](https://itoworld.atlassian.net/browse/BODP-3783) Send AVL feed down notification is throwing error.
- [BODP-2362](https://itoworld.atlassian.net/browse/BODP-2362) \[AXE\] Map element on observation page must not contain focus-able element

### Story

- [BODP-4888](https://itoworld.atlassian.net/browse/BODP-4888) Changelog: Release Notes - February 2022 \(1.16.0\)
- [BODP-4814](https://itoworld.atlassian.net/browse/BODP-4814) FBODS data catalogue: Location data CSV
- [BODP-4813](https://itoworld.atlassian.net/browse/BODP-4813) C&M: Location data CSV
- [BODP-4758](https://itoworld.atlassian.net/browse/BODP-4758) C&M: Overall data catalogue
- [BODP-4757](https://itoworld.atlassian.net/browse/BODP-4757) FBODS data catalogue: Overall Data catalogue CSV
- [BODP-4755](https://itoworld.atlassian.net/browse/BODP-4755) FBODS Data catalogue \(functionality story\)
- [BODP-4742](https://itoworld.atlassian.net/browse/BODP-4742) C&M: Organisations data catalogue
- [BODP-4741](https://itoworld.atlassian.net/browse/BODP-4741) C&M: Timetables data catalogue
- [BODP-4740](https://itoworld.atlassian.net/browse/BODP-4740) FBODS data catalogue: Organisations data catalogue
- [BODP-4738](https://itoworld.atlassian.net/browse/BODP-4738) FBODS data catalogue: Timetables data catalogue
- [BODP-4732](https://itoworld.atlassian.net/browse/BODP-4732) Download all timetables data: Folder structure update
- [BODP-4648](https://itoworld.atlassian.net/browse/BODP-4648) FBODS: Contact Operator page \(Signed in only\)
- [BODP-4647](https://itoworld.atlassian.net/browse/BODP-4647) FBODS: Operator Profile page \(signed in\)
- [BODP-4646](https://itoworld.atlassian.net/browse/BODP-4646) FBODS: Specific Operator Profile page \(signed out\)
- [BODP-4645](https://itoworld.atlassian.net/browse/BODP-4645) FBODS: View Operator Profile page \(Operator List View\)
- [BODP-4644](https://itoworld.atlassian.net/browse/BODP-4644) FBODS: Browse data page
- [BODP-4643](https://itoworld.atlassian.net/browse/BODP-4643) FBODS: Homepage
- [BODP-4642](https://itoworld.atlassian.net/browse/BODP-4642) API \(location data\): Adding BODS comlpiance and Vehicleref as new query parameters
- [BODP-4606](https://itoworld.atlassian.net/browse/BODP-4606) Modal Popup for AVL Datafeed Details
- [BODP-4604](https://itoworld.atlassian.net/browse/BODP-4604) Modal Popup for Timetable Dataset Details
- [BODP-4581](https://itoworld.atlassian.net/browse/BODP-4581) Download all data homepage
- [BODP-4580](https://itoworld.atlassian.net/browse/BODP-4580) Browse data timetables
- [BODP-4578](https://itoworld.atlassian.net/browse/BODP-4578) Fares API update
- [BODP-4577](https://itoworld.atlassian.net/browse/BODP-4577) FBODS: Case study page
- [BODP-4575](https://itoworld.atlassian.net/browse/BODP-4575) Updating the CSV naming for the PTI validation report.
- [BODP-4574](https://itoworld.atlassian.net/browse/BODP-4574) API homepage : for Logged out user
- [BODP-4481](https://itoworld.atlassian.net/browse/BODP-4481) Implement Django functionalities to enable TfL datafeed in BODS. \(UI\)
- [BODP-4480](https://itoworld.atlassian.net/browse/BODP-4480) Download all timetables data
- [BODP-4477](https://itoworld.atlassian.net/browse/BODP-4477) API \(Location data\)
- [BODP-4476](https://itoworld.atlassian.net/browse/BODP-4476) API \(timetables\)
- [BODP-4475](https://itoworld.atlassian.net/browse/BODP-4475) API \(fares data\)
- [BODP-4474](https://itoworld.atlassian.net/browse/BODP-4474) API \(homepage\): For Logged in User
- [BODP-4452](https://itoworld.atlassian.net/browse/BODP-4452) FBODS: Updated character limit of 'Descriptions' in registrations page
- [BODP-4446](https://itoworld.atlassian.net/browse/BODP-4446) PTI: Just-in-Time Servicecode check
- [BODP-4427](https://itoworld.atlassian.net/browse/BODP-4427) No reply email for the Feedback function
- [BODP-4425](https://itoworld.atlassian.net/browse/BODP-4425) Search for Fares dataset
- [BODP-4422](https://itoworld.atlassian.net/browse/BODP-4422) Browse data fares data
- [BODP-4421](https://itoworld.atlassian.net/browse/BODP-4421) FBODS Guide me page
- [BODP-4419](https://itoworld.atlassian.net/browse/BODP-4419) Search for AVL feeds
- [BODP-4418](https://itoworld.atlassian.net/browse/BODP-4418) Location data: Individual data set page
- [BODP-4417](https://itoworld.atlassian.net/browse/BODP-4417) Fares: Individual data set page
- [BODP-4416](https://itoworld.atlassian.net/browse/BODP-4416) Timetables: Individual data set page
- [BODP-4415](https://itoworld.atlassian.net/browse/BODP-4415) Addition of GA tags on events
- [BODP-4414](https://itoworld.atlassian.net/browse/BODP-4414) Download all location data
- [BODP-4413](https://itoworld.atlassian.net/browse/BODP-4413) Download all fares data
- [BODP-4412](https://itoworld.atlassian.net/browse/BODP-4412) Admin - Export - Stats - Adding 3 columns for number of services
- [BODP-4411](https://itoworld.atlassian.net/browse/BODP-4411) ADMIN - Stats - AVL feed status update in the data catalogue
- [BODP-4405](https://itoworld.atlassian.net/browse/BODP-4405) Browse AVL feeds
- [BODP-4376](https://itoworld.atlassian.net/browse/BODP-4376) FBODS: new user guide overview
- [BODP-4375](https://itoworld.atlassian.net/browse/BODP-4375) FBODS Data Catalogue/Glossary
- [BODP-4374](https://itoworld.atlassian.net/browse/BODP-4374) FBODS: Updated registrations page
- [BODP-4373](https://itoworld.atlassian.net/browse/BODP-4373) Update Banner Bus Open Data
- [BODP-4372](https://itoworld.atlassian.net/browse/BODP-4372) BODS main home page
- [BODP-4123](https://itoworld.atlassian.net/browse/BODP-4123) View License number in Organisation profile: Publisher non-admin
- [BODP-3782](https://itoworld.atlassian.net/browse/BODP-3782) Ingest OTC data into BODS
- [BODP-3478](https://itoworld.atlassian.net/browse/BODP-3478) Agent Mode Email updates
- [BODP-3476](https://itoworld.atlassian.net/browse/BODP-3476) AVL Emails

### Story Bug

- [BODP-4861](https://itoworld.atlassian.net/browse/BODP-4861) \[AXE\] 'Case studies' page: General UI - AXE Analysis raise a Critical issue for the used images
- [BODP-4860](https://itoworld.atlassian.net/browse/BODP-4860) FBODS data catalogue: Overall Data catalogue CSV - No field name for column O
- [BODP-4858](https://itoworld.atlassian.net/browse/BODP-4858) FBODS: Location Data Catalogue - The 'Compliant' and 'Unavailable due to dormant feed' statuses should not have validation report links
- [BODP-4854](https://itoworld.atlassian.net/browse/BODP-4854) FBODS: Download Data Catalogue - 'DQ Score' values are rounding upwards the numbers for each percentage
- [BODP-4853](https://itoworld.atlassian.net/browse/BODP-4853) FBODS: Location Data Catalogue - 'Expired' and 'Inactive' data feeds shouldn't be listed on the CSV
- [BODP-4851](https://itoworld.atlassian.net/browse/BODP-4851) FBODS Data Catalogue: Functionality story - The column names in the overall data catalogue section of the data_catalogue_guidance.txt file does not match what's in overall_data_catalogue.csv
- [BODP-4850](https://itoworld.atlassian.net/browse/BODP-4850) FBODS Data Catalogue: Functionality story - The column names in the timetables data catalogue section of the data_catalogue_guidance.txt file does not match what's in timetables_data_catalogue.csv
- [BODP-4849](https://itoworld.atlassian.net/browse/BODP-4849) FBODS Data Catalogue: Functionality story - The data_catalogue_guidance.txt does not include information about the "location_data_catalogue" CSV
- [BODP-4848](https://itoworld.atlassian.net/browse/BODP-4848) FBODS Data Catalogue: Functionality story - The data_catalogue_guidance.txt does not include information about the "operator_noc_data_catalogue" CSV
- [BODP-4847](https://itoworld.atlassian.net/browse/BODP-4847) FBODS Data Catalogue: Functionality story - The organisations data catalogue section in data_catalogue_guidance.txt is not readable
- [BODP-4846](https://itoworld.atlassian.net/browse/BODP-4846) FBODS Data Catalogue: Organisations data catalogue - Mismatch of number of published datasets for Timetables and AVL between the CSV and FBODS
- [BODP-4845](https://itoworld.atlassian.net/browse/BODP-4845) FBODS Data Catalogue: Organisations data catalogue - Incorrect column names in the csv
- [BODP-4812](https://itoworld.atlassian.net/browse/BODP-4812) FBODS Data Catalogue: Overall Data catalogue CSV - Incorrect column names in the csv
- [BODP-4811](https://itoworld.atlassian.net/browse/BODP-4811) FBODS Data Catalogue: Overall Data catalogue CSV - The "Profile NOCS" and "TxC File Name" columns should not be in the csv
- [BODP-4810](https://itoworld.atlassian.net/browse/BODP-4810) FBODS: Data Catalogue - Operator "123 Ltd." has the incorrect Permit Holder status
- [BODP-4809](https://itoworld.atlassian.net/browse/BODP-4809) Download Timetables Data: General UI - 'All - Download timetables data...' download is not showing the expected number of files
- [BODP-4792](https://itoworld.atlassian.net/browse/BODP-4792) FBODS: Timetables Data Catalogue - 'DQ Score' column should display the assigned percentage for the Published dataset
- [BODP-4791](https://itoworld.atlassian.net/browse/BODP-4791) FBODS: Data Catalogue - Incorrect file name for the csv
- [BODP-4790](https://itoworld.atlassian.net/browse/BODP-4790) FBODS: Data Catalogue - "Number of Fares Products" in the organisationsdatacatalougue.csv does not match what's on PBODS and FBODS
- [BODP-4789](https://itoworld.atlassian.net/browse/BODP-4789) FBODS: Timetables Data Catalogue - 'Expired' and 'Inactive' data sets shouldn't be listed on the CSV
- [BODP-4788](https://itoworld.atlassian.net/browse/BODP-4788) FBODS: Timetables Data Catalogue - 'BODS Compliant' column should display the values 'YES/NO'
- [BODP-4786](https://itoworld.atlassian.net/browse/BODP-4786) FBODS: Data Catalogue - Incorrect folder name
- [BODP-4785](https://itoworld.atlassian.net/browse/BODP-4785) FBODS: Data Catalogue - NOC codes and Licence Numbers are populating in the wrong columns in the organisationsdatacatalougue.csv file
- [BODP-4784](https://itoworld.atlassian.net/browse/BODP-4784) FBODS: Data Catalogue - The organisationsdatacatalougue.csv file missing columns
- [BODP-4783](https://itoworld.atlassian.net/browse/BODP-4783) FBODS: Data Catalogue - Missing column references despite data recorded within those columns
- [BODP-4781](https://itoworld.atlassian.net/browse/BODP-4781) FBODS: Data Catalogue - "download the Data Catalogue" link is returning 502
- [BODP-4739](https://itoworld.atlassian.net/browse/BODP-4739) FBODS Operator Profile page \(signed in\): General UI - The number of Non-compliant timetable datasets in Operator Profile page does not match with the number in the browse timetable data page
- [BODP-4736](https://itoworld.atlassian.net/browse/BODP-4736) Operator Profile page: General UI - 'Contact \(operator\)' link should redirect the user to the 'Sign In' page when the user is not logged in
- [BODP-4735](https://itoworld.atlassian.net/browse/BODP-4735) Operator Profile page: General UI - 'Location data' section doesn't display the correct number for 'Non-compliant' feeds
- [BODP-4734](https://itoworld.atlassian.net/browse/BODP-4734) Contact Operator page \(Signed in only\) - Clicking on the "Back" link does not take the user back to the Operator Profile detail page
- [BODP-4733](https://itoworld.atlassian.net/browse/BODP-4733) AVL Data feed Details Page: General UI - The c in "compliant" is not capitalised
- [BODP-4731](https://itoworld.atlassian.net/browse/BODP-4731) Contact Operator page \(Signed in only\) - Clicking on the Contact \[org\] link goes to the Coming soon page
- [BODP-4730](https://itoworld.atlassian.net/browse/BODP-4730) Modal pop up: General UI - Typo error from the Zeplin designs
- [BODP-4729](https://itoworld.atlassian.net/browse/BODP-4729) Modal pop up: General UI - Mapbox buttons overlaps the modal pop up
- [BODP-4728](https://itoworld.atlassian.net/browse/BODP-4728) Operator Profile page: General UI - When the user is not logged in, an exception error is displayed
- [BODP-4726](https://itoworld.atlassian.net/browse/BODP-4726) AVL Data feed Details Page: General UI - BODS Compliance Status value is not inline with the heading in the row
- [BODP-4725](https://itoworld.atlassian.net/browse/BODP-4725) FBODS Operator Profile page \(signed in\): General UI - Incorrect link destination for "What does this mean?"
- [BODP-4724](https://itoworld.atlassian.net/browse/BODP-4724) FBODS Operator Profile page \(signed in\): General UI - The text in the SIRI-VM modal box in the download all data page is missing a full stop
- [BODP-4723](https://itoworld.atlassian.net/browse/BODP-4723) FBODS Operator Profile page \(signed in\): API Request URLs - The query parameters in the request urls does not match the design
- [BODP-4722](https://itoworld.atlassian.net/browse/BODP-4722) FBODS Operator Profile page \(signed in\): General UI - The API snippet boxes does not match the designs
- [BODP-4721](https://itoworld.atlassian.net/browse/BODP-4721) AVL BODS compliant data modal box: General UI - Grammatical errors
- [BODP-4719](https://itoworld.atlassian.net/browse/BODP-4719) AVL Data feed Details Page: General UI - "Awaiting Publisher Reviewer" should not display the black information icon
- [BODP-4718](https://itoworld.atlassian.net/browse/BODP-4718) AVL Data feed Details Page: General UI - "Non-Compliant", "Partially Compliant" and "Awaiting Publisher Reviewer" being displayed as "property.avl_compliance"
- [BODP-4713](https://itoworld.atlassian.net/browse/BODP-4713) Download TImetables data: Admin - No GA event tag on one of the TransXChange format links
- [BODP-4712](https://itoworld.atlassian.net/browse/BODP-4712) Download Timetables data: General UI - Content of the link don't match to the designs
- [BODP-4710](https://itoworld.atlassian.net/browse/BODP-4710) Download Timetables data: General UI - Content of the links don't match to the designs
- [BODP-4709](https://itoworld.atlassian.net/browse/BODP-4709) Download Timetables data: General UI - If the user is not logged in must be taken to the Sign in page
- [BODP-4708](https://itoworld.atlassian.net/browse/BODP-4708) Download Timetables data: General UI - Breadcrumb don't match to the designs
- [BODP-4703](https://itoworld.atlassian.net/browse/BODP-4703) FBODS View Operator Profile page \(Operator List View\): Search bar - Clicking on one of the smart suggestions does not change the list view
- [BODP-4695](https://itoworld.atlassian.net/browse/BODP-4695) FBODS View Operator Profile page \(Operator List View\): General UI - Grey placeholder block is too wide and does not touch horizontal line
- [BODP-4694](https://itoworld.atlassian.net/browse/BODP-4694) FBODS: Browse data page: Timetables - The "found here" link in the modal box pointing to the wrong page
- [BODP-4692](https://itoworld.atlassian.net/browse/BODP-4692) Browse Timetables page: General UI - Search by 'Location' doesn't provide the expected results
- [BODP-4691](https://itoworld.atlassian.net/browse/BODP-4691) Browse Timetables page: General UI - Update position and content of 'BODS compliant data' row
- [BODP-4690](https://itoworld.atlassian.net/browse/BODP-4690) Browse Timetables page: General UI - Breadcrumb should match the Heading title
- [BODP-4689](https://itoworld.atlassian.net/browse/BODP-4689) FBODS Browse data page: General UI - The heading and paragraph in the banner does not align to the body content
- [BODP-4686](https://itoworld.atlassian.net/browse/BODP-4686) 'API reference' page: General UI - The listed parameters should be the same as the Swagger API.
- [BODP-4666](https://itoworld.atlassian.net/browse/BODP-4666) 'Fares Data Browser' page: General UI - Search by 'Location' doesn't provide the expected results
- [BODP-4660](https://itoworld.atlassian.net/browse/BODP-4660) 'Fares Data Browser' page: General UI - AXE Analysis raises one moderate issue
- [BODP-4658](https://itoworld.atlassian.net/browse/BODP-4658) 'Fares Data Browser' page: General UI - 'Last updated' row must display date \+ time
- [BODP-4650](https://itoworld.atlassian.net/browse/BODP-4650) Feedback email copy: General UI - The DfT Admin user should receive the same email template that the Consumer user
- [BODP-4649](https://itoworld.atlassian.net/browse/BODP-4649) Feedback email copy: General UI - The dotted line should extend only for one row
- [BODP-4640](https://itoworld.atlassian.net/browse/BODP-4640) Search for AVL feeds: General UI - The text "Search for specific operator or location" is misleading as you cannot search for AVL data feeds by location
- [BODP-4635](https://itoworld.atlassian.net/browse/BODP-4635) Browse AVL Feeds: General UI - Critical accessibility issue flagged for the search button in axe
- [BODP-4634](https://itoworld.atlassian.net/browse/BODP-4634) Browse AVL Feeds: General UI - Status drop down values do not match design
- [BODP-4627](https://itoworld.atlassian.net/browse/BODP-4627) Location data API: AVL API - Sent Request without parameters gets stuck in 'Loading' process
- [BODP-4623](https://itoworld.atlassian.net/browse/BODP-4623) Download all location data: FBODS AVL - The user can still view "All location data" page when not signed in
- [BODP-4622](https://itoworld.atlassian.net/browse/BODP-4622) Download all location data: General UI - Primary navigation does not match design
- [BODP-4620](https://itoworld.atlassian.net/browse/BODP-4620) Location data API: AVL API - 'data feed ID' text input must be a mandatory field
- [BODP-4618](https://itoworld.atlassian.net/browse/BODP-4618) Location data API: AVL API - Parameter 'vehicleRef' is not being displayed
- [BODP-4617](https://itoworld.atlassian.net/browse/BODP-4617) Location data API: General UI - Text is not matching the design
- [BODP-4608](https://itoworld.atlassian.net/browse/BODP-4608) Django Admin AVL Feed: General UI - Long and short descriptions are editable on PBODS
- [BODP-4585](https://itoworld.atlassian.net/browse/BODP-4585) Location Data Individual data set page: General UI - Heading for api url does not match design
- [BODP-4584](https://itoworld.atlassian.net/browse/BODP-4584) Feedback email: General UI - All the BODS Admin users should receive a copy of the email sent to the Consumer
- [BODP-4583](https://itoworld.atlassian.net/browse/BODP-4583) Fares Browser and Detail page: General UI - The wording for the data type within the breadcrumb does not match design
- [BODP-4573](https://itoworld.atlassian.net/browse/BODP-4573) Location Data Individual data set page: General UI - The ID row in the data feed details page has the incorrect label
- [BODP-4572](https://itoworld.atlassian.net/browse/BODP-4572) Location data Individual data set page: General UI - The wording for the data type within the breadcrumb does not match design
- [BODP-4570](https://itoworld.atlassian.net/browse/BODP-4570) API Fares: General UI - Heading \(h3\) is not matching the design
- [BODP-4569](https://itoworld.atlassian.net/browse/BODP-4569) Location data API: General UI - 'View developer documentation' link should redirect to 'Using the APIs' section
- [BODP-4568](https://itoworld.atlassian.net/browse/BODP-4568) Location data API: General UI - Links should open in a new tab
- [BODP-4567](https://itoworld.atlassian.net/browse/BODP-4567) Try API Service page: General UI - Text is not matching the design
- [BODP-4564](https://itoworld.atlassian.net/browse/BODP-4564) API Fares: General UI - Text is not matching the design on '/datasetID' section
- [BODP-4562](https://itoworld.atlassian.net/browse/BODP-4562) Request parameters: Fares_API - 'Error' status is invalid
- [BODP-4561](https://itoworld.atlassian.net/browse/BODP-4561) API Fares: General UI - Text is not matching the design on '/dataset' section
- [BODP-4558](https://itoworld.atlassian.net/browse/BODP-4558) Location data Individual data set page: General UI - Breadcrumb does not match design when in the data feed details page
- [BODP-4551](https://itoworld.atlassian.net/browse/BODP-4551) Create Account page: General UI - Character limiter is not applied in all text inputs.
- [BODP-4549](https://itoworld.atlassian.net/browse/BODP-4549) Create Account page: General UI - Text is not matching the design
- [BODP-4548](https://itoworld.atlassian.net/browse/BODP-4548) Addition of GA tags on events: Admin - Incorrect Event Action assigned on Google Analytics when clicking on the three links in the "Download all data" page
- [BODP-4547](https://itoworld.atlassian.net/browse/BODP-4547) BODS & PBODS Banner: General UI - '@busopendata' link should open in a new tab
- [BODP-4545](https://itoworld.atlassian.net/browse/BODP-4545) Stats.csv Adding 3 columns for number of services: Admin_Metrics: stats.csv is missing "Unique Service Codes" column
- [BODP-4544](https://itoworld.atlassian.net/browse/BODP-4544) API \(timetables\): General UI - The text "\(path\)" should be above "ID of dataset to return" heading as per design
- [BODP-4543](https://itoworld.atlassian.net/browse/BODP-4543) Guide Me page: General UI - Typo error from Zeplin designs
- [BODP-4541](https://itoworld.atlassian.net/browse/BODP-4541) Guide Me page: General UI - 'Case studies' link should redirect to 'Developer documentation> Case studies section'
- [BODP-4540](https://itoworld.atlassian.net/browse/BODP-4540) Guide Me page: General UI - 'Data catalogue field definitions' link should redirect to 'Data catalogue' section
- [BODP-4536](https://itoworld.atlassian.net/browse/BODP-4536) API \(timetables\): General UI - The font size for the h3 headings does not match design
- [BODP-4535](https://itoworld.atlassian.net/browse/BODP-4535) API \(timetables\): General UI - The paragraph "You can use the interactive documentation..." font size does not match design
- [BODP-4533](https://itoworld.atlassian.net/browse/BODP-4533) Location data Individual data set page: General UI - Link text does not match design for subscribing to a data feed
- [BODP-4532](https://itoworld.atlassian.net/browse/BODP-4532) Location data Individual data set page: General UI - 404 when clicking on the back link in the "Get data set updates" page
- [BODP-4531](https://itoworld.atlassian.net/browse/BODP-4531) Subscription page: General UI - 'Back' link produces a 404 error
- [BODP-4526](https://itoworld.atlassian.net/browse/BODP-4526) Timetables Individual data set page: General UI - Mismatch of data type label
- [BODP-4524](https://itoworld.atlassian.net/browse/BODP-4524) Location data Individual data set page: General UI - Mismatch of data type label
- [BODP-4523](https://itoworld.atlassian.net/browse/BODP-4523) FBODS new user guide overview: General UI - Breadcrumb does not match what's in the design

## [1.15.1] - 2022-01-06

### Bug

- [BODP-4771](https://itoworld.atlassian.net/browse/BODP-4771) SIRI VM Validator Email: Dates are incorrect

### Story

- [BODP-4747](https://itoworld.atlassian.net/browse/BODP-4747) NAPTAN link change

### Story Bug

- [BODP-4768](https://itoworld.atlassian.net/browse/BODP-4768) NaPTAN: Django Admin - NaPTAN Stop Points are missing from the Django DB

## [1.15.0] - 2021-11-18

### Bug

- [BODP-4673](https://itoworld.atlassian.net/browse/BODP-4673) Old datasets are able to be published without having passed PTI first
- [BODP-4672](https://itoworld.atlassian.net/browse/BODP-4672) Publisher and Consumer List Views show incorrect value for Last updated
- [BODP-4628](https://itoworld.atlassian.net/browse/BODP-4628) BODS PTI: Revision number issue encountered unexpectedly
- [BODP-4579](https://itoworld.atlassian.net/browse/BODP-4579) Invalid service code passes PTI
- [BODP-4529](https://itoworld.atlassian.net/browse/BODP-4529) \(Regression\) Published Fares Detail page: General UI - The map is not visible and the status is marked as DRAFT
- [BODP-4527](https://itoworld.atlassian.net/browse/BODP-4527) \(Regression\) Expired Fares Data Set: General UI - Cancel the 'Delete data' action redirects to Page not found
- [BODP-4522](https://itoworld.atlassian.net/browse/BODP-4522) \(REGRESSION\) Invite New Organisation: BODS Admin - Submitting form with NOC Code\(s\) filled out does not save in Organisation details page
- [BODP-4520](https://itoworld.atlassian.net/browse/BODP-4520) \(Regression\) 'Data Quality' page: General UI - Wrong percentage is displayed for the daily validation check
- [BODP-4519](https://itoworld.atlassian.net/browse/BODP-4519) \(REGRESSION\) Invite New Organisation: BODS Admin - Submitting empty form does not display validation message for NOC code field
- [BODP-4518](https://itoworld.atlassian.net/browse/BODP-4518) \(REGRESSION\) Invite New Organisation: BODS Admin - Submitting an invalid email also generate validation issue for an empty NOC code field
- [BODP-4517](https://itoworld.atlassian.net/browse/BODP-4517) \(Regression\) AVL Dashboard: General UI - 'Last automated update' column is showing wrong data
- [BODP-4516](https://itoworld.atlassian.net/browse/BODP-4516) \(REGRESSION\) Operator Dataset/Datafeed List: BODS Admin - Sorting by 'Data set name A-Z' & 'Data set name Z-A' Returns 500 Internal Server Error
- [BODP-4515](https://itoworld.atlassian.net/browse/BODP-4515) \(Regression\) Expired Fares Data set: General UI - Data set detail page should display the same message that an Expired TImetable data set.
- [BODP-4513](https://itoworld.atlassian.net/browse/BODP-4513) \(Regression\) Consumer Notifications: General UI - The Consumer/Developer user doesn't receive the notification email for an EXPIRED data set
- [BODP-4502](https://itoworld.atlassian.net/browse/BODP-4502) SiriVM Validator: AVL - VehicleJourneyRef is not recognised by the validator when not included in the packet
- [BODP-4501](https://itoworld.atlassian.net/browse/BODP-4501) \(REGRESSION\) User Management: General UI - Reset password email link immediately invalidates token
- [BODP-4499](https://itoworld.atlassian.net/browse/BODP-4499) \(REGRESSION\) Organisation Profile \(Publisher\): General UI - Incorrect link for "Find your National Operator Code"
- [BODP-4497](https://itoworld.atlassian.net/browse/BODP-4497) E2E Test SIRI VM Emails : SIRI_Validator - "SIRI-VM compliance status changed to..." email still generates when "Daily SIRI-VM compliance check alert" is disabled
- [BODP-4496](https://itoworld.atlassian.net/browse/BODP-4496) E2E Test SIRI VM Confirmation Page: SIRI_Validator - Guidance page link directs the user to "https://publish-bodp.staging.bus-data.dft.gov.uk/coming\_soon/"
- [BODP-4495](https://itoworld.atlassian.net/browse/BODP-4495) \(Regression\) Invalid upload: Fares - Error message is not contained within the message box \(Chrome v94\)
- [BODP-4494](https://itoworld.atlassian.net/browse/BODP-4494) E2E Test SIRI VM Validation Report CSV: SIRI_Validator - Validation Report CSV The "Reference" Column is not populated
- [BODP-4493](https://itoworld.atlassian.net/browse/BODP-4493) E2E Test SIRI VM Validation Report CSV: SIRI_Validator - Validation Report CSV Missing the Column "Category"
- [BODP-4484](https://itoworld.atlassian.net/browse/BODP-4484) Inactive feed: AVL - Data feed is not removed from CAVL once feed becomes Inactive by schema validator
- [BODP-4130](https://itoworld.atlassian.net/browse/BODP-4130) Regression: Missing DQ observations when xml file is added to a zip
- [BODP-4010](https://itoworld.atlassian.net/browse/BODP-4010) Data Quality Service returning inconsistent reports.
- [BODP-2513](https://itoworld.atlassian.net/browse/BODP-2513) Pagination: Hovering over the link to last page of browse/search
- [BODP-1634](https://itoworld.atlassian.net/browse/BODP-1634) Console errors on data set upload on first entry to screen

### Dev Task

- [BODP-4385](https://itoworld.atlassian.net/browse/BODP-4385) When OperatingProfile is missing from VehicleJourney, perform 2 month check using the OperatingProfile in the Service
- [BODP-4330](https://itoworld.atlassian.net/browse/BODP-4330) Dev

### Story

- [BODP-4651](https://itoworld.atlassian.net/browse/BODP-4651) Release Notes for v1.15.0
- [BODP-4624](https://itoworld.atlassian.net/browse/BODP-4624) Automated updates should check the content of error'd drafts before reprocessing
- [BODP-4610](https://itoworld.atlassian.net/browse/BODP-4610) SIRI-VM: Use calendar days to determine post 7 days report
- [BODP-4609](https://itoworld.atlassian.net/browse/BODP-4609) SIRI-VM: Handling empty feeds.
- [BODP-4465](https://itoworld.atlassian.net/browse/BODP-4465) FBOD Data feed detail page: 'BODS Compliant data' row
- [BODP-4444](https://itoworld.atlassian.net/browse/BODP-4444) Update PTI Validation : Lines group
- [BODP-4380](https://itoworld.atlassian.net/browse/BODP-4380) Send SIRI VM Schema failure email
- [BODP-4379](https://itoworld.atlassian.net/browse/BODP-4379) Display SIRI-VM schema failure check on the UI
- [BODP-4370](https://itoworld.atlassian.net/browse/BODP-4370) Update BODS PTI : StopPoints
- [BODP-4314](https://itoworld.atlassian.net/browse/BODP-4314) SIRI-VM validator: Send email when critical score less than lower threshold%
- [BODP-4313](https://itoworld.atlassian.net/browse/BODP-4313) SIRI-VM schema failure check \(backend\)
- [BODP-4311](https://itoworld.atlassian.net/browse/BODP-4311) SIRIVM: Critical score less than 20% validation
- [BODP-4268](https://itoworld.atlassian.net/browse/BODP-4268) SIRIVM: Daily Validation after day 7
- [BODP-4265](https://itoworld.atlassian.net/browse/BODP-4265) SIRI VM Validator: Sendcompliance status email for SIRI Validator when the status changes
- [BODP-4231](https://itoworld.atlassian.net/browse/BODP-4231) SIRI VM Validator: Send email for validation errors in the first 7 days
- [BODP-4225](https://itoworld.atlassian.net/browse/BODP-4225) SIRI VM Validator: Validating a feed
- [BODP-4222](https://itoworld.atlassian.net/browse/BODP-4222) SIRI-VM validator: Send email when feed is marked as non-compliant or partially compliant
- [BODP-4221](https://itoworld.atlassian.net/browse/BODP-4221) SIRI-VM: Update 'copy' of confirmation page
- [BODP-4220](https://itoworld.atlassian.net/browse/BODP-4220) SIRI-VM: daily compliance status change opt-out UI and functionality
- [BODP-4218](https://itoworld.atlassian.net/browse/BODP-4218) SIRI-VM Guidance pages
- [BODP-4217](https://itoworld.atlassian.net/browse/BODP-4217) SIRI-VM Download validation report CSV
- [BODP-4216](https://itoworld.atlassian.net/browse/BODP-4216) SIRI-VM: individual data feed page UI
- [BODP-4215](https://itoworld.atlassian.net/browse/BODP-4215) SIRI-VM: Location Data dashboard UI

### Story Bug

- [BODP-4684](https://itoworld.atlassian.net/browse/BODP-4684) Dayly validation: SIRI_Validator - The periodic task 'run_avl_validations_in_rt' is validating INACTIVE feeds
- [BODP-4680](https://itoworld.atlassian.net/browse/BODP-4680) Changelog page: General UI - 'Release notes' order should be from most recent to oldest
- [BODP-4679](https://itoworld.atlassian.net/browse/BODP-4679) Email updates: SIRI_Validator - Update content of email
- [BODP-4678](https://itoworld.atlassian.net/browse/BODP-4678) Daily validation reports: SIRI_Validator - When a feed has no packets, the daily validation report is not created
- [BODP-4463](https://itoworld.atlassian.net/browse/BODP-4463) Account settings: SIRI_Validator - 'Daily SIRI-VM compliance check alert' must be enabled by default
- [BODP-4462](https://itoworld.atlassian.net/browse/BODP-4462) Status changed email: SIRI_Validator - 'Short description' row is not showing the saved description for the data feed
- [BODP-4458](https://itoworld.atlassian.net/browse/BODP-4458) Data feed detail page: SIRI_Validator - 'BODS Compliant data' row is not showing the date and count days.
- [BODP-4455](https://itoworld.atlassian.net/browse/BODP-4455) Email for validation error: SIRI_Validator - Date is showing an additional wrong day number.

### Sub-task

- [BODP-4353](https://itoworld.atlassian.net/browse/BODP-4353) Dev
- [BODP-4342](https://itoworld.atlassian.net/browse/BODP-4342) Dev - BODP-4220 - SIRI-VM: daily compliance status change opt-out

### Test Task

- [BODP-4381](https://itoworld.atlassian.net/browse/BODP-4381) Test - BODP-4379 - Display SIRI-VM schema failure check on the UI
- [BODP-4371](https://itoworld.atlassian.net/browse/BODP-4371) Test - BODP-4370 - Update BODS PTI : StopPoints
- [BODP-4324](https://itoworld.atlassian.net/browse/BODP-4324) Test - BODP-4218 - SIRI-VM Guidance pages
- [BODP-4269](https://itoworld.atlassian.net/browse/BODP-4269) Test - BODP-4268 - SIRIVM: Daily Validation

## [1.14.0] - 2021-09-30

### Bug

- [BODP-4396](https://itoworld.atlassian.net/browse/BODP-4396) Browser compatibility: General UI - Timetables changelog table does not format correctly when there is a long comment
- [BODP-4395](https://itoworld.atlassian.net/browse/BODP-4395) \(REGRESSION\) Invalid Upload: Fares - Error message overlaps the message container \(Chrome v92\)
- [BODP-4393](https://itoworld.atlassian.net/browse/BODP-4393) TXC Validation Check: Timetables_PTI - Validation check failed message is not matching design \(Regression\)
- [BODP-4387](https://itoworld.atlassian.net/browse/BODP-4387) Data Quality Report: Timetables_DQ - The DQ report does not generate for a particular dataset
- [BODP-4369](https://itoworld.atlassian.net/browse/BODP-4369) \(REGRESSION\) Timetable Upload: Timetables_PTI - "All data that has outstanding issues..." still shows in the "Action required – PTI validation report requires resolution \(if applicable\)" when hardblock is enforced.
- [BODP-4362](https://itoworld.atlassian.net/browse/BODP-4362) PROD Publisher: PTI Validation- Accept <RunTime>PT0H0M0S</RunTime> for zero runtime
- [BODP-4361](https://itoworld.atlassian.net/browse/BODP-4361) PTI Valid file results in DQ Service unavailable
- [BODP-4360](https://itoworld.atlassian.net/browse/BODP-4360) \(REGRESSION\) User Management: General UI - Org Admin user invites a new user \(email\) that has a pending invite \(from another organisation\) gives back an error
- [BODP-4356](https://itoworld.atlassian.net/browse/BODP-4356) End Date PTI validation error encountered when start and end date are the same
- [BODP-4355](https://itoworld.atlassian.net/browse/BODP-4355) \(REGRESSSION\) Timetable Upload: Timetables - 500 Internal Server Error When Trying to Download dataqualityreport.csv
- [BODP-4354](https://itoworld.atlassian.net/browse/BODP-4354) \(REGRESSION\) Swagger API: Fares_API - Link 'Download data catalogue' should not be visible
- [BODP-4350](https://itoworld.atlassian.net/browse/BODP-4350) \(REGRESSION\) Password emails: General UI - Missing 'Hello,' word in the content of the email
- [BODP-4349](https://itoworld.atlassian.net/browse/BODP-4349) \(REGRESSSION\) Timetable Publish: Timetables_PTI - Email content does not match template when publishing timetable with PTI errors for Org Staff & Org Admin
- [BODP-4348](https://itoworld.atlassian.net/browse/BODP-4348) \(REGRESSION\) Timetable Upload: Timetables - Uploading timetable dataset over 10mb freezes progress bar at 45%
- [BODP-4337](https://itoworld.atlassian.net/browse/BODP-4337) Timetables and Fares: Map is not displaying properly with any timetable and fares dataset within Mapbox
- [BODP-4334](https://itoworld.atlassian.net/browse/BODP-4334) PROD Admin: Stats are not being updated since August 19th
- [BODP-4292](https://itoworld.atlassian.net/browse/BODP-4292) Invalid Error Link in the crispy form
- [BODP-4289](https://itoworld.atlassian.net/browse/BODP-4289) Timetables with empty <Licence /> tags cause pipeline to fail
- [BODP-4260](https://itoworld.atlassian.net/browse/BODP-4260) Timetables PTI: File name incorrect when a single xml dataset is uplaoded via URL
- [BODP-4223](https://itoworld.atlassian.net/browse/BODP-4223) Internal & Staging Timetables: Reverted back to "Data set reports are now available" emails \(Old Template\)
- [BODP-4188](https://itoworld.atlassian.net/browse/BODP-4188) Inconsistent spelling of "Data feed\(s\)" between Column H and K in the stats.csv file
- [BODP-4141](https://itoworld.atlassian.net/browse/BODP-4141) BODS Admin: 'Draft' option is not available in the Status dropdown for AVL
- [BODP-4120](https://itoworld.atlassian.net/browse/BODP-4120) Documentation - Local authority requirements: Type error
- [BODP-4022](https://itoworld.atlassian.net/browse/BODP-4022) Timetables: Dashboard rows overlap 'Processing' text with long data set name
- [BODP-3781](https://itoworld.atlassian.net/browse/BODP-3781) Adding random parameter to AVL provides all results and 200 status
- [BODP-2512](https://itoworld.atlassian.net/browse/BODP-2512) Pagination on last page of browse/search: the hyperlink to the first page is missing
- [BODP-1437](https://itoworld.atlassian.net/browse/BODP-1437) active_url template tag does not work as expected and therefore rarely adds appropriate CSS classes to active links

### Dev Task

- [BODP-4327](https://itoworld.atlassian.net/browse/BODP-4327) model and migration for known issues
- [BODP-4326](https://itoworld.atlassian.net/browse/BODP-4326) new app
- [BODP-4288](https://itoworld.atlassian.net/browse/BODP-4288) Dev

### Story

- [BODP-4357](https://itoworld.atlassian.net/browse/BODP-4357) Update to include PTIC link
- [BODP-4307](https://itoworld.atlassian.net/browse/BODP-4307) SIRI VM Validator: Control SIRI VM validator functionality though a feature flag
- [BODP-4306](https://itoworld.atlassian.net/browse/BODP-4306) Changelog BODS
- [BODP-4293](https://itoworld.atlassian.net/browse/BODP-4293) BODS PTI Updates: DaysofOperation - Include OtherPublicHolidays to list of acceptable elements
- [BODP-4272](https://itoworld.atlassian.net/browse/BODP-4272) PTI hardblock: Reject Non-compliant files in automatic update
- [BODP-4259](https://itoworld.atlassian.net/browse/BODP-4259) Datset subscriptions: 'Data feed status changed' email is not sent for Fares or Timetable datasets
- [BODP-4229](https://itoworld.atlassian.net/browse/BODP-4229) Update AVL email for no feed activity
- [BODP-4219](https://itoworld.atlassian.net/browse/BODP-4219) SIRIVM: change data unavailable to no vehicle activity
- [BODP-4112](https://itoworld.atlassian.net/browse/BODP-4112) PTI hardblock: Failed validation
- [BODP-3481](https://itoworld.atlassian.net/browse/BODP-3481) Developer Account Management Email
- [BODP-3474](https://itoworld.atlassian.net/browse/BODP-3474) Dataset feedback email
- [BODP-3422](https://itoworld.atlassian.net/browse/BODP-3422) Password Emails

### Story Bug

- [BODP-4339](https://itoworld.atlassian.net/browse/BODP-4339) Changelog Page: General UI - User is redirected to BODS Home page when clicking 'Back' link
- [BODP-4331](https://itoworld.atlassian.net/browse/BODP-4331) Having <OtherPublicHoliday> tags within the <DaysOfOperation> AND <DaysOfNonOperation> tags produces PTI Error
- [BODP-4287](https://itoworld.atlassian.net/browse/BODP-4287) PBODS & FBODS: Notification title still says "Published feed data unavailable alert"
- [BODP-4286](https://itoworld.atlassian.net/browse/BODP-4286) The text "Data containing this observation will be rejected by BODS after \[DDMMYYYY\]" is showing despite the dataset not passing the publish stage.
- [BODP-4285](https://itoworld.atlassian.net/browse/BODP-4285) No "Your data feed has been successfully updated" text in the green box when updating an already published AVL feed
- [BODP-4281](https://itoworld.atlassian.net/browse/BODP-4281) "No Vehicle Activity" status not being reflected in the UI after "AVL Feed \[ID\] is no longer sending data to the Bus Open Data Service email notification"
- [BODP-4264](https://itoworld.atlassian.net/browse/BODP-4264) No "You have changed your password on the Bus Open Data Service" email notification
- [BODP-4263](https://itoworld.atlassian.net/browse/BODP-4263) No "You have feedback on your data" email notification after submitting feedback

### Sub-task

- [BODP-4329](https://itoworld.atlassian.net/browse/BODP-4329) Dev - BODS PTI Updates: DaysofOperation

### Test Task

- [BODP-4325](https://itoworld.atlassian.net/browse/BODP-4325) Test - BODP-4306 - Changelog BODS
- [BODP-4230](https://itoworld.atlassian.net/browse/BODP-4230) Test - BODP-4229 - Update AVL email for no feed activity
- [BODP-3482](https://itoworld.atlassian.net/browse/BODP-3482) Test - BODP-3481 - Developer Account Management Email

## [1.13.1] - 2021-08-27 (Non-prod)

- NO-TICKET: Added `CELERY_BROKER_VISBILITY_TIMEOUT` as environment variable
- NO-TICKET: Various pipeline optimisations for database transactions

## [1.13.0] - 2021-08-12

- [BODP-4176](https://itoworld.atlassian.net/browse/BODP-4176) Timetables: TxC file from Production can be published without DQ report
- [BODP-4108](https://itoworld.atlassian.net/browse/BODP-4108) BODS Admin: Consumer Notes field is not responsive to max text
- [BODP-3834](https://itoworld.atlassian.net/browse/BODP-3834) Compliance and Monitoring - Ph1
- [BODP-4172](https://itoworld.atlassian.net/browse/BODP-4172) Update screens for API download
- [BODP-4168](https://itoworld.atlassian.net/browse/BODP-4168) C&M: Stats
- [BODP-4150](https://itoworld.atlassian.net/browse/BODP-4150) Emails: Make the body of emails a template variable so we can make faster changes
- [BODP-4144](https://itoworld.atlassian.net/browse/BODP-4144) BODS PTI Update: Revision incremements between versions
- [BODP-4139](https://itoworld.atlassian.net/browse/BODP-4139) C&M: timetables_data_catalogue
- [BODP-4127](https://itoworld.atlassian.net/browse/BODP-4127) Add License Number- Organisational profile update: Publisher Admin
- [BODP-4125](https://itoworld.atlassian.net/browse/BODP-4125) Add License Number- Organisation profile update: Publisher Agent
- [BODP-4121](https://itoworld.atlassian.net/browse/BODP-4121) Add License number in Organisation profile: DfT admin portal
- [BODP-4113](https://itoworld.atlassian.net/browse/BODP-4113) C&M: Addition of new fields to the Organisations csv
- [BODP-4053](https://itoworld.atlassian.net/browse/BODP-4053) Research Fares \(Netex\) to explore feasibility of extracting metrics for C&M
- [BODP-4051](https://itoworld.atlassian.net/browse/BODP-4051) C&M: Create Monthly API metrics
- [BODP-4048](https://itoworld.atlassian.net/browse/BODP-4048) Cookie Page Content Update
- [BODP-4017](https://itoworld.atlassian.net/browse/BODP-4017) C&M: Download details of dataset publishers through datasetpublishing csv
- [BODP-3942](https://itoworld.atlassian.net/browse/BODP-3942) C&M: Publishers
- [BODP-3940](https://itoworld.atlassian.net/browse/BODP-3940) C&M: Update Raw API metrics CSV
- [BODP-3939](https://itoworld.atlassian.net/browse/BODP-3939) DfT Admin: new download screens
- [BODP-3767](https://itoworld.atlassian.net/browse/BODP-3767) Addition of new fields to the Data Catalogue
- [BODP-3471](https://itoworld.atlassian.net/browse/BODP-3471) BODS Cookies updated
- [BODP-4224](https://itoworld.atlassian.net/browse/BODP-4224) The numberOfServicesWithValidOperatingDates & additionalServicesWithFutureStartDate figures doubling in organisation.csv for latest timetable dataset
- [BODP-4213](https://itoworld.atlassian.net/browse/BODP-4213) 'Cookie settings' banner is still visible after Save changes in 'Cookie settings' page
- [BODP-4211](https://itoworld.atlassian.net/browse/BODP-4211) Incorrect column name for "unregisteredServices" in organisations.csv
- [BODP-4210](https://itoworld.atlassian.net/browse/BODP-4210) Download lag with the "Download all publisher monitoring metrics" link
- [BODP-4208](https://itoworld.atlassian.net/browse/BODP-4208) "Download all publisher monitoring metrics" link produces 502 after download lag
- [BODP-4207](https://itoworld.atlassian.net/browse/BODP-4207) 'Edit organisation profile' page - Right section 'Need help populating this page?' not visible and incorrect element.
- [BODP-4206](https://itoworld.atlassian.net/browse/BODP-4206) BODS Admin: "Need help populating this page" right hand section is missing in Organisation detail page
- [BODP-4204](https://itoworld.atlassian.net/browse/BODP-4204) 'Organisation details' and 'Edit organisation' pages - Links must open in a new tab
- [BODP-4203](https://itoworld.atlassian.net/browse/BODP-4203) BODS Admin: Append the word "number" to first error message for invalid PSV Licence Number
- [BODP-4200](https://itoworld.atlassian.net/browse/BODP-4200) BODS Admin: Current Valid PSV Licence Numbers greys out "I do not have a PSV Licence number" with the box ticked
- [BODP-4199](https://itoworld.atlassian.net/browse/BODP-4199) BODS Admin: Cancel button in Edit organisation detail page returns "Page not found"
- [BODP-4198](https://itoworld.atlassian.net/browse/BODP-4198) BODS Admin: "I do not have a PSV Licence number" checkbox unticks itself
- [BODP-4196](https://itoworld.atlassian.net/browse/BODP-4196) BODS Admin: PSV Licence Number row not displayed by default in Organisation detail section
- [BODP-4195](https://itoworld.atlassian.net/browse/BODP-4195) BODS Admin: No "Need help populating this page? right hand section via Edit mode
- [BODP-4194](https://itoworld.atlassian.net/browse/BODP-4194) BODS Admin: PSV Licence Number Field Not Visible & Related Buttons not clickable by default
- [BODP-4186](https://itoworld.atlassian.net/browse/BODP-4186) Downloaded PTI observations file > Incorrect 'Filename' and 'XML Line Number' for 'RevisionNumber' warning
- [BODP-4180](https://itoworld.atlassian.net/browse/BODP-4180) lastUpdatedDate in timetabledatacatalogue.csv not picking up revision.published_at \(Date from the UI\)
- [BODP-4171](https://itoworld.atlassian.net/browse/BODP-4171) Downloaded csv file don't show the 'System' account type when an automated update happened
- [BODP-4189](https://itoworld.atlassian.net/browse/BODP-4189) Test - BODP-3471 - BODS Cookies updated
- [BODP-4183](https://itoworld.atlassian.net/browse/BODP-4183) Test - BODP-4113 - C&M: Addition of new fields to the Organisations csv
- [BODP-4145](https://itoworld.atlassian.net/browse/BODP-4145) Test - BODP-4144 - BODS PTI Update: Revision incremements between versions
- [BODP-4131](https://itoworld.atlassian.net/browse/BODP-4131) Test - BODP-4017 - C&M: Download details of dataset publishers through datasetpublishing csv
- [BODP-4082](https://itoworld.atlassian.net/browse/BODP-4082) Test - BODP-3939 - DfT Admin: new download screens
- [BODP-4052](https://itoworld.atlassian.net/browse/BODP-4052) Test - BODP-4051 - C&M: Create Monthly API metrics

## [1.12.1] - 2021-07-15

- [BODP-4166](https://itoworld.atlassian.net/browse/BODP-4166) Dataset with critical observations has 100% DQ score
- [BODP-4163](https://itoworld.atlassian.net/browse/BODP-4163) Multiple "Data set reports are now available" emails are being sent a minute apart
- [BODP-4164](https://itoworld.atlassian.net/browse/BODP-4164) Update email content for PTI date in Gov.notify
- [BODP-4073](https://itoworld.atlassian.net/browse/BODP-4073) Make the date in PTI report and UI driven by an environment variable
- [BODP-4162](https://itoworld.atlassian.net/browse/BODP-4162) Success update of dataset page - Missing PTI Date for Not Compliant Data
- [BODP-4155](https://itoworld.atlassian.net/browse/BODP-4155) Success publish of timetable dataset page - Missing paragraph
- [BODP-4074](https://itoworld.atlassian.net/browse/BODP-4074) Test - BODP-4073 - Make the date in PTI report and UI driven by an environment variable

## [1.11.2] - 2021-06-22

- Added Django admin screen for setting revisions into an error state
- Added periodic task to log stuck revisions to the log file

## [1.11.1] - 2021-06-16

- Added smaller batching to PTIObservation creation

## [1.11.0] - 2021-05-27

- [BODP-3857](https://itoworld.atlassian.net/browse/BODP-3857) Fares error emails are incorrect
- [BODP-3832](https://itoworld.atlassian.net/browse/BODP-3832) Regression: BODS admin view shows duplicate datasets for timetables
- [BODP-3831](https://itoworld.atlassian.net/browse/BODP-3831) Regression: Consumer is not receiving update emails for subscribed dataset
- [BODP-3829](https://itoworld.atlassian.net/browse/BODP-3829) Regression: 404 error when navigating from user detail page to org profile
- [BODP-3824](https://itoworld.atlassian.net/browse/BODP-3824) Dataset revision naming race condition causes monitoring pipeline to fail
- [BODP-3820](https://itoworld.atlassian.net/browse/BODP-3820) Regression: GTFS RT parameter 'startTimeAfter' returns no data
- [BODP-3779](https://itoworld.atlassian.net/browse/BODP-3779) Regression: Fares and AVL draft wrong time zone in draft name
- [BODP-3778](https://itoworld.atlassian.net/browse/BODP-3778) Emails are not triggering
- [BODP-3741](https://itoworld.atlassian.net/browse/BODP-3741) Regression: Internal Staging Your data sets page continuously refreshes and processes
- [BODP-3654](https://itoworld.atlassian.net/browse/BODP-3654) Some DQ scores in Changelog continue to show 'Generating'
- [BODP-3492](https://itoworld.atlassian.net/browse/BODP-3492) Organizations Fares Datasets count are showing as AVL on the Summary Page
- [BODP-3214](https://itoworld.atlassian.net/browse/BODP-3214) Error message for Timetable reads 'Data feed' instead of 'Data set'
- [BODP-1350](https://itoworld.atlassian.net/browse/BODP-1350) Account Management, Org Admin - 'Edit user' page has big space under page title
- [BODP-3929](https://itoworld.atlassian.net/browse/BODP-3929) Disable API metrics download link in BODS admin portal
- [BODP-3926](https://itoworld.atlassian.net/browse/BODP-3926) Add Django admin view for DQ stop points
- [BODP-3920](https://itoworld.atlassian.net/browse/BODP-3920) 1.11.0 Scan: Address warnings from Semgrep report
- [BODP-3910](https://itoworld.atlassian.net/browse/BODP-3910) UAT: BODS PTI: Change hardblock date in from october to August
- [BODP-3907](https://itoworld.atlassian.net/browse/BODP-3907) UAT: BODS PTI: Update validation and details for OperatingPeriod
- [BODP-3897](https://itoworld.atlassian.net/browse/BODP-3897) UAT: Remove validation on JourneyPattern Direction
- [BODP-3893](https://itoworld.atlassian.net/browse/BODP-3893) UAT: Update DaysofOperation
- [BODP-3869](https://itoworld.atlassian.net/browse/BODP-3869) UAT: Update detail for Layover point
- [BODP-3867](https://itoworld.atlassian.net/browse/BODP-3867) UAT: Update detail for Service Code validation
- [BODP-3846](https://itoworld.atlassian.net/browse/BODP-3846) BODS PTI: Update report for mandatory element validation
- [BODP-3776](https://itoworld.atlassian.net/browse/BODP-3776) BODS PTI : CreationDateTime should be same between revisions
- [BODP-3774](https://itoworld.atlassian.net/browse/BODP-3774) BODS PTI : RevisionNumber increments between revisions
- [BODP-3747](https://itoworld.atlassian.net/browse/BODP-3747) BODS PTI : VehicleJourney shall define the operation of a particular trip\(VehicleJourneyTimingLink \)
- [BODP-3722](https://itoworld.atlassian.net/browse/BODP-3722) BODS PTI: Update to Service code format
- [BODP-3713](https://itoworld.atlassian.net/browse/BODP-3713) Email notifications for Agents - Timetable publishing
- [BODP-3701](https://itoworld.atlassian.net/browse/BODP-3701) Email notifications for automatic uploads
- [BODP-3644](https://itoworld.atlassian.net/browse/BODP-3644) BODS PTI : Mandatory Elements
- [BODP-3642](https://itoworld.atlassian.net/browse/BODP-3642) BODS PTI : VehicleJourney shall define the operation of a particular trip
- [BODP-3640](https://itoworld.atlassian.net/browse/BODP-3640) BODS PTI : JourneyPatternTimingLink From/To
- [BODP-3638](https://itoworld.atlassian.net/browse/BODP-3638) BODS PTI : DaysofOperation
- [BODP-3636](https://itoworld.atlassian.net/browse/BODP-3636) BODS PTI : JourneyPatternTimingLink
- [BODP-3634](https://itoworld.atlassian.net/browse/BODP-3634) BODS PTI : JourneyPatternSection
- [BODP-3632](https://itoworld.atlassian.net/browse/BODP-3632) BODS PTI : RouteSection/Direction
- [BODP-3630](https://itoworld.atlassian.net/browse/BODP-3630) BODS PTI : Route/ReversingManoeuvres
- [BODP-3628](https://itoworld.atlassian.net/browse/BODP-3628) BODS PTI : Serviced organisations - StartDate
- [BODP-3626](https://itoworld.atlassian.net/browse/BODP-3626) BODS PTI : PeriodicDayType
- [BODP-3623](https://itoworld.atlassian.net/browse/BODP-3623) BODS PTI : Validate JourneyPattern Direction
- [BODP-3621](https://itoworld.atlassian.net/browse/BODP-3621) BODS PTI : DaysofWeek
- [BODP-3619](https://itoworld.atlassian.net/browse/BODP-3619) BODS PTI : Track
- [BODP-3617](https://itoworld.atlassian.net/browse/BODP-3617) BODS PTI : Routes
- [BODP-3615](https://itoworld.atlassian.net/browse/BODP-3615) BODS PTI : StopPoints
- [BODP-3613](https://itoworld.atlassian.net/browse/BODP-3613) BODS PTI : LineID
- [BODP-3611](https://itoworld.atlassian.net/browse/BODP-3611) BODS PTI : Lines group
- [BODP-3609](https://itoworld.atlassian.net/browse/BODP-3609) BODS PTI : Only one operator code per file
- [BODP-3604](https://itoworld.atlassian.net/browse/BODP-3604) BODS PTI : Versioning RevisionNumber
- [BODP-3602](https://itoworld.atlassian.net/browse/BODP-3602) BODS PTI : Versioning Modification
- [BODP-3600](https://itoworld.atlassian.net/browse/BODP-3600) BODS PTI : Versioning ModificationDateTime
- [BODP-3598](https://itoworld.atlassian.net/browse/BODP-3598) BODS PTI : DepartureDayShift
- [BODP-3596](https://itoworld.atlassian.net/browse/BODP-3596) BODS PTI : VehicleJourney/DestinationDisplay
- [BODP-3594](https://itoworld.atlassian.net/browse/BODP-3594) BODS PTI : JourneyPatternStopUsageStructure/DynamicDestinationDisplay
- [BODP-3592](https://itoworld.atlassian.net/browse/BODP-3592) UI: Display DQ score
- [BODP-3590](https://itoworld.atlassian.net/browse/BODP-3590) BODS PTI: VehicleJourneyInterchange
- [BODP-3586](https://itoworld.atlassian.net/browse/BODP-3586) BODS PTI: InboundDescription
- [BODP-3584](https://itoworld.atlassian.net/browse/BODP-3584) BODS PTI: OutboundDescription
- [BODP-3580](https://itoworld.atlassian.net/browse/BODP-3580) BODS PTI: Non Flexible Service
- [BODP-3578](https://itoworld.atlassian.net/browse/BODP-3578) BODS PTI: StandardService
- [BODP-3576](https://itoworld.atlassian.net/browse/BODP-3576) BODS PTI: OperatingPeriod
- [BODP-3574](https://itoworld.atlassian.net/browse/BODP-3574) BODS PTI: LayoverPoint
- [BODP-3572](https://itoworld.atlassian.net/browse/BODP-3572) BODS PTI: Service Code
- [BODP-3567](https://itoworld.atlassian.net/browse/BODP-3567) BODS PTI : Versioning CreationDateTime
- [BODP-3548](https://itoworld.atlassian.net/browse/BODP-3548) BODS PTI : Notes Shall not include date
- [BODP-3546](https://itoworld.atlassian.net/browse/BODP-3546) BODS PTI : Serviced organisations - Holidays
- [BODP-3544](https://itoworld.atlassian.net/browse/BODP-3544) 2.4 Schema validation error messaging
- [BODP-3542](https://itoworld.atlassian.net/browse/BODP-3542) BODS PTI : Schema not transxchange 2.4
- [BODP-3540](https://itoworld.atlassian.net/browse/BODP-3540) Download PTI Validation Report
- [BODP-3538](https://itoworld.atlassian.net/browse/BODP-3538) BODS PTI : Vehicle journeys - JourneyPatternStopUsageStructure
- [BODP-3536](https://itoworld.atlassian.net/browse/BODP-3536) BODS PTI : Special Operating Days
- [BODP-3534](https://itoworld.atlassian.net/browse/BODP-3534) BODS PTI : InterchangeActivity
- [BODP-3532](https://itoworld.atlassian.net/browse/BODP-3532) BODS PTI : Services Group
- [BODP-3530](https://itoworld.atlassian.net/browse/BODP-3530) BODS PTI : GarageCode in Garage is mandatory
- [BODP-3528](https://itoworld.atlassian.net/browse/BODP-3528) BODS PTI : Registrations group
- [BODP-3526](https://itoworld.atlassian.net/browse/BODP-3526) BODS PTI : Operators group contains no LicensedOperator
- [BODP-3524](https://itoworld.atlassian.net/browse/BODP-3524) BODS PTI : Operators group contains 1 Operator only
- [BODP-3522](https://itoworld.atlassian.net/browse/BODP-3522) BODS PTI : Serviced organisations - Meaningful name
- [BODP-3520](https://itoworld.atlassian.net/browse/BODP-3520) BODS PTI : Serviced organisations - Provisional dates
- [BODP-3518](https://itoworld.atlassian.net/browse/BODP-3518) BODS PTI : Notes should not be flagged as private
- [BODP-3516](https://itoworld.atlassian.net/browse/BODP-3516) BODS PTI : Notes Shall not include special characters
- [BODP-3514](https://itoworld.atlassian.net/browse/BODP-3514) BODS PTI : Validate Accessibility Information - AccessibilityInfo
- [BODP-3512](https://itoworld.atlassian.net/browse/BODP-3512) BODS PTI : Validate Accessibility Information - PassengerInfo
- [BODP-3509](https://itoworld.atlassian.net/browse/BODP-3509) UI: Display message when dataset is valid 2.4 schema and passes PTI validation
- [BODP-3507](https://itoworld.atlassian.net/browse/BODP-3507) UI: Display message when files fails PTI Validation
- [BODP-3505](https://itoworld.atlassian.net/browse/BODP-3505) Add link to the guidance page
- [BODP-3503](https://itoworld.atlassian.net/browse/BODP-3503) UI:Reject datasets not compliant with 2.4 schema during publishing
- [BODP-3502](https://itoworld.atlassian.net/browse/BODP-3502) Data set detail page
- [BODP-3501](https://itoworld.atlassian.net/browse/BODP-3501) Email notifications for manual uploads
- [BODP-3500](https://itoworld.atlassian.net/browse/BODP-3500) Guidance page: Publisher
- [BODP-3440](https://itoworld.atlassian.net/browse/BODP-3440) Email Updates - AVL Datafeeds
- [BODP-3436](https://itoworld.atlassian.net/browse/BODP-3436) Email Updates - Fares Dataset
- [BODP-3433](https://itoworld.atlassian.net/browse/BODP-3433) Email Updates - Timetable Dataset
- [BODP-3342](https://itoworld.atlassian.net/browse/BODP-3342) BODS PTI- CommonInterchangeGroup \(JourneyPatternInterchange\)

## [1.10.1] - 2021-04-14

- [BODP-3742](https://itoworld.atlassian.net/browse/BODP-3742) Automated URL update when a Draft revision exists for the dataset

## [1.10.1] - 2021-03-15

### Bug

- [BODP-3571](https://itoworld.atlassian.net/browse/BODP-3571) Accessing DQS report throws internal server error for large dataset updated via automated update
- [BODP-3570](https://itoworld.atlassian.net/browse/BODP-3570) Fares: Changelog shows DQ score column
- [BODP-3569](https://itoworld.atlassian.net/browse/BODP-3569) AVL changelog: Clicking on changelog gives 500 error

## [1.10.0] - 2021-03-10

### Bug

- [BODP-3563](https://itoworld.atlassian.net/browse/BODP-3563) Error displays on dataset details page during monitoring update
- [BODP-3446](https://itoworld.atlassian.net/browse/BODP-3446) Fares dataset details: Incorrect endpoint displayed
- [BODP-3445](https://itoworld.atlassian.net/browse/BODP-3445) Fares API: Dataset URL not available in the response
- [BODP-3103](https://itoworld.atlassian.net/browse/BODP-3103) Fares: Inactive dataset map is blank
- [BODP-3097](https://itoworld.atlassian.net/browse/BODP-3097) AVL: Changelog shows 'Error' status instead of 'Data unavailable'

### Story

- [BODP-3467](https://itoworld.atlassian.net/browse/BODP-3467) Update accessibility statement
- [BODP-3466](https://itoworld.atlassian.net/browse/BODP-3466) Changing links: content update
- [BODP-3455](https://itoworld.atlassian.net/browse/BODP-3455) Remove access to deprecated pages for Timetable datasets
- [BODP-3431](https://itoworld.atlassian.net/browse/BODP-3431) Observation detail page: critical observations
- [BODP-3420](https://itoworld.atlassian.net/browse/BODP-3420) Timetables Changelog: DQ per dataset
- [BODP-3405](https://itoworld.atlassian.net/browse/BODP-3405) Content Update: Remove 'Suppression' references in advisory observation details
- [BODP-3392](https://itoworld.atlassian.net/browse/BODP-3392) Add DQ observation 'No timing point for more than 15 minutes' to the DQ report
- [BODP-3363](https://itoworld.atlassian.net/browse/BODP-3363) DQ score description page
- [BODP-3356](https://itoworld.atlassian.net/browse/BODP-3356) DQ Scoring: Determine DQ level \(RAG\) of dataset
- [BODP-3354](https://itoworld.atlassian.net/browse/BODP-3354) DQ Scoring: Calculate DQ Score
- [BODP-3345](https://itoworld.atlassian.net/browse/BODP-3345) Tech Improvement: Upgrade existing Python Packages
- [BODP-3338](https://itoworld.atlassian.net/browse/BODP-3338) Observation detail page: advisory observations
- [BODP-3330](https://itoworld.atlassian.net/browse/BODP-3330) Content Update Create Account
- [BODP-3328](https://itoworld.atlassian.net/browse/BODP-3328) Download BODS API data
- [BODP-3325](https://itoworld.atlassian.net/browse/BODP-3325) Add agent org name in Automated exports in Agents.CSV
- [BODP-3315](https://itoworld.atlassian.net/browse/BODP-3315) Timetables DQ report: Export
- [BODP-3313](https://itoworld.atlassian.net/browse/BODP-3313) View DQ report observation definitions
- [BODP-3311](https://itoworld.atlassian.net/browse/BODP-3311) View DQ Score and RAG in Data Quality Report
- [BODP-3309](https://itoworld.atlassian.net/browse/BODP-3309) View Count of Lines in DQ Report
- [BODP-3305](https://itoworld.atlassian.net/browse/BODP-3305) Add advisory observation: Expired Lines to the DQ report
- [BODP-3303](https://itoworld.atlassian.net/browse/BODP-3303) Add line-missing-block-id warning to BODS
- [BODP-3301](https://itoworld.atlassian.net/browse/BODP-3301) Add critical observation: Missing NoC Code to the DQ report
- [BODP-3284](https://itoworld.atlassian.net/browse/BODP-3284) View Count of Critical/Advisory observations
- [BODP-3282](https://itoworld.atlassian.net/browse/BODP-3282) View DQ observations by category - Critical Observations
- [BODP-3281](https://itoworld.atlassian.net/browse/BODP-3281) Timetables DQ report: Advisory
- [BODP-3280](https://itoworld.atlassian.net/browse/BODP-3280) View DQ score and RAG in dataset details
- [BODP-3279](https://itoworld.atlassian.net/browse/BODP-3279) Add file type flag \(xml/zip\) to API response
- [BODP-3237](https://itoworld.atlassian.net/browse/BODP-3237) Stagecoach feedback - Include date of journey in DQ reports for journey overlaps
- [BODP-3230](https://itoworld.atlassian.net/browse/BODP-3230) Track bulk AVL GTFS downloads in Google Analytics
  [BODP-3215](https://itoworld.atlassian.net/browse/BODP-3215) 'Download all AVL data' in GTFS RT format
- [BODP-3185](https://itoworld.atlassian.net/browse/BODP-3185) Update AVL interactive API Paramter- Operatorref
- [BODP-2576](https://itoworld.atlassian.net/browse/BODP-2576) Enable DQ results to be viewed for a dataset that is taken during an automatic overnight update via URL

## [1.9.2] - 2021-01-31

- [BODP-3399](https://itoworld.atlassian.net/browse/BODP-3399) Deactivating an AVL feed is throwing API exception page
- [BODP-3344](https://itoworld.atlassian.net/browse/BODP-3344) API returns error when querying with query parameters greater than 255 characters
- [BODP-3308](https://itoworld.atlassian.net/browse/BODP-3308) When data set is processing, viewing DQ report gives 500 error
- [BODP-3300](https://itoworld.atlassian.net/browse/BODP-3300) Internal Server Error: When consumer logs in after clicking 'Publish bus open data'
- [BODP-3299](https://itoworld.atlassian.net/browse/BODP-3299) Internal Server Error: When Agent accesses my account from 'Find bus open data' page
- [BODP-3298](https://itoworld.atlassian.net/browse/BODP-3298) DQ report not created when StopMissingNaptanWarning's are reported
- [BODP-3290](https://itoworld.atlassian.net/browse/BODP-3290) Deactivating organization also deactivates agents of the organization
- [BODP-3350](https://itoworld.atlassian.net/browse/BODP-3350) Content Update: Add Phone number to service desk number in the contact page
- [BODP-3348](https://itoworld.atlassian.net/browse/BODP-3348) Update IP address in the AVL publishing page
- [BODP-3332](https://itoworld.atlassian.net/browse/BODP-3332) Tech Improvement: Timetable Pipelin Extraction stage memory optimisation
- [BODP-3310](https://itoworld.atlassian.net/browse/BODP-3310) Test - BODP-3309 - View Count of Lines in DQ Report

## [1.9.1] - 2020-12-15

### Bug

- [BODP-3294](https://itoworld.atlassian.net/browse/BODP-3294) Using 0 as the
  offset shouldn't return an error

## [1.9.0] - 2020-12-10

### Bug

- [BODP-2372] - Offset default to 0
- [BODP-2908] - Publishing (Accessibility) - The back link in the cancel
  publish confirmation page does not change the mouse pointer to finger on
  hover over
- [BODP-3124] - Long filenames not displayed clearly when uploading netex
- [BODP-3125] - Incorrect error text when publishing unhandled netex file
- [BODP-3129] - Back button in timetable DQ report takes back to Start Now page unexpectedly
- [BODP-3138] - Stagecoach found issue: Unexpected DQ error for BCT stops
- [BODP-3261] - Description extends beyond page for AVL: Browser dataset consumer
- [BODP-3264] - Update Breadcrumbs in BODS admin portal

### Story

- [BODP-2475] - DFT admin portal: View list of Data Consumers
- [BODP-2477] - DFT admin portal: View Timetable datasets of publishers
- [BODP-2479] - DFT admin portal: View Bus location data feeds of Publishers
- [BODP-2710] - DFT admin portal: View list of Agents
- [BODP-3006] - Track GTFS static file downloads in Google Analytics
- [BODP-3008] - Track Timetables/AVL/Fares API usage in BODS admin portal
- [BODP-3026] - DFT admin portal: View Fares Datasets of Publishers
- [BODP-3028] - DFT Admin Org Management Dashboard: Filter by invitation status
- [BODP-3030] - DFT admin portal: Select multiple Organizations and resend invitation
- [BODP-3082] - Research Spike: Checkboxes against organization invitations
- [BODP-3087] - DfT admin portal: Automated export of BODS metrics
- [BODP-3122] - Update to Guidance page
- [BODP-3171] - Update breadcrumb in BODS admin portal
- [BODP-3173] - BODS Admin Home page
- [BODP-3175] - BODS admin user - View Data Consumer Details
- [BODP-3177] - BODS Admin - Edit Consumer Notes
- [BODP-3179] - BODS admin - Revoke Consumer Access
- [BODP-3181] - BODS Admin - View details of specific Publisher Organization
- [BODP-3183] - BODS Admin - View details of specific agent user
- [BODP-3221] - Track bulk AVL/Fares downloads in Google Analytics
- [BODP-3223] - Track Swagger API usage for fares/AVL in Google Analytics

## [1.8.1] - 2020-12-01

### Bug

- [BODP-3211] - Resend invitation to user from user management by Org admin
  throws an Internal Server Error
- [BODP-3263] - Handle TXC files where stoppoints are represented with WGS84
  without using LocationSystem

### Story

- [BODP-3232] - Content update: Updating of Privacy and data collection notice during sign-up
- [BODP-3254] - Content change: Contact us page
- [BODP-3255] - Content change: for help desk mail box

## [1.8.0] - 2020-11-02

### Bug

- [BODP-2704] - Back button on DQ test description takes user to home page
- [BODP-2844] - DAC: Time Adjustable (A)
- [BODP-2863] - Adding a new NOC gives an Internal Server Error (500)
- [BODP-2902] - Fares API returns Timetables/AVL data
- [BODP-2907] - Existing Shortname and NOC's are not visible when editing as publisher
- [BODP-2949] - Fares: Data set details page breadcrumb is inconsistent
- [BODP-2959] - Org Staff: Account settings is missing notification section and setting
- [BODP-2963] - Fares: Screen reader doesn't read descriptive text for data set
  description field (Accessibility)
- [BODP-3010] - Error message for Fares has 'Data feed' instead of 'Data set'
- [BODP-3035] - Staging Fares: Dashboard tab title isn't consistent with other
  data types
- [BODP-3060] - Agent invitation gives 500 error when an invite already exists
  for the email address
- [BODP-3063] - Fares DAC: Unlabelled Form Fields (A)
- [BODP-3091] - Timetables: Monitoring is not updating some data sets in staging
- [BODP-3095] - Inviting new Agent user, you cannot see the 'user type'
- [BODP-3117] - Agent invitation not displayed under 'User Management' or site admin
- [BODP-3144] - Datafeed set to 'expired' on front end while it is 'Feed up' in
  the backend

### Epic

- [BODP-2411] - Public beta work: Agent Mode
- [BODP-2855] - Fares DAC Improvements

### Dev Task

- [BODP-2976] - Update Guidance

### Story

- [BODP-2554] - Agent Mode Email Notification: When Agent rejects an invite
  from Operator
- [BODP-2556] - BODS Publish homepage
- [BODP-2558] - Account types and pages they'll see
- [BODP-2559] - New Dataset/datafeed dashboard
- [BODP-2562] - My Account: Publisher Admin/Standard/Agent
- [BODP-2564] - New Invite user page: Publisher Admin
- [BODP-2566] - Operator Dashboard: Publisher Agent
- [BODP-2568] - Responding to Pending invitations: Publisher Agent
- [BODP-2570] - Organisation Profile: Publisher Agent
- [BODP-2572] - Account Settings:Publisher Agent
- [BODP-2583] - Changelog: Publisher Agent
- [BODP-2598] - Research Spike: Exploration of Site Map for agent mode
- [BODP-2632] - Data base update for Enabling Agent Mode
- [BODP-2684] - Refactor existing code for Agent Mode
- [BODP-2700] - New Breadcrumb for BODDS Publishers
- [BODP-2708] - Improve BODS capability to handle large files greater than 20mb
  zip for dataset publishing
- [BODP-2737] - Agent User: Publish dataset on behalf of organization
- [BODP-2739] - Migrate database and add User Agent Type
- [BODP-2741] - Creation of User Agent through Django Admin
- [BODP-2743] - User Agent: Viewing existing datasets
- [BODP-2934] - Update Netex Version
- [BODP-2977] - Leaving an organization: Publisher Agent
- [BODP-2981] - Agent Mode Email Notification: Any Dataset/datafeed related emails
- [BODP-2983] - Agent Mode Email Notification: When Agent leaves Operator’s organisation
- [BODP-2985] - Agent Mode Email Notification: When Operator removes Agent
- [BODP-2987] - Agent Mode Email Notification: When NOC is changed
- [BODP-2989] - Agent Mode Email Notification: When Operator sends invitation
  to an Agent
- [BODP-2991] - Agent Mode Email Notification: When Agent accepts an invite
  from Operator
- [BODP-3000] - Research Spike: Javascript libraries for session timeout popup
- [BODP-3003] - Agent Mode: Enter organization name
- [BODP-3013] - Update Data set details to include 'Earliest State Date' and
  'Earliest End Date': Timetable/Fares
- [BODP-3040] - Update text from 'Request Account' to 'Create Account'
- [BODP-3098] - Removing an Agent by 'Publisher Admin'
- [BODP-3100] - Removing an Agent by 'System Admin'
- [BODP-3109] - Resend Invitation to Agent - Publisher Admin
- [BODP-3112] - Resend Invitation to Agent - Site Admin

## [1.7.1] - 2020-10-13

### Bug

- Dashboard tab title isn't consistent with other data types [BODP-3032](https://itoworld.atlassian.net/browse/BODP-3032)
- Published data feed version doesn't match the data domain version [BODP-3033](https://itoworld.atlassian.net/browse/BODP-3033)

### Changes

- Increase frequency of Timetable Monitoring Task to twice a day [BODP-2939](https://itoworld.atlassian.net/browse/BODP-2939)

## [1.0.7] - 2020-09-04

### Added

### Changes

### Fixed

## [1.0.6] - 2020-08-13

### Changes

- Updated DfT phone number [BODP-2798](https://itoworld.atlassian.net/browse/BODP-2798)
- Bumped the year in the [BODP-2649](https://itoworld.atlassian.net/browse/BODP-2649)

### Fixed

For KPMG builds use the commit tag

## [1.0.2] - 2020-04-29

### Changes

- Change expiry time of datasets to 5am the day after they expireAll organisation drafts are visible in the draft tab fo ([BODP-2350](https://itoworld.atlassian.net/browse/BODP-2350))

## [1.0.1] - 2020-03-11

### Fixed

- All organisation drafts are visible in the draft tab for a single org ([BODP-2246](https://itoworld.atlassian.net/browse/BODP-2246))

## [1.0.0] - 2020-03-6

### Added

- Accounts DFT Staff ([BODP-1050](https://itoworld.atlassian.net/browse/BODP-1050))
- Accounts DFT Staff - View Organisations ([BODP-1052](https://itoworld.atlassian.net/browse/BODP-1052))
- Accounts DFT Staff - Re-send organisation invite ([BODP-1054](https://itoworld.atlassian.net/browse/BODP-1054))
- Accounts DFT Staff - Invite New Organisation ([BODP-1056](https://itoworld.atlassian.net/browse/BODP-1056))
- Accounts DFT Staff - Organisation Page ([BODP-1058](https://itoworld.atlassian.net/browse/BODP-1058))
- Accounts DFT Staff - Delete Organisation ([BODP-1060](https://itoworld.atlassian.net/browse/BODP-1060))
- Accounts DFT Staff - View data sets ([BODP-1062](https://itoworld.atlassian.net/browse/BODP-1062))
- Accounts DFT Staff - Edit Organisation ([BODP-1064](https://itoworld.atlassian.net/browse/BODP-1064))
- Accounts DFT Staff Edit Account ([BODP-1066](https://itoworld.atlassian.net/browse/BODP-1066))
- Accounts DFT Staff Edit Account_Password ([BODP-1068](https://itoworld.atlassian.net/browse/BODP-1068))
- DQ OC8: First stop set down only ([BODP-1308](https://itoworld.atlassian.net/browse/BODP-1308))
- DQ OC8: First stop set down only observation page ([BODP-1310](https://itoworld.atlassian.net/browse/BODP-1310))
- DQ OC9: Last Stop Pickup Only (Base Story) ([BODP-1384](https://itoworld.atlassian.net/browse/BODP-1384))
- DQ OC9: Last Stop Pickup Only Observation Page (Base Story) ([BODP-1386](https://itoworld.atlassian.net/browse/BODP-1386))
- OC11: TP not in First Stop ([BODP-1409](https://itoworld.atlassian.net/browse/BODP-1409))
- OC11: TP not in First Stop Observation Page ([BODP-1411](https://itoworld.atlassian.net/browse/BODP-1411))
- My data sets dashboard ([BODP-1483](https://itoworld.atlassian.net/browse/BODP-1483))
- Operator-specific data set view ([BODP-1485](https://itoworld.atlassian.net/browse/BODP-1485))
- Specific data sets page ([BODP-1518](https://itoworld.atlassian.net/browse/BODP-1518))
- Deactivation flow ([BODP-1520](https://itoworld.atlassian.net/browse/BODP-1520))
- Data set dashboard: Inactive tab ([BODP-1522](https://itoworld.atlassian.net/browse/BODP-1522))
- Specific data sets page: Expired ([BODP-1524](https://itoworld.atlassian.net/browse/BODP-1524))
- Specific data sets page: Inactive ([BODP-1526](https://itoworld.atlassian.net/browse/BODP-1526))
- Cancellation: Update flow (only during Step 1&2) ([BODP-1626](https://itoworld.atlassian.net/browse/BODP-1626))
- Infer whether a file is xml or zip without using 'Content-Type' header ([BODP-2104](https://itoworld.atlassian.net/browse/BODP-2104))
- Accounts DfT Staff - User management page ([BODP-2107](https://itoworld.atlassian.net/browse/BODP-2107))

### Fixed

- No link to DQ report from data set details section ([BODP-1737](https://itoworld.atlassian.net/browse/BODP-1737))
- TXC file fails to complete DQ check ([BODP-1843](https://itoworld.atlassian.net/browse/BODP-1843))
- Dev documentation - Downloading data has the wrong sub section title ([BODP-1862](https://itoworld.atlassian.net/browse/BODP-1862))
- Unexpected error for Missing destination display ([BODP-1893](https://itoworld.atlassian.net/browse/BODP-1893))
- Staging - Zip files not generating DQ report ([BODP-1915](https://itoworld.atlassian.net/browse/BODP-1915))
- Large zip does not get past 10% when being uploaded ([BODP-1925](https://itoworld.atlassian.net/browse/BODP-1925))
- IE browser compatibility - copying API code for dataset does not function and does not meet GDS ([BODP-1944](https://itoworld.atlassian.net/browse/BODP-1944))
- Email address confirmation screen font not consistent ([BODP-1953](https://itoworld.atlassian.net/browse/BODP-1953))
- Time given in dataset summary not correct (different to email published time) ([BODP-1954](https://itoworld.atlassian.net/browse/BODP-1954))
- 30 day expiry email sent with incorrect dataset name when the dataset is a duplicate and suffixed with \_1 ([BODP-1966](https://itoworld.atlassian.net/browse/BODP-1966))
- Incorrect warning message on duplicate journey warning detail page ([BODP-1970](https://itoworld.atlassian.net/browse/BODP-1970))
- Regression testing: All zip files fail to upload ([BODP-1988](https://itoworld.atlassian.net/browse/BODP-1988))
- Cannot upload the zip file and the URL link is invalid to get data sets on BODP internal ([BODP-1994](https://itoworld.atlassian.net/browse/BODP-1994))
- Cannot upload those zip files on BODP internal ([BODP-1995](https://itoworld.atlassian.net/browse/BODP-1995))
- DQ Map not drawn properly on drill down for DQ when route that triggers dq rule contains non-naptan stop ([BODP-2065](https://itoworld.atlassian.net/browse/BODP-2065))
- Regression: Monitoring - Multiple changes to end-point is not triggering email ([BODP-2066](https://itoworld.atlassian.net/browse/BODP-2066))
- Feedback on monitored dataset that has changed causes ISE ([BODP-2067](https://itoworld.atlassian.net/browse/BODP-2067))
- Guidance text - suggested change to TransXChange version quoted. ([BODP-2069](https://itoworld.atlassian.net/browse/BODP-2069))
- Guidance text - suggested change to mention of Text vs XML ([BODP-2070](https://itoworld.atlassian.net/browse/BODP-2070))
- Updating, updated draft gives ISE when trying to upload file ([BODP-2072](https://itoworld.atlassian.net/browse/BODP-2072))
- Search: Bringing back seach results after entering text, leads to error in the text on the results table ([BODP-2073](https://itoworld.atlassian.net/browse/BODP-2073))
- Guidance references internal Ito World URLs ([BODP-2095](https://itoworld.atlassian.net/browse/BODP-2095))
- Dead invitation link - 410 error ([BODP-2102](https://itoworld.atlassian.net/browse/BODP-2102))

## [0.8.2] - 2020-02-13

### Fixed

- 'Download all data sets' link downloads an old zip, not containing recent datasets ([BODP-2136](https://itoworld.atlassian.net/browse/BODP-2136))

## [0.8.1] - 2020-01-24

### Changes

- Change banner from Alpha to Beta ([BODP-2032](https://itoworld.atlassian.net/browse/BODP-2032))

### Fixed

- The cache is working on the first upload, but the 12 hour cache refresh is the part that is not happening on BODP internal ([BODP-1989](https://itoworld.atlassian.net/browse/BODP-1989))
- Error status of data sets if there is an error with the URL on BODP internal ([BODP-1993](https://itoworld.atlassian.net/browse/BODP-1993))

## [0.8.0] - 2020-1-16

### Added

- DQ OC19: Missing Destination Display Observation Page ([BODP-1399](https://itoworld.atlassian.net/browse/BODP-1399))
- DQ OC2: Backwards Timing ([BODP-1418](https://itoworld.atlassian.net/browse/BODP-1418))
- DQ OC2:Backwards Timing Observation Page ([BODP-1420](https://itoworld.atlassian.net/browse/BODP-1420))
- Update accessibility statement ([BODP-1510](https://itoworld.atlassian.net/browse/BODP-1510))
- View data quality report -> Generating data quality report (whilst it's being generated) ([BODP-1856](https://itoworld.atlassian.net/browse/BODP-1856))
- Add Antivirus scanning to pipeline ([BODP-1865](https://itoworld.atlassian.net/browse/BODP-1865))
- Prevent multiple sessions from different IP addresses ([BODP-1939](https://itoworld.atlassian.net/browse/BODP-1939))
- Set SessionId cookie with Secure flag and HttpOnly flag ([BODP-1960](https://itoworld.atlassian.net/browse/BODP-1960))
- Username enumeration: Do not allow attacker to work out if an email is registered on the service ([BODP-1963](https://itoworld.atlassian.net/browse/BODP-1963))
- Invite users through the admin console ([BODP-1972](https://itoworld.atlassian.net/browse/BODP-1972))

### Changes

- Replace Ito Google Analytics account with DfT account ([BODP-1868](https://itoworld.atlassian.net/browse/BODP-1868))
- Text change to privacy statement ([BODP-1981](https://itoworld.atlassian.net/browse/BODP-1981))
- Change email and number on contact page ([BODP-1983](https://itoworld.atlassian.net/browse/BODP-1983))

### Fixed

- Exploratory - when clicking on the back breadcrumb on Operator data page the user is returned to the wrong page ([BODP-1360](https://itoworld.atlassian.net/browse/BODP-1360))
- Search page - Ellipsis in the pagination shows 'page not found' ([BODP-1640](https://itoworld.atlassian.net/browse/BODP-1640))
- Console errors when not signed in ([BODP-1685](https://itoworld.atlassian.net/browse/BODP-1685))
- Page not found - pagination menu ([BODP-1776](https://itoworld.atlassian.net/browse/BODP-1776))
- Consumer registration confirmation font not consistent ([BODP-1785](https://itoworld.atlassian.net/browse/BODP-1785))
- Data Quality Report pages do not have titles ([BODP-1818](https://itoworld.atlassian.net/browse/BODP-1818))
- Re-sending email invite process does not include confirmation email has been sent ([BODP-1827](https://itoworld.atlassian.net/browse/BODP-1827))
- Find Bus Open Data: Using the API - get /dataset 400 response undocumented (BODP-1121) ([BODP-1828](https://itoworld.atlassian.net/browse/BODP-1828))
- Error for failed DQ check does not meet GDS format ([BODP-1859](https://itoworld.atlassian.net/browse/BODP-1859))
- Unexpected breadcrumb links on resend invitation page ([BODP-1867](https://itoworld.atlassian.net/browse/BODP-1867))
- For overlapping journeys show the top of the columns over two lines instead of one ([BODP-1876](https://itoworld.atlassian.net/browse/BODP-1876))
- Unexpected items of service number undefined ([BODP-1896](https://itoworld.atlassian.net/browse/BODP-1896))
- Clean git history to remove >100MB file preventing us from committing to DfT repo ([BODP-1897](https://itoworld.atlassian.net/browse/BODP-1897))
- Description mismatch ([BODP-1898](https://itoworld.atlassian.net/browse/BODP-1898))
- 'Example vehicle journeys affected' text doesn't match design ([BODP-1899](https://itoworld.atlassian.net/browse/BODP-1899))
- Affected journeys - Multiple titles/headings not matching designs ([BODP-1900](https://itoworld.atlassian.net/browse/BODP-1900))
- Navigation from publisher email activation confirmation screen takes to Find bus open data ([BODP-1902](https://itoworld.atlassian.net/browse/BODP-1902))
- Description doesn't match designs ([BODP-1904](https://itoworld.atlassian.net/browse/BODP-1904))
- Clicking on observation page gives ISE ([BODP-1909](https://itoworld.atlassian.net/browse/BODP-1909))
- Observation definition error on BODP staging (Last stop is not a timing stop) ([BODP-1912](https://itoworld.atlassian.net/browse/BODP-1912))
- Unable to name dataset correctly on KPMG architecture ([BODP-1913](https://itoworld.atlassian.net/browse/BODP-1913))
- DQ OC17: Incorrect Stop Type - Journey count incorrect ([BODP-1914](https://itoworld.atlassian.net/browse/BODP-1914))
- Attempting to login as consumer to publish workflow - forbidden 403 page with bad 'contact' link ([BODP-1916](https://itoworld.atlassian.net/browse/BODP-1916))
- Last point missing timing point - pagination not working ([BODP-1918](https://itoworld.atlassian.net/browse/BODP-1918))
- Unexpected resend button instead of delete button ([BODP-1923](https://itoworld.atlassian.net/browse/BODP-1923))
- Large zip does not start upload if submitted via URL ([BODP-1926](https://itoworld.atlassian.net/browse/BODP-1926))
- Change file naming from districts to localities ([BODP-1928](https://itoworld.atlassian.net/browse/BODP-1928))
- Upload process fails all TXC files ([BODP-1929](https://itoworld.atlassian.net/browse/BODP-1929))
- Link to contact page is not working ([BODP-1945](https://itoworld.atlassian.net/browse/BODP-1945))
- Change url to NOC database ([BODP-1795](https://itoworld.atlassian.net/browse/BODP-1795))

## [0.7.2] - 2020-1-6

### Changes

- Reduce session timeout to 30 minutes ([BODP-1935](https://itoworld.atlassian.net/browse/BODP-1935))
- Increase strict transport security setting to one year ([BODP-1937](https://itoworld.atlassian.net/browse/BODP-1937))

## [0.7.1] - 2019-12-17

### Fixed

- Paginate journey table rows with page size of 10 ([BODP-1835](https://itoworld.atlassian.net/browse/BODP-1835))
- Show correct value for timing pattern count ([BODP-1847](https://itoworld.atlassian.net/browse/BODP-1847))
- Add missing arrow to start button ([BODP-1851](https://itoworld.atlassian.net/browse/BODP-1851))
- Update dataset and report when a new dataset is uploaded ([BODP-1852](https://itoworld.atlassian.net/browse/BODP-1852),
  [BODP-1881](https://itoworld.atlassian.net/browse/BODP-1881), [BODP-1882](https://itoworld.atlassian.net/browse/BODP-1882))
- Limit access to DQS reports to only organisation users ([BODP-1864](https://itoworld.atlassian.net/browse/BODP-1864)) -`Set`download_url` in dataset API to obfuscate S3 url ([BODP-1863](https://itoworld.atlassian.net/browse/BODP-1863))
- Make Open API read only ([BODP-1903](https://itoworld.atlassian.net/browse/BODP-1903))

## [0.7.0] - 2019-12-11

### Added

- Add Data Quality report to publishing flow ([BODP-1267](https://itoworld.atlassian.net/browse/BODP-1267))
- Add periodic Celery task to update NaPTaN ([BODP-699](https://itoworld.atlassian.net/browse/BODP-699))

### Changes

- Update About page content ([BODP-798](https://itoworld.atlassian.net/browse/BODP-798))
- Allow publisher to delete dataset ([BODP-1455](https://itoworld.atlassian.net/browse/BODP-1455))
- Extract provisional NaPTaN stops from TXC ([BODP-1642](https://itoworld.atlassian.net/browse/BODP-1642))

### Fixed

- Fix data set map on IE11 ([BODP-1754](https://itoworld.atlassian.net/browse/BODP-1754))
- Fix maps on IE11 which do not render ([BODP-1743](https://itoworld.atlassian.net/browse/BODP-1743),
  [BODP-1754](https://itoworld.atlassian.net/browse/BODP-1754))
- Fix broken back link on DQS warning page ([BODP-1769](https://itoworld.atlassian.net/browse/BODP-1769))
- Fix url path to DQS report so it doesn't expose revision_id ([BODP-1786](https://itoworld.atlassian.net/browse/BODP-1786))
- Fix sort indicator missing on dataset list table ([BODP-1201](https://itoworld.atlassian.net/browse/BODP-1201))
- Fix typo on sign out page ([BODP-1481](https://itoworld.atlassian.net/browse/BODP-1481))
- Fix dropdown menu on IE11/Edge ([BODP-1641](https://itoworld.atlassian.net/browse/BODP-1641))

## [0.6.1] - 2019-12-4

### Changes

- Chore: Add deployment scripts

## [0.6.0] - 2019-11-29

### Added

- Add models for data quality reports ([BODP-1435](https://itoworld.atlassian.net/browse/BODP-1435))
- Allow users to leave feedback on data sets ([BODP-1038](https://itoworld.atlassian.net/browse/BODP-1038))
- New edit users page for organisation admins ([BODP-1076](https://itoworld.atlassian.net/browse/BODP-1078))
- Add organisation profile pages for organisation admins ([BODP-1082](https://itoworld.atlassian.net/browse/BODP-1082))
- Add notification settings on organisation admin settings page ([BODP-1086](https://itoworld.atlassian.net/browse/BODP-1086))
- Add data set subscription for data consumers ([BODP-1152](https://itoworld.atlassian.net/browse/BODP-1152))

### Changes

- Improve consistency of success pages by using base success template
- Migrate to new Notfiy account, update email templates, and implement new features for development ([BODP-801](https://itoworld.atlassian.net/browse/801),[BODP-1287](https://itoworld.atlassian.net/browse/1287))
- Allow data consumers to download expired data sets ([BODP-957](https://itoworld.atlassian.net/browse/BODP-957))
- Update styling on authentication pages ([BODP-996](https://itoworld.atlassian.net/browse/BODP-996))
- Update change password pages for all user types ([BODP-1044](https://itoworld.atlassian.net/browse/BODP-1044))
- Update styling on user management pages ([BODP-1076](https://itoworld.atlassian.net/browse/BODP-1076))
- Ensure user can get to data consumer home page ([BODP-1115](https://itoworld.atlassian.net/browse/BODP-1115))
- Update API documentation ([BODP-1117](https://itoworld.atlassian.net/browse/BODP-1117))
- Update archived user confirmation page ([BODP-1144](https://itoworld.atlassian.net/browse/BODP-1144))
- Accessibility improvements (DAC level A) ([BODP-1207](https://itoworld.atlassian.net/browse/BODP-1207))
- Accessibility improvements (DAC level AA) ([BODP-1215](https://itoworld.atlassian.net/browse/BODP-1215))
- Support provisional stops not yet in NaPTAN ([BODP-1252](https://itoworld.atlassian.net/browse/1252)
- Accessibility improvements (DAC level AAA) ([BODP-1219](https://itoworld.atlassian.net/browse/BODP-1219))
- NOC can be added when creating a new organisation ([BODP-1371](https://itoworld.atlassian.net/browse/BODP-1371))
- Update update footer ([BODP-1390](https://itoworld.atlassian.net/browse/BODP-1390))
- Update <title> tags ([BODP-1490](https://itoworld.atlassian.net/browse/1490))

### Fixed

- Fix timezone problems when running tasks ([BODP-961](https://itoworld.atlassian.net/browse/BODP-961))
- Ensure admin area is included when naming uploaded TXC files ([BODP-1188](https://itoworld.atlassian.net/browse/BODP-1188))
- Fix menu dropdown in header ([BODP-1192](https://itoworld.atlassian.net/browse/BODP-1192))
- Fix API search parameter error ([BODP-1198](https://itoworld.atlassian.net/browse/BODP-1198))
- Fix filtering of data sets by geographical area ([BODP-1199](https://itoworld.atlassian.net/browse/BODP-1199))
- Fix console error on publishers' data sets page ([BODP-1242](https://itoworld.atlassian.net/browse/1242))
- Fix accessibility issues in My Account menu dropdown ([BODP-1255](https://itoworld.atlassian.net/browse/1255))
- Fix link to download data sets page ([BODP-1276](https://itoworld.atlassian.net/browse/BODP-1276))
- Fix AttributeError when publish data set ([BODP-1339](https://itoworld.atlassian.net/browse/BODP-1339))
- Ensure publisher data sets have "preview developer view" link ([BODP-1358](https://itoworld.atlassian.net/browse/BODP-1358))
- Fix links to download dataset page ([BODP-1364](https://itoworld.atlassian.net/browse/BODP-1364))
- Fix representation of lines in API results ([BODP-1372](https://itoworld.atlassian.net/browse/1372))
- Fix timezone problems in notification emails ([BODP-1417](https://itoworld.atlassian.net/browse/BODP-1417))
- Fix ValidationError preventing invitations to new organisation users ([BODP-1439](https://itoworld.atlassian.net/browse/BODP-1439))
- Fix IntegrityError when updating data set ([BODP-1441](https://itoworld.atlassian.net/browse/BODP-1441))
- Add alernate text to image on search page ([BODP-1464](https://itoworld.atlassian.net/browse/1464))
- Fix error in which datasets don't transition to expired when expected ([BODP-1465](https://itoworld.atlassian.net/browse/1465))

## [0.5.4] - 2019-11-14

### Changed

- Make AWS environment variables optional in production settings

## [0.5.3] - 2019-11-7

### Fixed

- Call collectstatic management command in gunicorn start script

## [0.5.2] - 2019-11-5

### Changes

- Remove management commands from gunicorn start script
- Add `DJANGO_ALLOWED_HOSTS` to environment settings

## [0.5.1] - 2019-10-23

### Added

- Add GitLab CI task to push image to ECR

## [0.5.0] - 2019-10-17

### Added

- Add bulk download and changes download feature ([BODP-992](https://itoworld.atlassian.net/browse/BODP-992))
- Add support dataset revisions in publishing workflow ([BODP-964](https://itoworld.atlassian.net/browse/BODP-964))
- Generate dataset name from contents of timetable data ([BODP-981](https://itoworld.atlassian.net/browse/BODP-981))

### Changes

- Redesign publishing workflow ([BODP-898](https://itoworld.atlassian.net/browse/BODP-898))
- Add changes to Browse Bus Open Data home page ([BODP-958](https://itoworld.atlassian.net/browse/BODP-958))
- Add changes to Browse Bus Open Data pages ([BODP-976](https://itoworld.atlassian.net/browse/BODP-976))
- Add changes to Browse Bus Open Data search page ([BODP-978](https://itoworld.atlassian.net/browse/BODP-978))
- Treat invalid API query parameters as an error ([BODP-1006](https://itoworld.atlassian.net/browse/BODP-1006))

### Fixed

- Fix refreshing issue on data sets page ([BODP-991](https://itoworld.atlassian.net/browse/BODP-991))
- Updates to browse by area ([BODP-1004](https://itoworld.atlassian.net/browse/BODP-1004))
- Fix link to About Bus Open Data ([BODP-1005](https://itoworld.atlassian.net/browse/BODP-1005))

## [0.4.0] - 2019-10-10

### Fixed

- Fix monitoring solution detecting incorrect changes ([BODP-828](https://itoworld.atlassian.net/browse/BODP-828))
- Fix caching issue causing wrong service homepage to be served ([BODP-962](https://itoworld.atlassian.net/browse/BODP-962))
- Fix erroneous validation error in publishing form file field ([BODP-1029](https://itoworld.atlassian.net/browse/BODP-1029))

## [0.3.0] - 2019-09-20

### Changes

- Format timestamps in dataset table to show Europe/London timezone ([BODP-930](https://itoworld.atlassian.net/browse/BODP-930))
- Change order of aside links on sign in pages ([BODP-960](https://itoworld.atlassian.net/browse/BODP-960))

### Fixed

- Change 'data feed' to 'dataset' ([BODP-927](https://itoworld.atlassian.net/browse/BODP-927))
- Change placeholder text on dataset table ([BODP-928](https://itoworld.atlassian.net/browse/BODP-928))
- Add missing password guidance on reset flow ([BODP-929](https://itoworld.atlassian.net/browse/BODP-929))
- Fix typo in error message ([BODP-943](https://itoworld.atlassian.net/browse/BODP-943))
- Capitalise 'Troubleshooting' link on contact page ([BODP-959](https://itoworld.atlassian.net/browse/BODP-959))

## [0.2.0] - 2019-09-09

### Added

- Swagger API documentation ([BODP-525](https://itoworld.atlassian.net/browse/BODP-525))
- REST API: Add _noc_ query paramter ([BODP-877](https://itoworld.atlassian.net/browse/BODP-877))
- REST API: Add admin areas query paramter ([BODP-878](https://itoworld.atlassian.net/browse/BODP-878))
- REST API: Add _modifiedDate_ query paramter ([BODP-879](https://itoworld.atlassian.net/browse/BODP-879))
- REST API: Add _startDateStart_ and _startDateEnd_ query paramters ([BODP-880](https://itoworld.atlassian.net/browse/BODP-880))
- REST API: Add _endDateStart_ and _endDateEnd_ query paramters ([BODP-881](https://itoworld.atlassian.net/browse/BODP-881))
- REST API: Restrict results to published datasets ([BODP-892](https://itoworld.atlassian.net/browse/BODP-892))
- REST API: Add _search_ query paramter ([BODP-893](https://itoworld.atlassian.net/browse/BODP-893))
- REST API: Add limit and offset query parameters ([BODP-897](https://itoworld.atlassian.net/browse/BODP-897))

### Changes

- User testing refinements 1.1: Update Find landing page ([BODP-857](https://itoworld.atlassian.net/browse/BODP-857))
- User testing refinements 1.1: Update browse page ([BODP-858](https://itoworld.atlassian.net/browse/BODP-858))

### Fixed

- Progress spinner does not work correctly for multiple uploads ([BODP-855](https://itoworld.atlassian.net/browse/BODP-855))
- Progress spinner updates the wrong way ([BODP-856](https://itoworld.atlassian.net/browse/BODP-856))
- Remove extra _h1_ elements on dataset delete and archive pages ([BODP-825](https://itoworld.atlassian.net/browse/BODP-825))
- Fix broken link in browse by category section ([BODP-886](https://itoworld.atlassian.net/browse/BODP-886))
- Fix dataset download permission denied issue ([BODP-931](https://itoworld.atlassian.net/browse/BODP-931))
- REST API: Change status _live_ to _published_ ([BODP-939](https://itoworld.atlassian.net/browse/BODP-939))
- REST API: Add accepted datetime format to error message ([BODP-941](https://itoworld.atlassian.net/browse/BODP-941))
- Change _catalogue/_ page url path to _category/_ ([BODP-942](https://itoworld.atlassian.net/browse/BODP-942))

## [0.1.0] - 2019-08-27

### Added

- Add logout success page ([BODP-743](https://itoworld.atlassian.net/browse/BODP-743))
- Make dataset archive flow robust ([BODP-826](https://itoworld.atlassian.net/browse/BODP-826))

### Changes

- Update terminology across site ([BODP-673](https://itoworld.atlassian.net/browse/BODP-673))
- Change dataset table tab labels ([BODP-759](https://itoworld.atlassian.net/browse/BODP-759))
- Changes to publishing flow step 1 ([BODP-762](https://itoworld.atlassian.net/browse/BODP-762))
- Changes to publishing flow step 2 ([BODP-763](https://itoworld.atlassian.net/browse/BODP-763))
- Changes to publishing flow update font ([BODP-765](https://itoworld.atlassian.net/browse/BODP-765))
- Change 'Update data' to 'Change data' ([BODP-767](https://itoworld.atlassian.net/browse/BODP-767))
- Redesign dataset deletion page ([BODP-768](https://itoworld.atlassian.net/browse/BODP-768))

### Fixed

- Fix map on IE 11 ([BODP-773](https://itoworld.atlassian.net/browse/BODP-773))
- Prevent long urls overflowing in publishing flow ([BODP-776](https://itoworld.atlassian.net/browse/BODP-776))
- Make bus operator guidance section headings consistent ([BODP-784](https://itoworld.atlassian.net/browse/BODP-784))
- Remove duplicate navigation links on guidance pages ([BODP-788](https://itoworld.atlassian.net/browse/BODP-788))
- Ensure publishing views restrict data access ([BODP-831](https://itoworld.atlassian.net/browse/BODP-831))

[unreleased]: https://gitlab.ops.itoworld.com/transit-hub/bodp-django/compare/master...develop
[next]: https://gitlab.ops.itoworld.com/transit-hub/bodp-django/compare/master...release%2Fv1.0.0
[1.0.1]: https://gitlab.ops.itoworld.com/transit-hub/bodp-django/-/tags/v1.0.1
[1.0.0]: https://gitlab.ops.itoworld.com/transit-hub/bodp-django/-/tags/v1.0.0
[0.8.0]: https://gitlab.ops.itoworld.com/transit-hub/bodp-django/-/tags/v0.8.0
[0.7.2]: https://gitlab.ops.itoworld.com/transit-hub/bodp-django/-/tags/v0.7.2
[0.7.1]: https://gitlab.ops.itoworld.com/transit-hub/bodp-django/-/tags/v0.7.1
[0.7.0]: https://gitlab.ops.itoworld.com/transit-hub/bodp-django/-/tags/v0.7.0
[0.6.1]: https://gitlab.ops.itoworld.com/transit-hub/bodp-django/-/tags/v0.6.1
[0.6.0]: https://gitlab.ops.itoworld.com/transit-hub/bodp-django/-/tags/v0.6.0
[0.5.4]: https://gitlab.ops.itoworld.com/transit-hub/bodp-django/-/tags/v0.5.4
[0.5.3]: https://gitlab.ops.itoworld.com/transit-hub/bodp-django/-/tags/v0.5.3
[0.5.2]: https://gitlab.ops.itoworld.com/transit-hub/bodp-django/-/tags/v0.5.2
[0.5.1]: https://gitlab.ops.itoworld.com/transit-hub/bodp-django/-/tags/v0.5.1
[0.5.0]: https://gitlab.ops.itoworld.com/transit-hub/bodp-django/-/tags/v0.5.0
[0.4.0]: https://gitlab.ops.itoworld.com/transit-hub/bodp-django/-/tags/v0.4.0
[0.3.0]: https://gitlab.ops.itoworld.com/transit-hub/bodp-django/-/tags/v0.3.0
[0.2.0]: https://gitlab.ops.itoworld.com/transit-hub/bodp-django/-/tags/v0.2.0
[0.1.0]: https://gitlab.ops.itoworld.com/transit-hub/bodp-django/-/tags/v0.1.0
