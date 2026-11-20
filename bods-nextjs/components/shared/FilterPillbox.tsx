import Image from 'next/image';
import Link from 'next/link';

export interface FilterPill {
  key: string;
  label: string;
  href: string;
}

interface FilterPillboxProps {
  /** Bold heading shown before the pills, e.g. Django's `pill_box_title`. */
  title?: string;
  /** Shown before the search-term pill, e.g. "Containing" or "Beginning". */
  searchLabel?: string;
  searchTerm?: string;
  clearSearchHref?: string;
  filters?: FilterPill[];
  removeSectionBreakTopMargin?: boolean;
}

function Pill({ label, href }: { label: string; href: string }) {
  return (
    <Link href={href}>
      <span className="pill-item">
        <Image
          className="pill-item__image"
          src="/assets/images/icon-cross.png"
          alt=""
          width={16}
          height={16}
          aria-hidden="true"
        />
        <span className="pill-item__label">{label}</span>
      </span>
    </Link>
  );
}

/** Port of Django's `search-pillbox` filter bar (browse/snippets/search_list.html, site_admin lists). */
export function FilterPillbox({
  title,
  searchLabel,
  searchTerm,
  clearSearchHref,
  filters = [],
  removeSectionBreakTopMargin = false,
}: FilterPillboxProps) {
  return (
    <>
      <div className="govuk-body-s govuk-grid-row search-pillbox" role="region" aria-label="Search filters">
        {title && (
          <p className="govuk-body govuk-!-margin-bottom-0 govuk-!-margin-right-3">
            <b>{title}</b>
          </p>
        )}
        {searchTerm && searchLabel && (
          <span className="govuk-label govuk-!-font-weight-bold govuk-!-padding-right-3">{searchLabel}</span>
        )}
        {searchTerm && clearSearchHref && <Pill label={searchTerm} href={clearSearchHref} />}
        {filters.map((filter) => (
          <Pill key={filter.key} label={filter.label} href={filter.href} />
        ))}
      </div>
      <hr
        className={`govuk-section-break govuk-section-break--s govuk-section-break--visible pillbox-break${
          removeSectionBreakTopMargin ? ' govuk-!-margin-top-0' : ''
        }`}
      />
    </>
  );
}
