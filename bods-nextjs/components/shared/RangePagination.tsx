'use client';

import Link from 'next/link';

interface RangePaginationProps {
  currentPage: number;
  numPages: number;
  /** Django's `paginator_range` output: page numbers with "..." gaps. */
  pageRange: Array<number | string>;
  /** Builds the link for a page, keeping the other query parameters. */
  buildHref: (page: number) => string;
}

const ARROW_PREV =
  'm6.5938-0.0078125-6.7266 6.7266 6.7441 6.4062 1.377-1.449-4.1856-3.9768h12.896v-2h-12.984l4.2931-4.293-1.414-1.414z';
const ARROW_NEXT =
  'm8.107-0.0078125-1.4136 1.414 4.2926 4.293h-12.986v2h12.896l-4.1855 3.9766 1.377 1.4492 6.7441-6.4062-6.7246-6.7266z';

/**
 * Mirrors Django's `snippets/pagination.html` (used by the data-host list
 * views): previous link, `paginator_range` page items with ⋯ gaps, next link.
 * The shared `Pagination` component uses a different windowing rule, so it
 * cannot be used where 1:1 page numbers matter.
 */
export function RangePagination({ currentPage, numPages, pageRange, buildHref }: RangePaginationProps) {
  return (
    <nav className="justify-center-l govuk-pagination" role="navigation" aria-label="Pagination">
      {currentPage > 1 && (
        <div className="govuk-pagination__prev">
          <Link className="govuk-link govuk-pagination__link" href={buildHref(currentPage - 1)} rel="prev">
            <svg
              className="govuk-pagination__icon govuk-pagination__icon--prev"
              xmlns="http://www.w3.org/2000/svg"
              height="13"
              width="15"
              aria-hidden="true"
              focusable="false"
              viewBox="0 0 15 13"
            >
              <path d={ARROW_PREV} />
            </svg>
            <span className="govuk-pagination__link-title">
              Previous<span className="govuk-visually-hidden">page</span>
            </span>
          </Link>
        </div>
      )}
      <ul className="govuk-pagination__list">
        {pageRange.map((item, index) => {
          if (item === '...') {
            return (
              <li key={`gap-${index}`} className="govuk-pagination__item govuk-pagination__item--ellipses">
                ⋯
              </li>
            );
          }
          const page = Number(item);
          return (
            <li
              key={page}
              className={`govuk-pagination__item${page === currentPage ? ' govuk-pagination__item--current' : ''}`}
            >
              <Link className="govuk-link govuk-pagination__link" href={buildHref(page)} aria-label={`Page ${page}`}>
                {page}
              </Link>
            </li>
          );
        })}
      </ul>
      {currentPage < numPages && (
        <div className="govuk-pagination__next">
          <Link className="govuk-link govuk-pagination__link" href={buildHref(currentPage + 1)} rel="next">
            <span className="govuk-pagination__link-title">
              Next<span className="govuk-visually-hidden">page</span>
            </span>
            <svg
              className="govuk-pagination__icon govuk-pagination__icon--next"
              xmlns="http://www.w3.org/2000/svg"
              height="13"
              width="15"
              aria-hidden="true"
              focusable="false"
              viewBox="0 0 15 13"
            >
              <path d={ARROW_NEXT} />
            </svg>
          </Link>
        </div>
      )}
    </nav>
  );
}
