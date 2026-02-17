import { SUPPORT_EMAIL } from '@/lib/config';
import { HelpSectionTables } from './HelpSectionTables';

export function HelpSection() {
  return (
    <>
      <h1 className="govuk-heading-l">How to get help</h1>
      <h2 className="govuk-heading-l">NaPTAN stop data support</h2>
      <p className="govuk-body">
        The DfT is offering a free service whereby local authorities can get in contact with{' '}
        <a className="govuk-link" href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a> to request
        a spreadsheet that contains potential NaPTAN corrections for the areas that you are
        responsible for.
      </p>
      <HelpSectionTables />
      <p className="govuk-body">
        Contact <a className="govuk-link" href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a>{' '}
        for:
      </p>
      <ul className="govuk-list govuk-list--bullet">
        <li>Request TxC tool support or creation from DfT</li>
        <li>Support using the Fare Data Build tool</li>
        <li>Technical and publishing issues on BODS</li>
        <li>Create an operator account</li>
        <li>Enquiries about the Bus Open Data Program</li>
        <li>Feedback on the service</li>
      </ul>
    </>
  );
}

