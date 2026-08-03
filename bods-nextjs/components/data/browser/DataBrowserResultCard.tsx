import Link from 'next/link';

interface KeyValue {
  key: string;
  value: string;
}

interface DataBrowserResultCardProps {
  title: string;
  href: string;
  status: string;
  statusLabel: string;
  keyValues: KeyValue[];
  description?: string;
}

function getStatusClass(status: string): string {
  if (status === 'published' || status === 'live') {
    return 'app-data-browser__status-dot--live';
  }
  if (status === 'inactive') {
    return 'app-data-browser__status-dot--inactive';
  }
  return 'app-data-browser__status-dot--error';
}

export function DataBrowserResultCard({
  title,
  href,
  status,
  statusLabel,
  keyValues,
  description,
}: DataBrowserResultCardProps) {
  return (
    <div>
      <div className="app-data-browser__result-heading">
        <Link className="govuk-link app-data-browser__title-link" href={href}>
          {title}
        </Link>
        <span className="app-data-browser__status-text">
          <span className={`app-data-browser__status-dot ${getStatusClass(status)}`} />
          {statusLabel}
        </span>
      </div>
      <ul className="app-data-browser__key-value-list">
        {keyValues.map((item) => (
          <li className="app-data-browser__key-value-item" key={`${item.key}-${item.value}`}>
            <span className="app-data-browser__item-key">{item.key}</span>
            <span className="app-data-browser__item-value">{item.value}</span>
          </li>
        ))}
      </ul>
      {description && <p className="govuk-body">{description}</p>}
    </div>
  );
}

