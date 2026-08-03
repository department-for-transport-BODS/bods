/**
 * How to get help Section
 * Source: transit_odp/guidance/templates/guidance/bus_operators/help.html
 * 
 * This section includes content from multiple snippets:
 * - timetable_suppliers.html
 * - bus_location_suppliers.html
 * - fares_suppliers.html
 * - contact_details.html
 */

import Link from 'next/link';
import { SupportEmailLink } from './SupportEmailLink';

export function HelpSection() {
  return (
    <>
      <h2 data-qa="help-header" className="govuk-heading-l">How to get help</h2>

      <h3 className="govuk-heading-m">Timetables suppliers</h3>
      <p className="govuk-body">
        If you need help with timetables data, speak with your scheduling software
        supplier or Local Transport Authority.
      </p>

      <h3 className="govuk-heading-m">Bus location suppliers</h3>
      <p className="govuk-body">
        For bus location data support, contact your ETM or real-time system supplier.
      </p>

      <h3 className="govuk-heading-m">Fares suppliers</h3>
      <p className="govuk-body">
        For fares data support, speak with your ticketing system supplier.
      </p>

      <h3 className="govuk-heading-m">Contact the Bus Open Data Service</h3>
      <p className="govuk-body">
        For general enquiries and support, contact the Bus Open Data Service helpdesk:{' '}
        <SupportEmailLink />
      </p>
      <p className="govuk-body">
        You can also visit our{' '}
        <Link href="/contact" className="govuk-link">contact page</Link>{' '}
        for more information.
      </p>
    </>
  );
}


