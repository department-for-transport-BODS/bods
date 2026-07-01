'use client';

import Link from 'next/link';
import { AvlFeedDetail } from './AvlFeedDetailContent';

interface AvlFeedDetailActionsProps {
  feedDetail: AvlFeedDetail;
  orgId: string;
  datasetId: string;
}

export function AvlFeedDetailActions({ feedDetail, orgId, datasetId }: AvlFeedDetailActionsProps) {
  // Don't show buttons if dummy or if status is inactive
  if (feedDetail.isDummy || feedDetail.status === 'inactive') {
    return null;
  }

  const updateUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}/update`;
  const deactivateUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}/archive`;

  return (
    <div className="btn-group-justified" style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
      <Link role="button" className="govuk-button" href={updateUrl}>
        Update data feed
      </Link>
      {feedDetail.status !== 'expired' && (
        <Link role="button" className="govuk-button govuk-button--secondary" href={deactivateUrl}>
          Deactivate data feed
        </Link>
      )}
    </div>
  );
}
