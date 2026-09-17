import { publishAppPath, TRANSXCHANGE_VERSION, wwwPath } from '@/config/client';

export function TimetableHelpAside() {
  const supportBusOperatorsUrl = publishAppPath('/guidance/operator-requirements');
  const contactSupportUrl = wwwPath('/contact');
  const txcSchemaVersion = TRANSXCHANGE_VERSION.split('.').slice(0, 2).join('.');

  return (
    <div className="govuk-grid-column-one-third">
      <h2 className="govuk-heading-m">Need help with operator data requirements?</h2>
      <ul className="govuk-list app-list--nav govuk-!-font-size-19">
        <li>
          <a className="govuk-link" target="_blank" rel="noopener noreferrer" href={`${supportBusOperatorsUrl}?section=dataquality`}>
            View the Txc {txcSchemaVersion} schema and profile requirement
          </a>
        </li>
        <li>
          <a className="govuk-link" target="_blank" rel="noopener noreferrer" href={supportBusOperatorsUrl}>
            View our guidelines here
          </a>
        </li>
        <li>
          <a className="govuk-link" target="_blank" rel="noopener noreferrer" href={contactSupportUrl}>
            Contact support desk
          </a>
        </li>
      </ul>
    </div>
  );
}