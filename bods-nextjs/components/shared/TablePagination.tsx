/**
 * Pagination for the Django django-tables2 lists (transit_odp/templates/snippets/pagination.html).
 *
 * Same window, `⋯` gaps, Previous/Next markup and relative `?page=N&…` links as the Django
 * template, which is what the feed lists render under their tables. The shared `Pagination`
 * renders this when given `variant="table"`.
 */

'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { PaginationNextIcon, PaginationPrevIcon } from './PaginationIcons';
import { tablePageRange } from '@/lib/table-page-range';

interface TablePaginationProps {
  currentPage: number;
  totalPages: number;
  pageParam?: string;
}

export function TablePagination({
  currentPage,
  totalPages,
  pageParam = 'page',
}: TablePaginationProps) {
  const searchParams = useSearchParams();

  // Django's relative_url tag: the page first, then every other query parameter as it was.
  const pageHref = (page: number) => {
    const others = new URLSearchParams(searchParams.toString());
    others.delete(pageParam);
    const rest = others.toString();
    return rest ? `?${pageParam}=${page}&${rest}` : `?${pageParam}=${page}`;
  };

  return (
    <nav className="justify-center-l govuk-pagination" role="navigation" aria-label="Pagination">
      {currentPage > 1 && (
        <div className="govuk-pagination__prev">
          <Link className="govuk-link govuk-pagination__link" href={pageHref(currentPage - 1)} rel="prev">
            {PaginationPrevIcon}
            <span className="govuk-pagination__link-title">
              Previous<span className="govuk-visually-hidden">page</span>
            </span>
          </Link>
        </div>
      )}
      <ul className="govuk-pagination__list">
        {tablePageRange(currentPage, totalPages).map((item, index) =>
          item === '...' ? (
            <li
              key={`ellipsis-${index}`}
              className="govuk-pagination__item govuk-pagination__item--ellipses"
            >
              ⋯
            </li>
          ) : (
            <li
              key={item}
              className={`govuk-pagination__item${item === currentPage ? ' govuk-pagination__item--current' : ''}`}
            >
              {/* Django gives every link aria-label="Page 1"; kept for 1:1 parity. */}
              <Link
                className="govuk-link govuk-pagination__link"
                href={pageHref(item)}
                aria-label="Page 1"
              >
                {item}
              </Link>
            </li>
          ),
        )}
      </ul>
      {currentPage < totalPages && (
        <div className="govuk-pagination__next">
          <Link className="govuk-link govuk-pagination__link" href={pageHref(currentPage + 1)} rel="next">
            <span className="govuk-pagination__link-title">
              Next<span className="govuk-visually-hidden">page</span>
            </span>
            {PaginationNextIcon}
          </Link>
        </div>
      )}
    </nav>
  );
}
