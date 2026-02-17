/**
 * Overview Section
 * Source: transit_odp/guidance/templates/guidance/bus_operators/overview.html
 */

import { RequirementsTable } from './RequirementsTable';

export function OverviewSection() {
  return (
    <>
      <h2 className="govuk-heading-l">Overview</h2>
      <p data-qa="overview-paragraph" className="govuk-body">
        The Bus Open Data Service (BODS) is the central service for publishing high
        quality information for all local bus services in England. The Bus Services Act
        2017 requires operators of local bus services in England to publish data to the
        Bus Open Data Service. There are three types of data that operators must publish
        in certain data formats: timetables, bus location and fares. Local transport
        authorities are required to maintain NaPTAN stop data.
      </p>
      <RequirementsTable />
    </>
  );
}


