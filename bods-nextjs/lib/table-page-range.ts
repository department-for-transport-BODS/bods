export type TablePageItem = number | '...';

/**
 * Port of Django's `paginator_range` filter (transit_odp/common/templatetags/paginator_range.py),
 * which the django-tables2 `snippets/pagination.html` uses to decide which page links to show.
 *
 * Up to `pageRange` items are returned (10 for lists of at most 11 pages, otherwise 8), always
 * including the first and last page, with `'...'` standing in for any gap.
 */
export function tablePageRange(currentPage: number, numPages: number): TablePageItem[] {
  const pageRange = numPages - 1 < 11 ? 10 : 8;

  const all = (start: number, end: number): number[] =>
    Array.from({ length: end - start }, (_, index) => start + index);

  if (numPages <= pageRange) {
    return all(1, numPages + 1);
  }

  let rangeStart = currentPage - Math.trunc(pageRange / 2);
  if (rangeStart < 1) {
    rangeStart = 1;
  }
  let rangeEnd = rangeStart + pageRange;
  if (rangeEnd > numPages) {
    rangeStart = numPages - pageRange + 1;
    rangeEnd = numPages + 1;
  }

  let items: TablePageItem[] = all(rangeStart, rangeEnd);
  if (!items.includes(1)) {
    items = [1, '...', ...items.slice(2)];
  }
  if (!items.includes(numPages)) {
    items = [...items.slice(0, -2), '...', numPages];
  }
  return items;
}
