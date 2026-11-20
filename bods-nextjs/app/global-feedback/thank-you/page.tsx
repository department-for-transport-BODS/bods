import type { Metadata } from 'next';
import Link from 'next/link';
import { wwwPath } from '@/config/client';

export const metadata: Metadata = {
  title: 'Thank you',
};

export default function FeedbackThankYouPage() {
  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-l app-!-mb-4">Thank you for getting in touch</h1>
            <p className="govuk-body">Your feedback helps to improve our service.</p>
          </div>
          <div className="govuk-grid-column-one-third">
            <h2 className="govuk-heading-m">Need help?</h2>
            <p className="govuk-body">
              Visit the <Link className="govuk-link" href={wwwPath('/contact')}>Contact us</Link> page.
            </p>
            <hr className="govuk-section-break govuk-section-break--l govuk-section-break--visible" />
            <div>
              <a
                className="govuk-link"
                href="https://twitter.com/busopendata?ref_src=twsrc%5Etfw"
                target="_blank"
                rel="noreferrer"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src="/assets/images/feedback/twitter_icon.png"
                  alt="twitter icon"
                  height="auto"
                  width="auto"
                  style={{ width: '30px', height: '30px' }}
                />
                Bus open data service Twitter
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
