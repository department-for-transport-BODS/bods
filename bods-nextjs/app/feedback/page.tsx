import type { Metadata } from 'next';
import Link from 'next/link';
import { wwwPath } from '@/config/client';
import { FeedbackForm } from './_components/FeedbackForm';

export const metadata: Metadata = {
  title: 'Feedback',
};

type FeedbackPageProps = {
  searchParams: Promise<{ url?: string | string[] }>;
};

export default async function FeedbackPage({ searchParams }: FeedbackPageProps) {
  const params = await searchParams;
  const pageUrl = typeof params.url === 'string' ? params.url : '';

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds govuk-!-padding-right-9">
            <FeedbackForm pageUrl={pageUrl} />
          </div>
          <aside className="govuk-grid-column-one-third">
            <h2 className="govuk-heading-m">Need help?</h2>
            <p className="govuk-body">
              Visit the <Link className="govuk-link" href={wwwPath('/contact')}>Contact us</Link> page.
            </p>
            <hr className="govuk-section-break govuk-section-break--l govuk-section-break--visible" />
            <a
              className="govuk-link"
              href="https://twitter.com/busopendata?ref_src=twsrc%5Etfw"
              target="_blank"
              rel="noreferrer"
            >
              Bus open data service Twitter
            </a>
          </aside>
        </div>
      </div>
    </div>
  );
}
