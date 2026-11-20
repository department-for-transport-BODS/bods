import type { CatalogueField } from './dataCatalogueDefinitions';

// Mirrors guidance/snippets/datacatalogue_table.html; definitions may contain <br /> markup.
export function CatalogueDefinitionTable({ fields }: { fields: CatalogueField[] }) {
  return (
    <table data-qa="requirements-table" className="govuk-table govuk-!-margin-bottom-9">
      <thead data-qa="requirements-table-header" className="govuk-table__head">
        <tr className="govuk-table__row">
          <th scope="col" className="govuk-table__header">Field name</th>
          <th scope="col" className="govuk-table__header">Definition</th>
        </tr>
      </thead>
      <tbody className="govuk-table__body">
        {fields.map(({ field, definition }) => (
          <tr className="govuk-table__row" key={field}>
            <td className="govuk-table__cell">{field}</td>
            <td className="govuk-table__cell" dangerouslySetInnerHTML={{ __html: definition }} />
          </tr>
        ))}
      </tbody>
    </table>
  );
}
