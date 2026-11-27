export type AvlStatus =
  | 'live'
  | 'published'
  | 'success'
  | 'draft'
  | 'inactive'
  | 'expired'
  | 'archived'
  | 'indexing'
  | 'pending'
  | 'processing'
  | 'error'
  | 'warning';

interface StatusMeta {
  label: string;
  indicator: string;
}

const DEFAULT_STATUS_META: StatusMeta = {
  label: 'Draft',
  indicator: 'status-indicator--draft',
};

const STATUS_META: Record<AvlStatus, StatusMeta> = {
  live: { label: 'Published', indicator: 'status-indicator--success' },
  published: { label: 'Published', indicator: 'status-indicator--success' },
  success: { label: 'Draft', indicator: 'status-indicator--draft' },
  draft: { label: 'Draft', indicator: 'status-indicator--draft' },
  inactive: { label: 'Inactive', indicator: 'status-indicator--inactive' },
  expired: { label: 'Inactive', indicator: 'status-indicator--inactive' },
  archived: { label: 'Inactive', indicator: 'status-indicator--inactive' },
  indexing: { label: 'Processing', indicator: 'status-indicator--indexing' },
  pending: { label: 'Processing', indicator: 'status-indicator--indexing' },
  processing: { label: 'Processing', indicator: 'status-indicator--indexing' },
  error: { label: 'Error', indicator: 'status-indicator--error' },
  warning: { label: 'Warning', indicator: 'status-indicator--warning' },
};

function getStatusMeta(status?: string): StatusMeta {
  if (!status) {
    return DEFAULT_STATUS_META;
  }

  return STATUS_META[status as AvlStatus] ?? DEFAULT_STATUS_META;
}

export function statusIndicatorClass(status?: string) {
  return getStatusMeta(status).indicator;
}

export function statusLabel(status?: string) {
  return getStatusMeta(status).label;
}
