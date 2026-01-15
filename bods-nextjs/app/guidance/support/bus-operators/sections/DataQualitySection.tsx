/**
 * Data Quality Section
 * Source: transit_odp/guidance/templates/guidance/bus_operators/dataquality.html
 */

export function DataQualitySection() {
  return (
    <>
      <h2 className="govuk-heading-l">Data quality</h2>
      <p className="govuk-body">
        High quality data is essential for the Bus Open Data Service to deliver value
        to passengers and app developers. Operators are expected to maintain accurate,
        complete and timely data.
      </p>

      <h2 className="govuk-heading-l">PTI validation</h2>
      <p className="govuk-body">
        The Bus Open Data Service validates timetables data against the PTI (Profile for
        TransXChange - Interchange) standard. Data that does not meet PTI requirements
        may be flagged as non-compliant.
      </p>

      <h2 className="govuk-heading-l">Data quality reports</h2>
      <p className="govuk-body">
        Operators can view data quality reports for their published data. These reports
        highlight any issues that may affect the usefulness of the data for passengers
        and app developers.
      </p>

      <h2 className="govuk-heading-l">Common data quality issues</h2>
      <ul className="govuk-list govuk-list--bullet">
        <li>Missing or incorrect stop references</li>
        <li>Expired or outdated timetable data</li>
        <li>Incorrect operator or service codes</li>
        <li>Incomplete journey patterns</li>
      </ul>
    </>
  );
}


