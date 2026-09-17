import Link from 'next/link';
import { wwwPath } from '@/config/client';

export function OverviewSection() {
  return (
    <>
      <h1 data-qa="overview-header" className="govuk-heading-l">Overview</h1>
      <p className="govuk-body">
        The Bus Open Data Service provides <b>timetables, bus location and fares data for local bus
        services across England.</b>
      </p>
      <p className="govuk-body">
        The Bus Services Act 2017 requires all operators of local bus services in England to
        provide this information. The transition period is from 2020-2021.
      </p>
      <p className="govuk-body govuk-!-padding-bottom-5">
        The Bus Open Data Service is freely available for anyone to use, providing a single
        location to discover and access data. As well as provide feedback to data publishers. You
        do not need a license to use the data.
      </p>
      <h2 className="govuk-heading-m">Road map</h2>
      <p className="govuk-body">
        Bus Open Data Service is currently in public beta testing stage. Please find the key
        dates for changes below. Please visit the{' '}
        <Link className="govuk-link" href={wwwPath('/changelog')}>
          Service changelog
        </Link>{' '}
        for more detailed updates.
      </p>
      <table className="govuk-table govuk-!-font-size-16">
        <thead className="govuk-table__head">
          <tr className="govuk-table__row">
            <th scope="col" className="govuk-table__header">Date</th>
            <th scope="col" className="govuk-table__header">Event</th>
          </tr>
        </thead>
        <tbody className="govuk-table__body">
          <tr className="govuk-table__row">
            <th className="govuk-table__header">31 December 2020</th>
            <td className="govuk-table__cell">Obligation to provide bus timetable data to the Bus Open Data Service.</td>
          </tr>
          <tr className="govuk-table__row">
            <th className="govuk-table__header">7 January 2021</th>
            <td className="govuk-table__cell">Obligation to provide vehicle location and basic fares and tickets data to the Bus Open Data Service.</td>
          </tr>
          <tr className="govuk-table__row">
            <th className="govuk-table__header">7 January 2023</th>
            <td className="govuk-table__cell">Obligation to provide complex fares and ticket data to the Bus Open Data Service.</td>
          </tr>
        </tbody>
      </table>
    </>
  );
}

