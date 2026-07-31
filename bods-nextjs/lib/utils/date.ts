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
 * Formats an ISO date string as a UK-locale date and time, e.g. "5 Apr 2026 14:32".
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

  const datePart = new Intl.DateTimeFormat('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(date);

  const timePart = new Intl.DateTimeFormat('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date);

  return `${datePart} ${timePart}`;
};

/**
 * Formats an ISO date string to the following date and time style, used on the AVL feeds list page:
 * e.g. "July 10, 2026, 10:53 a.m.".
 * Returns "-" when the value is missing or cannot be parsed.
 */
export const formatDateTimeFeedsList = (value?: string | null): string => {
  if (!value) {
    return '-';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '-';
  }

  const datePart = new Intl.DateTimeFormat('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  }).format(date);

  const timePart = new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  })
    .format(date)
    .replace(/AM$/, 'a.m.')
    .replace(/PM$/, 'p.m.');

  return `${datePart}, ${timePart}`;
};
