/**
 * Version Page
 * 
 * Displays the current version of the application
 */

import { clientConfig } from '@/config/client';

export default function VersionPage() {
  const version = clientConfig.appVersion;

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Version</h1>
            <p className="govuk-body">
              Current version: <strong>{version}</strong>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

