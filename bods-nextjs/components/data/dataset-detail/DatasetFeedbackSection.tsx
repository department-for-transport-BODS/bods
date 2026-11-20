/**
 * Source: transit_odp/browse/templates/browse/base/feedback.html
 * (the plain, non service-specific variant used by the dataset detail page).
 * Callers hide it when the `is_specific_feedback` flag is on.
 */

import Link from 'next/link';
import type { DatasetType } from '@/types';
import { datasetSubpagePath } from '@/lib/dataset-paths';

interface DatasetFeedbackSectionProps {
  datasetId: number;
  datasetType: DatasetType;
}

export function DatasetFeedbackSection({ datasetId, datasetType }: DatasetFeedbackSectionProps) {
  const isAvl = datasetType === 'AVL';

  return (
    <>
      <h2 className="govuk-heading-m">
        {isAvl ? 'Noticed issues with this data feed?' : 'Noticed issues with this data set?'}
      </h2>
      <Link
        className="govuk-link govuk-!-font-size-19"
        href={datasetSubpagePath(datasetType, datasetId, 'feedback')}
      >
        {isAvl ? 'Contact data feed owner directly' : 'Contact data set owner directly'}
      </Link>
    </>
  );
}
