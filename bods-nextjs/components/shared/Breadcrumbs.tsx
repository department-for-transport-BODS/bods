import Link from 'next/link';

export interface BreadcrumbItem {
  label: string;
  href?: string;
  current?: boolean;
  truncateAt?: number;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
}

function formatLabel(label: string, truncateAt?: number) {
  if (!truncateAt || label.length <= truncateAt) {
    return label;
  }

  return `${label.slice(0, truncateAt - 1)}...`;
}

function isExternalHref(href: string) {
  return href.startsWith('http://') || href.startsWith('https://');
}

export function Breadcrumbs({ items }: BreadcrumbsProps) {
  return (
    <nav className="govuk-breadcrumbs" aria-label="Breadcrumb">
      <ol className="govuk-breadcrumbs__list">
        {items.map((item) => {
          const label = formatLabel(item.label, item.truncateAt);

          return (
            <li
              key={`${item.href ?? 'current'}-${item.label}`}
              className="govuk-breadcrumbs__list-item"
              aria-current={item.current ? 'page' : undefined}
            >
              {item.href && isExternalHref(item.href) ? (
                <a className="govuk-breadcrumbs__link" href={item.href}>
                  {label}
                </a>
              ) : item.href ? (
                <Link className="govuk-breadcrumbs__link" href={item.href}>
                  {label}
                </Link>
              ) : (
                label
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}