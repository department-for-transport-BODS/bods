import Link from 'next/link';

export function MaintainingQualityDataSection() {
  return (
    <>
      <h1 className="govuk-heading-l">Maintaining quality data</h1>
      <p className="govuk-body">
        Use data quality reports and validation feedback to monitor and improve dataset health
        over time.
      </p>
      <p className="govuk-body">
        <Link className="govuk-link" href="/guidance/support/bus-operators?section=dataquality">
          Read data quality guidance
        </Link>
        .
      </p>
    </>
  );
}

