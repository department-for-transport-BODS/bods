import Link from 'next/link';
import { config } from '@/config';

export function SupportSection() {
  return (
    <>
      <h1 className="govuk-heading-l">Timetables data support</h1>
      <p className="govuk-body">
        Local transport authorities may support operators by sending them the digitised
        TranXChange files made from their paper registration. The operator can then publish it on
        the service.
      </p>
      <p className="govuk-body">
        A number of smaller bus operators may wish to post bus information to you, as many are
        currently doing whilst registering a service. You may offer to send these files to
        operators or support them in producing their TransXChange files for the service.
      </p>
      <p className="govuk-body">
        Methods of producing TransXChange 2.4 include procuring scheduling software or using the
        free TxC 2.4 tool provided by DfT, from the following website:
      </p>
      <p className="govuk-body">
        <a className="govuk-link" href="https://www.gov.uk/guidance/publish-bus-open-data" target="_blank" rel="noopener noreferrer">
          https://www.gov.uk/guidance/publish-bus-open-data
        </a>
      </p>
      <p className="govuk-body">
        If you require additional support, DfT can support the creation of TxC using the tool.
        For more information please contact{' '}
        <a className="govuk-link" href={`mailto:${config.supportEmail}`}>{config.supportEmail}</a>.
      </p>
      <p className="govuk-body">Please ensure the timetables data provided aligns with TransXChange version 2.4.</p>

      <h2 className="govuk-heading-l">Bus location data support</h2>
      <p className="govuk-body">
        A limited number of operators still do not have ETMs that can provide SIRI-VM data
        which aligns with the Department for Transport SIRI-VM Profile. This also enables
        crowding information to be provided to the service.
      </p>
      <p className="govuk-body">
        Please ensure ETM suppliers procured can provide bus location data in feeds that align
        with the standards documented in the{' '}
        <Link className="govuk-link" href="/guidance/support/bus-operators">
          operator requirements
        </Link>
        . Once a supplier has been procured, operators may require support getting set up.
      </p>

      <h2 className="govuk-heading-l">Fares data support</h2>
      <p className="govuk-body">
        Operators who have ETM suppliers can talk with them about hosted NeTEx solutions. A
        large proportion of fares data already resides within ETM systems. This can be leveraged
        to provide NeTEx to BODS. There may be a need for additional product development, so
        ensure your needs are understood by your supplier.
      </p>
      <p className="govuk-body">
        Alternatively, you can support operators using the free Fare Data Build Tool to produce
        NeTEx which can be found here:
      </p>
      <p className="govuk-body">
        <a className="govuk-link" href="https://fares-data.dft.gov.uk/" target="_blank" rel="noopener noreferrer">
          https://fares-data.dft.gov.uk/
        </a>
      </p>
      <p className="govuk-body">
        Please ensure fares data provided aligns to the standards in the{' '}
        <Link className="govuk-link" href="/guidance/support/bus-operators">
          operator requirements
        </Link>
        .
      </p>
    </>
  );
}

