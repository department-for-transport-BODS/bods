/**
 * Accessibility Page
 * 
 * Source: transit_odp/templates/pages/accessibility.html
 */

import Link from 'next/link';
import { config, HOSTS } from '@/config';

export default function AccessibilityPage() {
  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Accessibility statement</h1>
            
            <p className="govuk-body">
              This statement applies to pages on{' '}
              <a className="govuk-link" rel="noopener noreferrer" target="_blank" href={HOSTS.root}>
                {HOSTS.root}
              </a>.
            </p>
            
            <p className="govuk-body">
              This website is run by the Department for Transport. The text should be clear and simple to understand. You should be able to:
            </p>
            
            <ul className="govuk-list govuk-list--bullet">
              <li>zoom in up to 400% without the text spilling off the screen.</li>
              <li>navigate all of the website using just a keyboard (except for maps which are not essential to the functionality).</li>
              <li>use all of the website using a screen reader (including the most recent versions of NVDA).</li>
              <li>interpret page information through access technology due to a consistent heading structure.</li>
              <li>access the site and use the associated services with Google Chrome, Internet Explorer, Safari, Opera, Firefox, and Edge.</li>
            </ul>
            
            <br />
            
            <section>
              <p className="govuk-heading-m">How accessible this website is</p>
              <p className="govuk-body">
                Parts of this website are not fully accessible. These include the map function, which isn't readily accessible by the screen reader and the key board function will not pick it up directly.
              </p>
            </section>
            
            <section>
              <h2 className="govuk-heading-m">Feedback and contact information</h2>
              <p className="govuk-body">
                If you need information on this website in a different format like accessible PDF, large print, easy read, audio recording or braille:
              </p>
              <ul className="govuk-list govuk-list--bullet">
                <li>
                  Email: <a className="govuk-link" href="mailto:BusOpenData@dft.gov.uk">BusOpenData@dft.gov.uk</a>
                </li>
              </ul>
              <p className="govuk-body">
                We'll consider your request and get back to you in 3 working days.
              </p>
            </section>
            
            <section>
              <h2 className="govuk-heading-m">Reporting accessibility problems with this website</h2>
              <p className="govuk-body">
                We're always looking to improve the accessibility of this website. If you find any problems that are not listed on this page or you think we're not meeting the accessibility requirements, contact:{' '}
                <a className="govuk-link" href="mailto:BusOpenData@dft.gov.uk">BusOpenData@dft.gov.uk</a>
              </p>
            </section>
            
            <section>
              <h2 className="govuk-heading-m">Enforcement procedure</h2>
              <p className="govuk-body">
                The Equality and Human Rights Commission (EHRC) is responsible for enforcing the Public Sector Bodies (Websites and Mobile Applications) (No. 2) Accessibility Regulations 2018 (the 'accessibility regulations'). If you're not happy with how we respond to your complaint,{' '}
                <a className="govuk-link" rel="noopener noreferrer" target="_blank" href="https://www.equalityadvisoryservice.com/">
                  contact the Equality Advisory and Support Service (EASS).
                </a>
              </p>
            </section>
            
            <section>
              <h2 className="govuk-heading-m">Technical information about this website's accessibility</h2>
              <p className="govuk-body">
                Department for Transport is committed to making its websites accessible, in accordance with the Public Sector Bodies (Websites and Mobile Applications) (No. 2) Accessibility Regulations 2018.
              </p>
            </section>
            
            <br />
            
            <section>
              <p className="govuk-heading-m">Compliance status</p>
              <p className="govuk-body">
                This website follows the{' '}
                <a className="govuk-link" rel="noopener noreferrer" target="_blank" href="https://www.w3.org/TR/WCAG22/">
                  Web Content Accessibility Guidelines version 2.2
                </a>{' '}
                AA standard.
              </p>
            </section>
            
            <section>
              <h2 className="govuk-heading-m">Non-accessible content</h2>
              <p className="govuk-body govuk-!-font-weight-bold">
                The content listed below is non-accessible for the following reasons.
              </p>
              <p className="govuk-body">Non-compliance with accessibility regulations</p>
              <ul className="govuk-list govuk-list--bullet">
                <li>Maps functions cannot be directly read by a screen reader. Key information is in the text.</li>
                <li>Keyboard only users may not be able to zoom on our maps.</li>
                <li>Alternative versions can be provided in plain text, braille, BSL, large print or audio CD.</li>
              </ul>
            </section>
            
            <section>
              <h2 className="govuk-heading-m">Preparation of this accessibility statement</h2>
              <p className="govuk-body">
                This statement was prepared on 17 December 2019. It was last reviewed on 27 September 2024.
              </p>
              <p className="govuk-body">
                This website was last tested on 20 September 2024.
              </p>
            </section>
          </div>
          
          <div className="govuk-grid-column-one-third">
            <hr className="govuk-section-break govuk-section-break--l" />
            <h2 className="govuk-heading-m">Bus Open Data Service</h2>
            <div>
              <p className="govuk-body">
                <Link href="/contact" className="govuk-link">Contact us</Link>
              </p>
            </div>
            <hr className="govuk-section-break govuk-section-break--l" />
            <h2 className="govuk-heading-m">Follow us</h2>
            <div>
              <p className="govuk-body">
                <a href="https://twitter.com/busopendata" className="govuk-link" target="_blank" rel="noopener noreferrer">
                  Bus open data service Twitter
                </a>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
