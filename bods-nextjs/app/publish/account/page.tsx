import Link from 'next/link';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

function ManageAccountPageContent() {
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
              Manage your account
            </li>
          </ol>
        </div>

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Manage your account</h1>
            <p className="govuk-body">
              Use this area to manage organisation-related details before publishing, including licence and account information.
            </p>
            <div className="govuk-inset-text">
              Account management pages have not been fully migrated yet. Continue via organisation selection for publishing tasks,
              or contact support if you need account changes made now.
            </div>
            <div className="govuk-button-group">
              <Link href="/publish/org" className="govuk-button">
                Select organisation
              </Link>
              <Link href="/contact" className="govuk-link">
                Contact support
              </Link>
            </div>
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

export default function ManageAccountPage() {
  return (
    <ProtectedRoute>
      <ManageAccountPageContent />
    </ProtectedRoute>
  );
}