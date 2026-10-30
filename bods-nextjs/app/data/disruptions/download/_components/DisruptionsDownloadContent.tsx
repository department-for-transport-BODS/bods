'use client';

import { DownloadPage } from '@/components/data/bulk-download/DownloadPage';
import { BULK_DOWNLOAD_UNAVAILABLE } from '@/components/data/bulk-download/constants';
import { GtfsRtHelp, SiriSxHelp } from '@/components/data/bulk-download/help-modals';
import { dataPath } from '@/config/client';

/**
 * Source: transit_odp/browse/templates/browse/disruptions/download_disruptions.html
 * View: transit_odp/browse/views/disruptions_views.py - DownloadDisruptionsView
 * Data: transit_odp/browse/views/download_api.py - get_download_disruptions_api
 */

interface DisruptionsDownloadData {
  showBulkArchiveUrl: boolean;
  isGtfsServiceAlertsLive: boolean;
}

export function DisruptionsDownloadContent() {
  return (
    <DownloadPage<DisruptionsDownloadData>
      title="All disruption data"
      breadcrumb={{ label: 'All Disruption Data', path: '/disruptions/download/' }}
      endpoint="/api/browser/downloads/disruptions/"
      withTrailingRow
    >
      {({ showBulkArchiveUrl, isGtfsServiceAlertsLive }) => (
        <>
          <h3 className="govuk-heading-l">Download file</h3>
          <p className="govuk-body">
            Download a snapshot of all live and upcoming disruptions within England
          </p>
          <ul className="govuk-list">
            <li>
              <b>Format :</b> SIRI-SX <SiriSxHelp />
              {isGtfsServiceAlertsLive && (
                <>
                  {' '}
                  GTFS-RT <GtfsRtHelp />
                </>
              )}
            </li>
            <li>
              <b>Mode :</b> Bus, Ferry, Light Rail
            </li>
            <li>
              <b>File type :</b> ZIP file
            </li>
            <li>
              <b>Update frequency :</b> Every minute
            </li>
            <li>
              <b>Source :</b> Local authorities
            </li>
          </ul>
          {showBulkArchiveUrl ? (
            <ul className="govuk-list">
              <li>
                <a className="govuk-link" href={dataPath('/disruptions/download/bulk_archive')}>
                  Download all disruption data in SIRI-SX format
                </a>
              </li>
              {isGtfsServiceAlertsLive && (
                <li>
                  <a
                    className="govuk-link"
                    href={dataPath('/disruptions/download/gtfsrt_service_alerts')}
                  >
                    Download all disruption data in GTFS-RT format
                  </a>
                </li>
              )}
            </ul>
          ) : (
            <p className="govuk-body govuk-!-margin-bottom-0">{BULK_DOWNLOAD_UNAVAILABLE}</p>
          )}
        </>
      )}
    </DownloadPage>
  );
}
