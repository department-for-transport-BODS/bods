export interface FeedStatusIndicator {
  className: string;
  label: string;
}

/**
 * Mirrors organisation/snippets/status_indicator.html for a feed-detail page
 * (no `record`/`dataset_type` in context, so the draft-revision links do not apply).
 */
export function timetableFeedStatusIndicator(status: string): FeedStatusIndicator {
  switch (status) {
    case 'live':
      return { className: 'status-indicator--success', label: 'Published' };
    case 'indexing':
    case 'pending':
      return { className: 'status-indicator--indexing', label: 'Processing' };
    case 'warning':
      return { className: 'status-indicator--warning', label: 'Warning' };
    case 'expiring':
      return { className: 'status-indicator--warning', label: 'Soon to expire' };
    case 'error':
      return { className: 'status-indicator--error', label: 'Error' };
    case 'draft':
    case 'success':
      return { className: 'status-indicator--draft', label: 'Draft' };
    case 'expired':
      return { className: 'status-indicator--inactive', label: 'Expired' };
    case 'inactive':
      return { className: 'status-indicator--inactive', label: 'Inactive' };
    case 'deleted':
      return { className: 'status-indicator--error', label: 'Deleted' };
    default:
      return { className: '', label: status };
  }
}
