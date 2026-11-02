/**
 * Service Changelog Page
 *
 * Source: transit_odp/changelog/templates/changelog/changelog.html
 */

import { connection } from 'next/server';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { HOSTS, dataPath, publishAppPath, wwwPath } from '@/config/client';
import { getKnownIssues } from '@/lib/changelog/known-issues';
import { getReleaseNotes } from '@/lib/changelog/release-notes';
import { KnownIssuesSection } from './_components/KnownIssuesSection';
import { ReleaseNotesSection } from './_components/ReleaseNotesSection';

export default async function ChangelogPage() {
  await connection();
  const [knownIssues, releaseNotes] = await Promise.all([getKnownIssues(), getReleaseNotes()]);

  return (
    <div className="govuk-width-container">
      <Breadcrumbs
        items={[
          { label: 'Bus Open Data Service', href: HOSTS.www },
          { label: 'Service Changelog', current: true },
        ]}
      />
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Service changelog</h1>
          </div>
          <div className="govuk-grid-column-one-third">
            <h2 className="govuk-heading-m">Need further guidance?</h2>
            <ul className="govuk-list app-list--nav govuk-!-font-size-19">
              <li>
                <a className="govuk-link" href={publishAppPath('/guidance/operator-requirements/')}>
                  View operator guidance
                </a>
              </li>
              <li>
                <a className="govuk-link" href={dataPath('/guidance/requirements/')}>
                  View developer guidance
                </a>
              </li>
              <li>
                <a className="govuk-link" href={wwwPath('/contact/')}>
                  Contact support desk
                </a>
              </li>
            </ul>
          </div>
        </div>
        <KnownIssuesSection knownIssues={knownIssues} />
        <hr className="govuk-section-break govuk-section-break--l govuk-section-break--visible" />
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-full">
            <h2 className="govuk-heading-l govuk-!-margin-bottom-5">Release notes</h2>
            <p className="govuk-body">Get involved in the work that is being done by the BODS team.</p>
            <ReleaseNotesSection releaseNotes={releaseNotes} />
          </div>
        </div>
      </div>
    </div>
  );
}
