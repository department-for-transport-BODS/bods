export function RequirementsTable() {
  return (
    <table className="govuk-table">
      <thead className="govuk-table__head">
        <tr className="govuk-table__row">
          <th scope="col" className="govuk-table__header">Data required</th>
          <th scope="col" className="govuk-table__header">Data format required</th>
          <th scope="col" className="govuk-table__header">Requirement date</th>
          <th scope="col" className="govuk-table__header">Obligation</th>
        </tr>
      </thead>
      <tbody className="govuk-table__body">
        <tr className="govuk-table__row">
          <td className="govuk-table__cell">Timetable</td>
          <td className="govuk-table__cell">TransXChange Version 2.4</td>
          <td className="govuk-table__cell">31st December 2020</td>
          <td className="govuk-table__cell">Operator</td>
        </tr>
        <tr className="govuk-table__row">
          <td className="govuk-table__cell">Bus location</td>
          <td className="govuk-table__cell">SIRI-VM Version 2.0</td>
          <td className="govuk-table__cell">7th January 2021</td>
          <td className="govuk-table__cell">Operator</td>
        </tr>
        <tr className="govuk-table__row">
          <td className="govuk-table__cell">Basic fares</td>
          <td className="govuk-table__cell">UK NeTEx 1.10</td>
          <td className="govuk-table__cell">7th January 2021</td>
          <td className="govuk-table__cell">Operator</td>
        </tr>
        <tr className="govuk-table__row">
          <td className="govuk-table__cell">Complex fares</td>
          <td className="govuk-table__cell">UK NeTEx 1.10</td>
          <td className="govuk-table__cell">7th January 2023</td>
          <td className="govuk-table__cell">Operator</td>
        </tr>
        <tr className="govuk-table__row">
          <td className="govuk-table__cell">Stop data</td>
          <td className="govuk-table__cell">NaPTAN</td>
          <td className="govuk-table__cell">31st December 2020</td>
          <td className="govuk-table__cell">Local Transport Authority</td>
        </tr>
      </tbody>
    </table>
  );
}

