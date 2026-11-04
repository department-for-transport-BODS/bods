import { publishAppPath, wwwPath } from '@/config/client';

/**
 * "Need help with operator data requirements?" sidebar shared by the publish
 * timetable feed-detail and line-detail pages.
 *
 * Source: transit_odp/publish/templates/publish/dataset_detail/related_links.html
 */
export function OperatorRequirementsHelp() {
  return (
    <>
      <h2 className="govuk-heading-m">Need help with operator data requirements?</h2>
      <ul className="govuk-list app-list--nav govuk-!-font-size-19">
        <li>
          <a className="govuk-link" href={publishAppPath('/guidance/operator-requirements')}>
            View our guidelines here
          </a>
        </li>
        <li>
          <a className="govuk-link" href={wwwPath('/contact')}>
            Contact support desk
          </a>
        </li>
      </ul>
    </>
  );
}
