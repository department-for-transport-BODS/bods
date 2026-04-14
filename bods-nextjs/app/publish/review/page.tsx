import Link from 'next/link';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

function ReviewMyDataPageContent() {
  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-breadcrumbs">
          <ol className="govuk-breadcrumbs__list">
            <li className="govuk-breadcrumbs__list-item">
              <Link className="govuk-breadcrumbs__link" href="/data">
                Bus Open Data Service
              </Link>
            </li>
            <li className="govuk-breadcrumbs__list-item">
              <Link className="govuk-breadcrumbs__link" href="/publish">
                Publish Open Data Service
              </Link>
            </li>
            <li className="govuk-breadcrumbs__list-item" aria-current="page">
              Review my data
            </li>
          </ol>
        </div>

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