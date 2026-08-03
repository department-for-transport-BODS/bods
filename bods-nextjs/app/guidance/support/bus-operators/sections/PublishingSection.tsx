/**
 * Publishing Data Section
 * Source: transit_odp/guidance/templates/guidance/bus_operators/publish_data.html
 */

import { RequirementsTable } from './RequirementsTable';

export function PublishingSection() {
  return (
    <>
      <h2 data-qa="publish-data-header" className="govuk-heading-l">Publishing data</h2>
      <p className="govuk-body">
        Operators are expected to have the people, processes and technology needed to
        maintain timely, complete and accurate information to the Bus Open Data Service.
        Operators, and those publishing as agents on behalf of operators, should have
        all their data published and be able to maintain it, prior to the requirement
        date; allowing business processes to be tested and established prior to the
        requirement.
      </p>
      <RequirementsTable />

      <h2 data-qa="maintaining-data-header" className="govuk-heading-l">Maintaining data</h2>
      <p className="govuk-body">
        Operators are expected to have timely, complete and accurate information
        published to the service at all times. The most effective method in organising
        this for timetables and fares data is to maintain the URL endpoints published,
        which will be cached to the service daily around 6:00am. The number of data sets
        published is at the discretion of the operator. Many operators are choosing to
        have a single data set, with a single URL endpoint hosting the data. Others are
        choosing to have a data set per operating company, certain regions, lines or the
        underlying scheduler.
      </p>

      <h2 data-qa="dataset-naming-header" className="govuk-heading-l">Data set naming</h2>
      <p className="govuk-body">
        The service will automatically name data provided, using an internal naming
        convention, not the original file name. The unique identifier for each individual
        data set is given by the data set ID or data feed ID.
      </p>

      <h2 data-qa="timetable-fare-header" className="govuk-heading-l">Publishing timetables and fares data</h2>
      <p className="govuk-body">
        Most operators must host their own timetables and fares data and publish it by
        providing a URL link to the data. Operators who run fewer than forty services
        may choose to upload their data on BODS. Multiple files will only be accepted
        if uploaded in a ZIP file. For trial purposes files may be uploaded by larger
        operators.
      </p>

      <h2 data-qa="providing-url-header" className="govuk-heading-l">Providing a URL link</h2>
      <p className="govuk-body">
        Bus operators should provide a URL link to their hosted data. The data exposed
        through this link should be data that the operator wishes to be published.
        Publishers are expected to maintain their end point and remove expired data.
      </p>
      <p className="govuk-body">
        Data for timetables will be updated in the cache for data consumer from a URL
        daily, around 6:00 UCT.
      </p>

      <h2 data-qa="uploading-a-file-header" className="govuk-heading-l">Uploading a file</h2>
      <p className="govuk-body">
        Small operators may choose to upload a single XML file or zip containing
        multiple XML files. Please update data as it expires to ensure there is a valid
        data set published on the service.
      </p>

      <h2 data-qa="publish-bus-data-header" className="govuk-heading-l">Publishing bus location data</h2>
      <h2 data-qa="publish-feed-header" className="govuk-heading-l">Providing a feed</h2>
      <p className="govuk-body">
        Automatic vehicle location data will need to be provided using a SIRI-VM data
        feed that can be provided by real time/ETM suppliers.
      </p>
    </>
  );
}


