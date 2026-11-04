'use client';

import { DownloadPage } from '@/components/data/bulk-download/DownloadPage';
import { BULK_DOWNLOAD_UNAVAILABLE } from '@/components/data/bulk-download/constants';
import { dataPath } from '@/config/client';

/**
 * Source: transit_odp/browse/templates/browse/timetables/download_timetables.html
 * View: transit_odp/browse/views/timetable_views.py - DownloadTimetablesView
 * Data: transit_odp/browse/views/download_api.py - get_download_timetables_api
 */

interface TimetableDownloadData {
  showBulkArchiveUrl: boolean;
  regions: { regionCode: string; name: string; exists: boolean }[];
  changeArchives: { publishedAt: string; label: string }[];
  isNewGtfsApiActive: boolean;
  gtfsFiles: { id: string; name: string }[];
}

const TNDS_URL =
  'https://data.gov.uk/dataset/0447f8d9-8f1b-4a68-bbc8-246981d02256/traveline-national-dataset';

export function TimetableDownloadContent() {
  return (
    <DownloadPage<TimetableDownloadData>
      title="All timetables data"
      breadcrumb={{ label: 'All Timetables Data', path: '/timetable/download/' }}
      endpoint="/api/browser/downloads/timetables/"
    >
      {({ showBulkArchiveUrl, regions, changeArchives, gtfsFiles }) => (
        <>
          <div className="govuk-!-margin-top-0">
            <h3 className="govuk-heading-m">Download file in TransXChange format</h3>
            <p className="govuk-body">
              You can download all the active timetables data cached on the service as of today by
              clicking the link below. Timetables data is provided in a TransXChange format within a
              compressed ZIP file.
            </p>
            <ul className="govuk-list app-list--nav govuk-!-font-size-19">
              {showBulkArchiveUrl ? (
                <li>
                  <a
                    className="govuk-link"
                    href={dataPath('/timetable/download/bulk_archive')}
                  >
                    All - Download timetables data in TransXChange format
                  </a>
                </li>
              ) : (
                BULK_DOWNLOAD_UNAVAILABLE
              )}
              {regions
                .filter((region) => region.exists && region.regionCode !== 'ALL')
                .map((region) => (
                  <li key={region.regionCode}>
                    <a
                      className="govuk-link"
                      href={dataPath(
                        `/timetable/download/bulk_archive/${encodeURIComponent(region.regionCode)}`,
                      )}
                    >
                      {region.name} - Download timetables data in TransXChange format
                    </a>
                  </li>
                ))}
            </ul>
          </div>

          <div className="govuk-!-margin-top-8">
            <h3 className="govuk-heading-m">Download data set updates in TransXChange format</h3>
            <p className="govuk-body">
              The following links enable you to download the last 7 days of data at specific
              intervals.
            </p>
            {changeArchives.length > 0 ? (
              <ul className="govuk-list download-list">
                {changeArchives.map((archive) => (
                  <li key={archive.publishedAt}>
                    <a
                      className="govuk-link"
                      href={dataPath(`/timetable/download/change_archive/${archive.publishedAt}/`)}
                    >
                      All data set updates from {archive.label} 00:00:00 - 23:59:59
                    </a>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="govuk-body">
                There have been no updates in the last 7 days. Please check back later.
              </p>
            )}
          </div>

          <div className="govuk-!-margin-top-8">
            <h3 className="govuk-heading-m">
              Download regional and national data sets in GTFS format
            </h3>
            <p className="govuk-body">
              You can download timetables data in GTFS format for the whole of GB, or filter for
              specific regions. This dataset is created using compliant data published to the Bus
              Open Data Service. Where data is not yet published on Bus Open Data, or is published
              but not compliant, this data is supplemented with{' '}
              <a
                className="govuk-link"
                rel="noopener noreferrer"
                href={TNDS_URL}
                target="_blank"
              >
                Traveline National Dataset (TNDS)
              </a>
              .
            </p>
            {gtfsFiles.length > 0 ? (
              <ul className="govuk-list download-list">
                {gtfsFiles.map((file) => (
                  <li key={file.id}>
                    <a
                      className="govuk-link"
                      href={dataPath(
                        `/timetable/download/gtfs-file/${encodeURIComponent(file.id)}/`,
                      )}
                    >
                      {file.name} - Download timetables data in GTFS format
                    </a>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="govuk-body">
                There are no GTFS files currently available. Please check back later.
              </p>
            )}
          </div>
        </>
      )}
    </DownloadPage>
  );
}
