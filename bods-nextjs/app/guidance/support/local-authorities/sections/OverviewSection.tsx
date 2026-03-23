import Link from 'next/link';
import { RequirementsTable } from './RequirementsTable';

export function OverviewSection() {
  return (
    <>
      <h1 className="govuk-heading-l">Overview</h1>
      <p className="govuk-body">
        The Bus Open Data Service (BODS) is the central service for publishing high quality
        information for all local bus services in England. The Bus Services Act 2017 requires
        operators of local bus services in England to publish data to the Bus Open Data Service.
        There are three types of data that operators must published in certain data formats:
        timetables, bus location and fares.
      </p>
      <p className="govuk-body">
        Local transport authorities are required to maintain NaPTAN stop data and should enable
        operators to publish data to this service to fulfil the{' '}
        <Link className="govuk-link" href="/guidance/support/bus-operators">
          operator requirements
        </Link>
        . Local transport authorities should be{' '}
        <Link className="govuk-link" href="?section=support">supporting operators</Link> and may
        also act as an operator's{' '}
        <Link className="govuk-link" href="?section=agent">agent</Link>.
      </p>
      <RequirementsTable />
      <p className="govuk-body">
        Community bus operators are currently outside the scope of the requirement if they have
        exemptions under Section 19 or Section 22 of the Local Government Act 1985.
      </p>
    </>
  );
}

