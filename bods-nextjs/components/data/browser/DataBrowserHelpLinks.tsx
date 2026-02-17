import Link from 'next/link';

interface HelpLink {
  href: string;
  label: string;
}

interface DataBrowserHelpLinksProps {
  title?: string;
  links: HelpLink[];
}

export function DataBrowserHelpLinks({
  title = 'Need further help?',
  links,
}: DataBrowserHelpLinksProps) {
  return (
    <div className="govuk-grid-column-one-third">
      <h2 className="govuk-heading-m">{title}</h2>
      <ul className="govuk-list">
        {links.map((link) => (
          <li className="govuk-!-margin-bottom-3" key={`${link.href}-${link.label}`}>
            {link.href.startsWith('http') ? (
              <a className="govuk-link" href={link.href} target="_blank" rel="noopener noreferrer">
                {link.label}
              </a>
            ) : (
              <Link className="govuk-link" href={link.href}>
                {link.label}
              </Link>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

