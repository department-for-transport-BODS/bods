import Link from 'next/link';
import { dataPath } from '@/config/client';

export function ApiReferenceSection() {
  return (
    <>
      <h1 className="govuk-heading-l">API reference</h1>
      <p className="govuk-body">
        Use the dedicated API docs for endpoint parameters, request formats and responses:
      </p>
      <ul className="govuk-list govuk-list--bullet">
        <li><Link className="govuk-link" href={dataPath('/timetables')}>Timetables API</Link></li>
        <li><Link className="govuk-link" href={dataPath('/avl')}>Bus location API</Link></li>
        <li><Link className="govuk-link" href={dataPath('/fares')}>Fares API</Link></li>
        <li><Link className="govuk-link" href={dataPath('/disruptions')}>Disruptions API</Link></li>
        <li><Link className="govuk-link" href={dataPath('/cancellations')}>Cancellations API</Link></li>
      </ul>
    </>
  );
}

