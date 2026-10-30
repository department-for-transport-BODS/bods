/**
 * Django's `truncatechars` filter: the result is at most `length` characters
 * long, ending in a single "…" when the value was shortened.
 */
export function truncateChars(value: string, length: number): string {
  return value.length > length ? `${value.slice(0, length - 1)}…` : value;
}
