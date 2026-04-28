/**
 * Formats an ISO date string as a UK-locale date, e.g. "5 April 2026".
 * Returns "-" when the value is missing or cannot be parsed.
 */
export const formatDate = (value?: string | null): string => {
  if (!value) {
    return '-';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '-';
  }

  return new Intl.DateTimeFormat('en-GB', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(date);
};

/**
 * Formats an ISO date string as a UK-locale date and time, e.g. "5 Apr 2026, 14:32".
 * Returns "-" when the value is missing or cannot be parsed.
 */
export const formatDateTime = (value?: string | null): string => {
  if (!value) {
    return '-';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '-';
  }

  return new Intl.DateTimeFormat('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date);
};
