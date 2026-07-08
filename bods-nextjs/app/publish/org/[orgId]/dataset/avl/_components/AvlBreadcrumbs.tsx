import Link from 'next/link';

export interface AvlBreadcrumbItem {
  label: string;
  href: string;
  isCurrent?: boolean;
  truncateLabel?: boolean;
}

interface AvlBreadcrumbsProps {
  items: AvlBreadcrumbItem[];
}

function truncateBreadcrumbLabel(label: string, maxLength = 20): string {
  if (label.length <= maxLength) {
    return label;
  }

  return `${label.slice(0, maxLength - 1)}...`;
}

export function AvlBreadcrumbs({ items }: AvlBreadcrumbsProps) {
  return (
    <nav className="govuk-breadcrumbs" aria-label="Breadcrumb">
      <ol className="govuk-breadcrumbs__list">
        <li className="govuk-breadcrumbs__list-item">
          <Link className="govuk-breadcrumbs__link" href="/">
            Bus Open Data Service
          </Link>
        </li>
        <li className="govuk-breadcrumbs__list-item">
          <Link className="govuk-breadcrumbs__link" href="/publish/">
            Publish Open Data Service
          </Link>
        </li>
        {items.map((item) => (
          <li
            key={`${item.href}-${item.label}`}
            className="govuk-breadcrumbs__list-item"
            aria-current={item.isCurrent ? 'page' : undefined}
          >
            <Link className="govuk-breadcrumbs__link" href={item.href}>
              {item.truncateLabel ? truncateBreadcrumbLabel(item.label) : item.label}
            </Link>
          </li>
        ))}
      </ol>
    </nav>
  );
}