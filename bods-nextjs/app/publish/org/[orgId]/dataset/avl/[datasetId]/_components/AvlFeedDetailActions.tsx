import Link from 'next/link';
import type { AvlFeedDetail } from './AvlFeedDetailContent';
import { publishAppPath } from '@/config/client';

interface AvlFeedDetailActionsProps {
  feedDetail: AvlFeedDetail;
  orgId: string;
  datasetId: string;
}

export function AvlFeedDetailActions({ feedDetail, orgId, datasetId }: AvlFeedDetailActionsProps) {
  if (feedDetail.isDummy || feedDetail.status === 'inactive') {
    return null;
  }

  const updateUrl = publishAppPath(`/org/${orgId}/dataset/avl/${datasetId}/update/`);
  const deactivateUrl = publishAppPath(`/org/${orgId}/dataset/avl/${datasetId}/deactivate/`);

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
