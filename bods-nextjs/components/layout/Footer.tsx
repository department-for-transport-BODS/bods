/**
 * Footer Component
 *
 * same as transit_odp/templates/footer.html for layout parity.
 */

'use client';

import { GovUkCrownIcon } from './icons/GovUkCrownIcon';
import { OpenGovernmentLicenceLogo } from './icons/OpenGovernmentLicenceLogo';

const footerLinks = [
  { href: '/cookie', text: 'Cookies' },
  { href: '/contact', text: 'Contact' },
  { href: '/accessibility', text: 'Accessibility' },
  { href: '/privacy-policy', text: 'Privacy' },
];

export function Footer() {
  return (
    <footer className="govuk-footer" role="contentinfo">
      <div className="govuk-width-container">
        <GovUkCrownIcon />

        <div className="govuk-footer__meta">
          <div className="govuk-footer__meta-item govuk-footer__meta-item--grow">
            <h2 className="govuk-visually-hidden">Support links</h2>
            <ul className="govuk-footer__inline-list">
              {footerLinks.map((link) => (
                <li key={link.href} className="govuk-footer__inline-list-item">
                  <a className="govuk-footer__link" href={link.href}>
                    {link.text}
                  </a>
                </li>
              ))}
            </ul>

            <p className="govuk-footer__body">
              Built by the{' '}
              <a
                className="govuk-footer__link"
                href="https://www.gov.uk/government/organisations/department-for-transport"
                target="_blank"
                rel="noreferrer"
              >
                Department for Transport
              </a>
            </p>

            <OpenGovernmentLicenceLogo />

            <span className="govuk-footer__licence-description">
              All content is available under the{' '}
              <a
                className="govuk-footer__link"
                href="https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/"
                rel="license"
                target="_blank"
              >
                Open Government Licence v3.0
              </a>
              {', except where otherwise stated'}
            </span>
          </div>

          <div className="govuk-footer__meta-item">
            <a
              className="govuk-footer__link govuk-footer__copyright-logo"
              href="https://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/uk-government-licensing-framework/crown-copyright/"
              target="_blank"
              rel="noreferrer"
            >
              © Crown copyright
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}

