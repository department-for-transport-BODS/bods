import Link from 'next/link';
import { dataPath, wwwPath } from '@/config/client';

export function DataHelpSidebar() {
  return (
    <div className="govuk-grid-column-one-third">
      <h2 className="govuk-heading-m">Need further help?</h2>
      <ul className="govuk-list">
        <li className="govuk-!-margin-bottom-3">
          <Link className="govuk-link" href={dataPath('/guide-me')}>
            Guide me
          </Link>
        </li>
        <li className="govuk-!-margin-bottom-3">
          <Link className="govuk-link" href={wwwPath('/changelog')}>
            Service changelog
          </Link>
        </li>
        <li className="govuk-!-margin-bottom-3">
          <Link className="govuk-link" href={wwwPath('/contact')}>
            Contact us for technical issues
          </Link>
        </li>
      </ul>
    </div>
  );
}
