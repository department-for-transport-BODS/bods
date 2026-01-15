/**
 * Publisher Dashboard Home
 * 
 * Main page for publishers (publish subdomain)
 */

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import Link from 'next/link';

function PublishDashboard() {
  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Publisher dashboard</h1>
            <p className="govuk-body-l">
              Manage your bus data publications.
            </p>
            <ul className="govuk-list">
              <li>
                <Link href="/publish/org" className="govuk-link">
                  Select organisation
                </Link>
              </li>
              <li>
                <Link href="/publish/agent-dashboard" className="govuk-link">
                  Agent dashboard
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function PublishPage() {
  return (
    <ProtectedRoute>
      <PublishDashboard />
    </ProtectedRoute>
  );
}

