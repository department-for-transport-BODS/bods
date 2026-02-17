import Link from 'next/link';

export function OverviewSection() {
  return (
    <>
      <h1 className="govuk-heading-l">Overview</h1>
      <p className="govuk-body">
        The Bus Open Data Service provides <strong>timetables, bus location and fares data for
        local bus services across England.</strong>
      </p>
      <p className="govuk-body">
        The Bus Services Act 2017 requires operators of local bus services in England to provide
        this information.
      </p>
      <p className="govuk-body">
        The service is freely available for anyone to use and does not require a license to use
        the data.
      </p>
      <h2 className="govuk-heading-m">Road map</h2>
      <p className="govuk-body">
        BODS is in public beta. See the <Link className="govuk-link" href="/changelog">Service changelog</Link>{' '}
        for updates.
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
            <td className="govuk-table__cell">Obligation to provide bus timetable data.</td>
          </tr>
          <tr className="govuk-table__row">
            <th className="govuk-table__header">7 January 2021</th>
            <td className="govuk-table__cell">Obligation to provide vehicle location and basic fares data.</td>
          </tr>
          <tr className="govuk-table__row">
            <th className="govuk-table__header">7 January 2023</th>
            <td className="govuk-table__cell">Obligation to provide complex fares and ticket data.</td>
          </tr>
        </tbody>
      </table>
    </>
  );
}

