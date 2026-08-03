import Link from 'next/link';

export function DataCatalogueSection() {
  return (
    <>
      <h1 className="govuk-heading-l">Data Catalogue</h1>
      <p className="govuk-body">
        The data catalogue zip contains a machine-readable overview of data currently on BODS.
        It covers primary sources (TransXChange timetables, SIRI-VM location and NeTEx fares).
      </p>
      <p className="govuk-body">
        <Link className="govuk-link" href="/data">
          Download the data catalogue
        </Link>{' '}
        for CSV files that describe data sets, organisations, locations and associated NOCs.
      </p>
      <p className="govuk-body">
        Field definitions are documented in the developer resources and include overall catalogue,
        timetables, fares, disruptions, organisations, location and operator NOC definitions.
      </p>
    </>
  );
}

