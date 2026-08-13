import Link from 'next/link';
import { publishAppPath } from '@/config/client';

export function AgentSection() {
  return (
    <>
      <h1 className="govuk-heading-l">Being an Agent</h1>
      <p className="govuk-body">
        Agents agreeing to publish data must provide and maintain it as prescribed in the{' '}
        <Link className="govuk-link" href={publishAppPath('/guidance/operator-requirements?section=agents')}>
          operator requirements
        </Link>
        . Local transport authorities may wish to provide agency services as a bureau service
        for multiple operators.
      </p>
      <p className="govuk-body">
        Find out more information about being an{' '}
        <Link className="govuk-link" href={publishAppPath('/guidance/operator-requirements')}>
          agent
        </Link>
        .
      </p>
    </>
  );
}

