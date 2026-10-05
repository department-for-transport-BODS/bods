export type ObservationExtraInfo = { code: string; description: string }[];

export type ObservationDefinition = {
  title: string;
  level: string;
  text: string;
  impacts: string | null;
  resolve: string | null;
  preamble: string | null;
  isActive: boolean;
  extraInfo: ObservationExtraInfo;
};

export function ExtraInfoTable({ extraInfo }: { extraInfo: ObservationExtraInfo }) {
  return (
    <table className="govuk-table">
      <tbody className="govuk-table__body">
        {extraInfo.map((item) => (
          <tr className="govuk-table__row" key={item.code}>
            <td className="govuk-table__cell govuk-!-font-weight-bold">{item.code}</td>
            <td className="govuk-table__cell">{item.description}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
