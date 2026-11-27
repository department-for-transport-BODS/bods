export function DataUpdatesTable() {
  return (
    <table className="govuk-table">
      <thead className="govuk-table__head">
        <tr className="govuk-table__row">
          <th scope="col" className="govuk-table__header">Data type</th>
          <th scope="col" className="govuk-table__header">Cache type</th>
          <th scope="col" className="govuk-table__header">Update rate</th>
        </tr>
      </thead>
      <tbody className="govuk-table__body">
        <tr className="govuk-table__row">
          <td className="govuk-table__cell">Timetables</td>
          <td className="govuk-table__cell">Static</td>
          <td className="govuk-table__cell">Updates every 24 hours around 06:00 GMT</td>
        </tr>
        <tr className="govuk-table__row">
          <td className="govuk-table__cell">Fares data</td>
          <td className="govuk-table__cell">Static</td>
          <td className="govuk-table__cell">Updates every 24 hours around 06:00 GMT</td>
        </tr>
        <tr className="govuk-table__row">
          <td className="govuk-table__cell">Bus location data</td>
          <td className="govuk-table__cell">Real time</td>
          <td className="govuk-table__cell">Every 10 seconds</td>
        </tr>
      </tbody>
    </table>
  );
}
