/**
 * Source: transit_odp/browse/templates/browse/base/subscribe_and_download.html
 *         (timetables, fares) and browse/avl/feed_detail/subscribe_and_download.html
 *         (AVL: subscribe only, worded for a data feed)
 *
 * Both links go to Django's own pages (subscription sub-page, download URL).
 */

import Link from 'next/link';
import type { DatasetType } from '@/types';
import { datasetSubpagePath } from '@/lib/dataset-paths';

interface DatasetSubscribeDownloadProps {
  datasetId: number;
  datasetType: DatasetType;
  isSubscribed: boolean;
  /** Not used by AVL, which has no download link */
  fileExtension?: string;
}

export function DatasetSubscribeDownload({
  datasetId,
  datasetType,
  isSubscribed,
  fileExtension,
}: DatasetSubscribeDownloadProps) {
  if (datasetType === 'AVL') {
    return (
      <>
        <h2 className="govuk-heading-m govuk-!-margin-top-5">Subscribe</h2>
        <ul className="govuk-list app-list--nav govuk-!-font-size-19">
          <li>
            <Link className="govuk-link" href={datasetSubpagePath(datasetType, datasetId, 'subscription')}>
              {isSubscribed ? 'Unsubscribe from this data feed' : 'Subscribe to this data feed'}
            </Link>
          </li>
        </ul>
      </>
    );
  }

  return (
    <>
      <h2 className="govuk-heading-m govuk-!-margin-top-5">Subscribe, download the data</h2>
      <ul className="govuk-list app-list--nav govuk-!-font-size-19">
        <li>
          <Link className="govuk-link" href={datasetSubpagePath(datasetType, datasetId, 'subscription')}>
            {isSubscribed ? 'Unsubscribe from this data set' : 'Subscribe to this data set'}
          </Link>
        </li>
        <li>
          <a className="govuk-link" href={datasetSubpagePath(datasetType, datasetId, 'download')}>
            Download dataset (.{fileExtension})
          </a>
        </li>
      </ul>
    </>
  );
}
