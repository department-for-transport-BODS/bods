const NUMERIC_ID = /^\d+$/;

/**
 * Type guard verifying that a route/query param is a non-null string of digits,
 * e.g. an `orgId` or `datasetId` extracted from a URL.
 */
export function isNumericId(value: string | null): value is string {
  return Boolean(value && NUMERIC_ID.test(value));
}
