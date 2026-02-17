import Link from 'next/link';

export function LocalAuthorityBusesSection() {
  return (
    <>
      <h1 className="govuk-heading-l">Providing data for Local Authority operated buses</h1>
      <p className="govuk-body">
        Bus operators owned or managed by Local Authorities must comply with the new legal
        requirements to publish open data - please see our{' '}
        <Link className="govuk-link" href="/guidance/support/bus-operators">
          operator requirements
        </Link>
        .
      </p>
    </>
  );
}

