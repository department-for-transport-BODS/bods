import type { ErrorSummaryItem } from '@/components/shared/ErrorSummary';


export function errorSummaryItems(
  errors: Record<string, string | undefined>,
  anchors: Record<string, string> = {},
): ErrorSummaryItem[] {
  return Object.entries(errors)
    .filter((entry): entry is [string, string] => Boolean(entry[1]))
    .map(([field, text]) => ({ text, href: anchors[field] }));
}
