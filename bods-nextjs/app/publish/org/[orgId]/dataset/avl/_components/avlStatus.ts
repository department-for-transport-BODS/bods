export function statusIndicatorClass(status?: string) {
  if (!status) {
    return 'status-indicator--draft';
  }

  if (status === 'live' || status === 'published') {
    return 'status-indicator--success';
  }

  if (status === 'error') {
    return 'status-indicator--error';
  }

  if (status === 'warning') {
    return 'status-indicator--warning';
  }

  if (status === 'indexing' || status === 'pending' || status === 'processing') {
    return 'status-indicator--indexing';
  }

  return 'status-indicator--draft';
}

export function statusLabel(status?: string) {
  if (!status) {
    return 'Draft';
  }

  if (status === 'live' || status === 'published') {
    return 'Published';
  }

  if (status === 'indexing' || status === 'pending' || status === 'processing') {
    return 'Processing';
  }

  if (status === 'success' || status === 'draft') {
    return 'Draft';
  }

  return status.charAt(0).toUpperCase() + status.slice(1);
}
