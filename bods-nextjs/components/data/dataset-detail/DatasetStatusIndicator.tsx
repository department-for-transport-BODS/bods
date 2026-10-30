/**
 * Source: transit_odp/organisation/templates/organisation/snippets/status_indicator.html
 *
 * Public detail pages can only show live / inactive datasets, but the full set
 * of Django branches is kept so the AVL / fares pages can reuse this. Draft
 * revision links ("View") are publish-side only and are not rendered here.
 */

import type { DatasetType } from '@/types';

interface DatasetStatusIndicatorProps {
  status: string;
  datasetType?: DatasetType;
}

export function DatasetStatusIndicator({ status, datasetType }: DatasetStatusIndicatorProps) {
  switch (status) {
    case 'live':
      return <span className="status-indicator status-indicator--success">Published</span>;
    case 'indexing':
    case 'pending':
      return (
        <div className="progress-centre">
          <div className="pie-progress">
            <span className="progress-percent" />
            <span className="progress-text">Processing</span>
          </div>
        </div>
      );
    case 'warning':
      return <span className="status-indicator status-indicator--warning">Warning</span>;
    case 'expiring':
      return <span className="status-indicator status-indicator--warning">Soon to expire</span>;
    case 'error':
      return datasetType === 'AVL' ? (
        <span className="status-indicator status-indicator--success">Published</span>
      ) : (
        <span className="status-indicator status-indicator--error">Error</span>
      );
    case 'draft':
    case 'success':
      return <span className="status-indicator status-indicator--draft">Draft</span>;
    case 'expired':
      return <span className="status-indicator status-indicator--inactive">Expired</span>;
    case 'inactive':
      return <span className="status-indicator status-indicator--inactive">Inactive</span>;
    case 'deleted':
      return <span className="status-indicator status-indicator--error">Deleted</span>;
    default:
      return <span>{status}</span>;
  }
}
