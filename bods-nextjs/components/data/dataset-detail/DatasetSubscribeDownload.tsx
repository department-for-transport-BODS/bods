/**
 * Source: transit_odp/browse/templates/browse/base/subscribe_and_download.html
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
  fileExtension: string;
}

export function DatasetSubscribeDownload({
  datasetId,
  datasetType,
  isSubscribed,
  fileExtension,
}: DatasetSubscribeDownloadProps) {
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
