/**
 * Admin Dashboard Home
 * 
 * Main page for site administrators (admin subdomain)
 * Note: Django admin remains at /admin/ on this subdomain
 */

import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import Link from 'next/link';

function AdminDashboard() {
  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Admin dashboard</h1>
            <p className="govuk-body-l">
              Manage users, organisations, and system settings.
            </p>
            <div className="govuk-warning-text">
              <span className="govuk-warning-text__icon" aria-hidden="true">!</span>
              <strong className="govuk-warning-text__text">
                <span className="govuk-warning-text__assistive">Warning</span>
                Django admin is available at{' '}
                <a href="/admin" className="govuk-link">
                  /admin
                </a>
              </strong>
            </div>
            <ul className="govuk-list">
              <li>
                <Link href="/admin/users" className="govuk-link">
                  User management
                </Link>
              </li>
              <li>
                <Link href="/admin/organisations" className="govuk-link">
                  Organisation management
                </Link>
              </li>
              <li>
                <Link href="/admin/metrics" className="govuk-link">
                  Metrics and analytics
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AdminPage() {
  return (
    <ProtectedRoute>
      <AdminDashboard />
    </ProtectedRoute>
  );
}

