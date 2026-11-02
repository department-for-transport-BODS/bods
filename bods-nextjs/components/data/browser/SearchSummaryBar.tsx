import Image from 'next/image';
import Link from 'next/link';

export interface SearchSummaryFilter {
  key: string;
  label: string;
  href: string;
}

interface SearchSummaryBarProps {
  filters?: SearchSummaryFilter[];
  searchTerm?: string;
  clearSearchHref?: string;
  showContaining?: boolean;
  removeSectionBreakTopMargin?: boolean;
}

function FilterPill({ label, href }: { label: string; href: string }) {
  return (
    <Link href={href}>
      <span className="app-data-browser__filter-pill">
        <Image
          className="app-data-browser__filter-pill-image"
          src="/assets/images/icon-cross.png"
          alt=""
          width={16}
          height={16}
          aria-hidden="true"
        />
        <span className="app-data-browser__filter-pill-label">{label}</span>
      </span>
    </Link>
  );
}

export function SearchSummaryBar({
  filters = [],
  searchTerm,
  clearSearchHref,
  showContaining = false,
  removeSectionBreakTopMargin = false,
}: SearchSummaryBarProps) {
  return (
    <>
      <div
        className="govuk-body-s govuk-grid-row app-data-browser__filter-pillbox"
        role="region"
        aria-label="Search filters"
      >
        {searchTerm && showContaining && (
          <span className="govuk-label govuk-!-font-weight-bold govuk-!-padding-right-3">Containing</span>
        )}
        {searchTerm && clearSearchHref && <FilterPill label={searchTerm} href={clearSearchHref} />}
        {filters.map((filter) => (
          <FilterPill key={filter.key} label={filter.label} href={filter.href} />
        ))}
      </div>
      <hr
        className={`govuk-section-break govuk-section-break--s govuk-section-break--visible pillbox-break${
          removeSectionBreakTopMargin
            ? ' govuk-!-margin-top-0 app-data-browser__section-break--no-top-margin'
            : ''
        }`}
      />
    </>
  );
}
