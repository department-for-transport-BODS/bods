'use client';

import { DownloadPage } from '@/components/data/bulk-download/DownloadPage';
import { BULK_DOWNLOAD_UNAVAILABLE } from '@/components/data/bulk-download/constants';
import { NetexHelp } from '@/components/data/bulk-download/help-modals';
import { dataPath } from '@/config/client';

/**
 * Source: transit_odp/browse/templates/browse/fares/download_fares.html
 * View: transit_odp/browse/views/fares_views.py - DownloadFaresView
 * Data: transit_odp/browse/views/download_api.py - get_download_fares_api
 */

interface FaresDownloadData {
  showBulkArchiveUrl: boolean;
}

export function FaresDownloadContent() {
  return (
    <DownloadPage<FaresDownloadData>
      title="All fares data"
      breadcrumb={{ label: 'All Fares Data', path: '/fares/download/' }}
      endpoint="/api/browser/downloads/fares/"
      withTrailingRow
    >
      {({ showBulkArchiveUrl }) => (
        <>
          <h3 className="govuk-heading-l">Download file</h3>
          <p className="govuk-body">
            You can download all the active fares data cached on the service as of today by clicking
            the link below. Fares data is provided in a NeTEx format within a compressed ZIP file.
          </p>
          <ul className="govuk-list">
            <li>
              <b>Format :</b> NeTEx <NetexHelp />
            </li>
            <li>
              <b>Mode :</b> Bus
            </li>
            <li>
              <b>File type :</b> ZIP file
            </li>
            <li>
              <b>Update frequency :</b> Daily around 6:00 am GMT
            </li>
          </ul>
          <p className="govuk-body govuk-!-margin-bottom-0">
            {showBulkArchiveUrl ? (
              <a className="govuk-link" href={dataPath('/fares/download/bulk_archive')}>
                Download all fares data
              </a>
            ) : (
              BULK_DOWNLOAD_UNAVAILABLE
            )}
          </p>
        </>
      )}
    </DownloadPage>
  );
}
