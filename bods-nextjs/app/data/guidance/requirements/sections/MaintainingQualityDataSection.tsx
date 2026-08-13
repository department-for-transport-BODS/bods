import Link from 'next/link';
import { publishAppPath } from '@/config/client';

export function MaintainingQualityDataSection() {
  return (
    <>
      <h1 className="govuk-heading-l">Maintaining quality data</h1>
      <p className="govuk-body">
        Use data quality reports and validation feedback to monitor and improve dataset health
        over time.
      </p>
      <p className="govuk-body">
        <Link className="govuk-link" href={publishAppPath('/guidance/operator-requirements?section=dataquality')}>
          Read data quality guidance
        </Link>
        .
      </p>
    </>
  );
}

