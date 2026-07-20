import Link from 'next/link';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';

function ReviewMyDataPageContent() {
  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <Breadcrumbs
          items={[
            { label: 'Bus Open Data Service', href: '/data' },
            { label: 'Publish Bus Open Data', href: '/publish' },
            { label: 'Review my data', current: true },
          ]}
        />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Review my data</h1>
            <p className="govuk-body">
              Select an organisation to review existing data sets, drafts and publishing status.
            </p>
            <Link href="/publish/org" className="govuk-button">
              Select organisation
            </Link>
          </div>

          <div className="govuk-grid-column-one-third">
            <h2 className="govuk-heading-m">Need further help?</h2>
            <ul className="govuk-list app-list--nav govuk-!-font-size-19">
              <li>
                <Link className="govuk-link" href="/changelog">
                  Service changelog
                </Link>
              </li>
              <li>
                <Link className="govuk-link" href="/contact">
                  Contact us for technical issues
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ReviewMyDataPage() {
  return (
    <ProtectedRoute>
      <ReviewMyDataPageContent />
    </ProtectedRoute>
  );
}