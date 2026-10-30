'use client';

import { DownloadPage } from '@/components/data/bulk-download/DownloadPage';
import { BULK_DOWNLOAD_UNAVAILABLE } from '@/components/data/bulk-download/constants';
import { GtfsRtHelp, SiriVmHelp } from '@/components/data/bulk-download/help-modals';
import { dataPath } from '@/config/client';

/**
 * Source: transit_odp/browse/templates/browse/avl/download_avl.html
 * View: transit_odp/browse/views/avl_views.py - DownloadAVLView
 * Data: transit_odp/browse/views/download_api.py - get_download_avl_api
 */

interface AvlDownloadData {
  showBulkArchiveUrl: boolean;
}

export function AvlDownloadContent() {
  return (
    <DownloadPage<AvlDownloadData>
      title="All location data"
      breadcrumb={{ label: 'All Location Data', path: '/avl/download/' }}
      endpoint="/api/browser/downloads/avl/"
      withTrailingRow
    >
      {({ showBulkArchiveUrl }) => (
        <>
          <h3 className="govuk-heading-l">Download file</h3>
          <p className="govuk-body">
            Download a snapshot of all live bus locations at a point in time.
          </p>
          <ul className="govuk-list govuk-!-margin-bottom-3">
            <li>
              <b>Format:</b> SIRI-VM <SiriVmHelp /> GTFS-RT <GtfsRtHelp />
            </li>
            <li>
              <b>Mode:</b> Bus
            </li>
            <li>
              <b>File type:</b> ZIP file
            </li>
            <li>
              <b>Update frequency:</b> Every 10 seconds
            </li>
          </ul>
          <ul className="govuk-list">
            <li>
              {showBulkArchiveUrl ? (
                <a className="govuk-link" href={dataPath('/avl/download/bulk_archive')}>
                  Download all bus location data in SIRI-VM format
                </a>
              ) : (
                BULK_DOWNLOAD_UNAVAILABLE
              )}
            </li>
            <li>
              {showBulkArchiveUrl ? (
                <a className="govuk-link" href={dataPath('/avl/download/gtfsrt')}>
                  Download all bus location data in GTFS RT format
                </a>
              ) : (
                BULK_DOWNLOAD_UNAVAILABLE
              )}
            </li>
            <li>
              {showBulkArchiveUrl ? (
                <a className="govuk-link" href={dataPath('/avl/download/sirivm_tfl')}>
                  Download all bus location data from Transport for London (TfL) only in SIRI-VM
                  format
                </a>
              ) : (
                BULK_DOWNLOAD_UNAVAILABLE
              )}
            </li>
          </ul>
        </>
      )}
    </DownloadPage>
  );
}
