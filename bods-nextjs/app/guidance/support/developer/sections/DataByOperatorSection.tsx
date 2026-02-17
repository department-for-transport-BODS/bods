import Link from 'next/link';

export function DataByOperatorSection() {
  return (
    <>
      <h1 className="govuk-heading-l">Data by operator or location</h1>
      <h2 className="govuk-heading-m">Getting data by operator</h2>
      <p className="govuk-body">
        Use the NOC query parameter to limit results to data published by an operator.
      </p>
      <p className="govuk-body">
        Download the data catalogue to see the relationship between operators and NOC values on
        this service.
      </p>
      <h2 className="govuk-heading-m">Getting data by location</h2>
      <p className="govuk-body">
        Use the bounding box query parameter for geographic filtering. For location data this
        returns vehicles within the area at that time; for static data, matching data sets are
        returned.
      </p>
      <p className="govuk-body">
        For query parameter details see the{' '}
        <Link className="govuk-link" href="?section=apireference">
          API reference
        </Link>
        .
      </p>
    </>
  );
}

