'use client';

import { DownloadPage } from '@/components/data/bulk-download/DownloadPage';

/**
 * Source: transit_odp/common/templates/common/coach_download.html
 * View: transit_odp/common/views.py - CoachDownloadView (public, no login)
 * Data: transit_odp/browse/views/download_api.py - get_download_coach_api
 */

interface CoachDownloadData {
  txcFile: string;
  atcoFile: string;
}

export function CoachDownloadContent() {
  return (
    <DownloadPage<CoachDownloadData>
      title="All coach data"
      breadcrumb={{ label: 'All Coach Data', path: '/coach/download' }}
      endpoint="/api/browser/downloads/coach/"
    >
      {({ txcFile, atcoFile }) => (
        <div className="govuk-!-margin-top-0">
          <h3 className="govuk-heading-m">
            Download regional and national coach data sets in TxC2.4 PTI and ATCO-CIF format
          </h3>
          <p className="govuk-body">
            You can download coach data in TxC2.4 PTI or ATCO-CIF format for the whole of GB. This
            dataset is created using transformed data from coach operators. The data provided is PTI
            compliant.
          </p>
          <ul className="govuk-list app-list--nav govuk-!-font-size-19">
            <li>
              <a className="govuk-link" href={txcFile}>
                All - Download coach data in TransXchange2.4 PTI
              </a>
            </li>
            <li>
              <a className="govuk-link" href={atcoFile}>
                All - Download coach data in ATCO-CIF
              </a>
            </li>
          </ul>
        </div>
      )}
    </DownloadPage>
  );
}
