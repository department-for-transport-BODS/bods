import Link from 'next/link';

export function AgentSection() {
  return (
    <>
      <h1 className="govuk-heading-l">Being an Agent</h1>
      <p className="govuk-body">
        Agents agreeing to publish data must provide and maintain it as prescribed in the{' '}
        <Link className="govuk-link" href="/guidance/support/bus-operators">
          operator requirements
        </Link>
        . Local transport authorities may wish to provide agency services as a bureau service
        for multiple operators.
      </p>
      <p className="govuk-body">
        Find out more information about being an{' '}
        <Link className="govuk-link" href="/guidance/support/bus-operators?section=agents">
          agent
        </Link>
        .
      </p>
    </>
  );
}

